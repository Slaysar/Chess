from __future__ import annotations
import os
import secrets
import uuid
from pathlib import Path
from threading import Lock
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from game import Game
from tools.clock import Clock
from tools.position import Position

from bots.base import Bot
from bots.greedy import GreedyBot
from bots.minimax import MinimaxBot
from tools.color import Color
from web.serializers import GAME_OVER, serialize

# клик -> app.js -> HTTP-запрос -> uvicorn -> FastAPI -> функция в app.py
#      -> Game (правила) -> serialize() -> JSON -> uvicorn -> app.js -> render()


BOTS = {"greedy": GreedyBot, "advanced": lambda: MinimaxBot(depth=5, workers=os.cpu_count() or 1)}
TIME_CONTROLS = (5, 10)  # блиц: минут на партию каждому игроку

# Всё про партию лежит в словарях по id партии
games: dict[str, Game] = {}
opponents: dict[str, str] = {}  # id партии -> "human" / "greedy" / "advanced"
bots: dict[str, Bot] = {}  # бот играет чёрными
clocks: dict[str, Clock] = {}
players: dict[str, dict[Color, str]] = {}  # токены игроков: кто может ходить за какой цвет
invites: dict[str, str] = {}  # токен чёрных, пока второй игрок не присоединился
locks: dict[str, Lock] = {}  # у каждой партии своя блокировка: пока бот думает в одной, другие работают


STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Chess")


class NewGameIn(BaseModel):
    opponent: str = "human"
    minutes: int = 5


class NoCacheStatic(StaticFiles):
    """Браузер проверяет файл у сервера при каждой загрузке (если не менялся, ответ 304)"""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


app.mount("/static", NoCacheStatic(directory=STATIC), name="static")


def flagged(game_id: str) -> Color | None:
    clock = clocks.get(game_id)
    return clock.flagged() if clock else None


def is_over(game_id: str, game: Game) -> bool:
    return game.status() in GAME_OVER or flagged(game_id) is not None


def state_of(game_id: str, game: Game) -> dict:
    state: dict[str, Any] = {**serialize(game), "opponent": opponents.get(game_id, "human"),
             "waiting_for_opponent": game_id in invites}
    clock = clocks.get(game_id)
    if clock is not None:
        loser = clock.flagged()
        if loser is not None:
            state.update(status="timeout", game_over=True, winner=loser.opposite.value, draw_reason=None)
        state["clock"] = {
            "white": round(clock.remaining(Color.WHITE), 1),
            "black": round(clock.remaining(Color.BLACK), 1),
            "running": clock.running.value if clock.running else None,
        }
    return state


def advance_clock(game_id: str, game: Game) -> None:
    """Вызывается после каждого сделанного хода"""
    clock = clocks[game_id]
    if game.status() in GAME_OVER:
        clock.stop()
    elif clock.running is None:
        clock.start(game.turn)  # первый ход белых сделан: пошло время чёрных
    else:
        clock.switch()


def player_color(game_id: str, token: str | None) -> Color:
    """Кто делает запрос: определяем по токену. Без верного токена ходить нельзя"""
    if not token:
        raise HTTPException(401, "Нужен токен игрока")
    for color, own in players[game_id].items():
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
    body = body or NewGameIn()
    opponent = body.opponent
    if opponent != "human" and opponent not in BOTS:
        raise HTTPException(400, "Неизвестный соперник")
    if body.minutes not in TIME_CONTROLS:
        raise HTTPException(400, "Контроль времени: 5 или 10 минут")
    game_id = uuid.uuid4().hex
    token = secrets.token_urlsafe(16)
    locks[game_id] = Lock()
    clocks[game_id] = Clock(body.minutes * 60)
    players[game_id] = {Color.WHITE: token}
    opponents[game_id] = opponent
    if opponent == "human":
        invites[game_id] = secrets.token_urlsafe(16)  # получит тот, кто откроет ссылку
    else:
        bots[game_id] = BOTS[opponent]()
    games[game_id] = Game()  # последним: партия появляется, когда всё остальное уже готово
    return {"id": game_id, "token": token, "color": "white", **state_of(game_id, games[game_id])}


@app.post("/api/games/{game_id}/join")
def join_game(game_id: str):
    """Второй игрок (чёрные) открывает ссылку и получает свой токен. Токен выдаётся один раз"""
    game = get_game(game_id)
    with locks[game_id]:
        token = invites.pop(game_id, None)
        if token is None:
            raise HTTPException(409, "Место соперника уже занято")
        players[game_id][Color.BLACK] = token
        return {"token": token, "color": "black", **state_of(game_id, game)}


@app.get("/api/games/{game_id}")
def get_state(game_id: str):
    game = get_game(game_id)
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
    game = get_game(game_id)
    color = player_color(game_id, x_player_token)
    promotion = None
    if body.promotion:
        promotion = Game.PROMOTION_PIECES.get(body.promotion.lower())
        if promotion is None:
            raise HTTPException(400, "Неизвестная фигура для превращения")
    try:
        with locks[game_id]:
            if is_over(game_id, game):
                raise HTTPException(400, "Партия окончена")
            if color is not game.turn:
                raise HTTPException(403, "Сейчас ход соперника")
            game.make_move(Position.from_str(body.source),
                           Position.from_str(body.destination), promotion)
            advance_clock(game_id, game)
            return state_of(game_id, game)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/games/{game_id}/bot-move")
def bot_move(game_id: str):
    game = get_game(game_id)
    bot = bots.get(game_id)
    if bot is None:
        raise HTTPException(400, "В этой партии нет бота")
    try:
        with locks[game_id]:
            if not is_over(game_id, game) and game.turn is Color.BLACK:
                move = bot.choose_move(game)
                if flagged(game_id) is None:  # пока бот думал, его время могло выйти
                    game.make_move(*move)
                    advance_clock(game_id, game)
            return state_of(game_id, game)  # не очередь бота или партия кончилась: просто состояние
    except ValueError as e:
        raise HTTPException(400, str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)