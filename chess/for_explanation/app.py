from __future__ import annotations
import os        # узнать число ядер процессора
import secrets   # криптографически стойкие случайные токены и безопасное сравнение строк
import uuid
from pathlib import Path
from threading import Lock

import uvicorn
from fastapi import FastAPI, Header, HTTPException   # Header — чтение заголовка запроса
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from game import Game
from tools.clock import Clock                         # НОВОЕ: шахматные часы
from tools.position import Position

from bots.base import Bot
from bots.greedy import GreedyBot
from bots.minimax import MinimaxBot
from tools.color import Color
from web.serializers import GAME_OVER, serialize

# клик -> app.js -> HTTP-запрос -> uvicorn -> FastAPI -> функция в app.py
#      -> Game (правила) -> serialize() -> JSON -> uvicorn -> app.js -> render()


# «Продвинутый» бот теперь создаётся сразу на всех ядрах. Это lambda, потому что новый бот
# создаётся для каждой партии. os.cpu_count() может вернуть None, тогда берём 1 процесс.
BOTS = {"greedy": GreedyBot, "advanced": lambda: MinimaxBot(depth=4, workers=os.cpu_count() or 1)}
TIME_CONTROLS = (5, 10)  # блиц: допустимые контроли времени, минут на партию каждому игроку

# Всё про партию лежит в словарях; ключ везде — id партии
games: dict[str, Game] = {}
opponents: dict[str, str] = {}  # id партии -> "human" / "greedy" / "advanced"
bots: dict[str, Bot] = {}  # бот играет чёрными
clocks: dict[str, Clock] = {}  # НОВОЕ: часы партии
players: dict[str, dict[Color, str]] = {}  # НОВОЕ: токены игроков, т.е. кто может ходить за какой цвет
invites: dict[str, str] = {}  # НОВОЕ: токен чёрных, пока второй игрок не присоединился
locks: dict[str, Lock] = {}  # НОВОЕ: у каждой партии своя блокировка. Пока бот думает в одной партии,
                             # остальные работают (раньше блокировка была одна на всё приложение)


STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Chess")


class NewGameIn(BaseModel):
    opponent: str = "human"
    minutes: int = 5          # НОВОЕ: контроль времени; значения по умолчанию сохраняют работу старых запросов


class NoCacheStatic(StaticFiles):
    """Браузер проверяет файл у сервера при каждой загрузке (если не менялся, ответ 304)"""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


app.mount("/static", NoCacheStatic(directory=STATIC), name="static")


def flagged(game_id: str) -> Color | None:
    """Цвет того, у кого упал флажок, или None. clocks.get вместо [] — чтобы не падать, если часов нет"""
    clock = clocks.get(game_id)
    return clock.flagged() if clock else None


def is_over(game_id: str, game: Game) -> bool:
    """Партия окончена: по правилам (мат, пат, ничья) ИЛИ по времени"""
    return game.status() in GAME_OVER or flagged(game_id) is not None


def state_of(game_id: str, game: Game) -> dict:
    # обычное состояние партии + кто соперник + ждём ли мы второго игрока (его токен ещё в invites)
    state = {**serialize(game), "opponent": opponents.get(game_id, "human"),
             "waiting_for_opponent": game_id in invites}
    clock = clocks.get(game_id)
    if clock is not None:
        loser = clock.flagged()
        if loser is not None:
            # время вышло: поверх обычного статуса записываем конец партии и победителя (противоположный цвет).
            # Правила шахмат (Game) про время ничего не знают, поэтому подмена делается здесь, в веб-слое.
            state.update(status="timeout", game_over=True,
                         winner=loser.opposite.value, draw_reason=None)
        # остаток времени обоих (округлён до 0.1 с) и цвет того, чьи часы идут
        state["clock"] = {
            "white": round(clock.remaining(Color.WHITE), 1),
            "black": round(clock.remaining(Color.BLACK), 1),
            "running": clock.running.value if clock.running else None,
        }
    return state


def advance_clock(game_id: str, game: Game) -> None:
    """Вызывается после каждого УСПЕШНОГО хода"""
    clock = clocks[game_id]
    if game.status() in GAME_OVER:
        clock.stop()              # партия окончена: часы замораживаются
    elif clock.running is None:
        clock.start(game.turn)    # это был первый ход белых: запускаем часы чёрных (чья очередь)
    else:
        clock.switch()            # иначе передаём время сопернику


def player_color(game_id: str, token: str | None) -> Color:
    """Кто делает запрос: определяем по токену. Без верного токена ходить нельзя"""
    if not token:
        raise HTTPException(401, "Нужен токен игрока")
    for color, own in players[game_id].items():
        # compare_digest сравнивает за время, не зависящее от того, на каком символе строки различаются
        # (иначе токен можно подбирать по времени ответа). Принимает байты, поэтому кодируем.
        if secrets.compare_digest(own.encode(), token.encode()):
            return color
    raise HTTPException(401, "Неверный токен игрока")


class MoveIn(BaseModel):
    source: str
    destination: str
    promotion: str | None = None  # 'q', 'r', 'b', 'n'


def get_game(game_id: str) -> Game:
    game = games.get(game_id)
    if game is None:
        raise HTTPException(404, "Партия не найдена")
    return game


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.post("/api/games")
def create_game(body: NewGameIn | None = None):
    body = body or NewGameIn()              # тела нет — берём значения по умолчанию
    opponent = body.opponent
    if opponent != "human" and opponent not in BOTS:
        raise HTTPException(400, "Неизвестный соперник")
    if body.minutes not in TIME_CONTROLS:
        raise HTTPException(400, "Контроль времени: 5 или 10 минут")
    game_id = uuid.uuid4().hex              # неугадываемый id партии
    token = secrets.token_urlsafe(16)       # токен белых: 16 случайных байт = 128 бит, безопасная для URL кодировка
    locks[game_id] = Lock()                 # блокировка именно этой партии
    clocks[game_id] = Clock(body.minutes * 60)   # минуты -> секунды
    players[game_id] = {Color.WHITE: token}      # создатель всегда играет белыми
    opponents[game_id] = opponent
    if opponent == "human":
        invites[game_id] = secrets.token_urlsafe(16)  # токен чёрных ждёт, пока кто-то откроет ссылку
    else:
        bots[game_id] = BOTS[opponent]()
    games[game_id] = Game()  # ПОСЛЕДНИМ: пока партии нет в games, другие запросы получают 404,
                             # так что никто не застанет её наполовину созданной (например, без блокировки)
    return {"id": game_id, "token": token, "color": "white", **state_of(game_id, games[game_id])}


@app.post("/api/games/{game_id}/join")
def join_game(game_id: str):
    """Второй игрок (чёрные) открывает ссылку и получает свой токен. Токен выдаётся один раз"""
    game = get_game(game_id)
    with locks[game_id]:
        # pop достаёт и УДАЛЯЕТ токен за одну операцию под блокировкой партии:
        # даже при двух одновременных запросах токен получит ровно один
        token = invites.pop(game_id, None)
        if token is None:                   # партия с ботом или место уже занято
            raise HTTPException(409, "Место соперника уже занято")
        players[game_id][Color.BLACK] = token
        return {"token": token, "color": "black", **state_of(game_id, game)}


@app.get("/api/games/{game_id}")
def get_state(game_id: str):
    game = get_game(game_id)
    # читаем под блокировкой партии: status() проверяет легальные ходы и временно двигает фигуры,
    # читать доску в этот момент из другого потока нельзя
    with locks[game_id]:
        return state_of(game_id, game)


@app.get("/api/games/{game_id}/moves")
def get_moves(game_id: str, square: str):
    """Легальные ходы фигуры с клетки square, чтобы подсветить их на доске"""
    game = get_game(game_id)
    try:
        source = Position.from_str(square)
    except ValueError as e:
        raise HTTPException(400, str(e))
    with locks[game_id]:
        piece = game.board.get(source)
        if piece is None or piece.color is not game.turn:
            return {"moves": [], "promotions": []}
        destinations = game.legal_moves(source)
        return {
            "moves": sorted(str(d) for d in destinations),
            "promotions": sorted(str(d) for d in destinations if game.is_promotion(source, d)),
        }


@app.post("/api/games/{game_id}/move")
def make_move(game_id: str, body: MoveIn, x_player_token: str | None = Header(None)):
    # x_player_token: FastAPI превращает имя параметра в заголовок X-Player-Token; нет заголовка — None
    game = get_game(game_id)                         # 404, если партии нет
    color = player_color(game_id, x_player_token)    # 401, если токена нет или он неверный
    promotion = None
    if body.promotion:
        promotion = Game.PROMOTION_PIECES.get(body.promotion.lower())
        if promotion is None:
            raise HTTPException(400, "Неизвестная фигура для превращения")
    try:
        with locks[game_id]:
            if is_over(game_id, game):               # партия окончена, в том числе по времени
                raise HTTPException(400, "Партия окончена")
            if color is not game.turn:               # ход не твоего цвета
                raise HTTPException(403, "Сейчас ход соперника")
            # сам ход: правила проверяет Game, при ошибке бросает ValueError (ниже превращается в 400)
            game.make_move(Position.from_str(body.source),
                           Position.from_str(body.destination), promotion)
            advance_clock(game_id, game)             # переключаем часы только после УСПЕШНОГО хода
            return state_of(game_id, game)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/games/{game_id}/bot-move")
def bot_move(game_id: str):
    # токен не нужен: эндпоинт лишь просит сделать ход бота, и то только если сейчас очередь бота
    game = get_game(game_id)
    bot = bots.get(game_id)
    if bot is None:
        raise HTTPException(400, "В этой партии нет бота")
    try:
        # блокировка держится всё время раздумий бота, но она относится ТОЛЬКО к этой партии
        with locks[game_id]:
            if not is_over(game_id, game) and game.turn is Color.BLACK:
                move = bot.choose_move(game)
                if flagged(game_id) is None:   # пока бот думал, его время могло закончиться: тогда ход не делаем
                    game.make_move(*move)
                    advance_clock(game_id, game)
            return state_of(game_id, game)  # не очередь бота или партия кончилась: просто состояние
    except ValueError as e:
        raise HTTPException(400, str(e))


if __name__ == "__main__":
    # запуск из папки chess: python -m web.app
    # проверка __name__ нужна ради Windows: процессы-рабочие импортируют модуль заново
    # и без неё каждый из них пытался бы поднять сервер
    uvicorn.run(app, host="127.0.0.1", port=8000)
