from __future__ import annotations
import uuid
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from game import Game
from tools.position import Position

from bots.base import Bot
from bots.greedy import GreedyBot
from bots.minimax import MinimaxBot
from tools.color import Color
from web.serializers import GAME_OVER, serialize

# клик -> app.js -> HTTP-запрос -> uvicorn -> FastAPI -> функция в app.py
#      -> Game (правила) -> serialize() -> JSON -> uvicorn -> app.js -> render()


BOTS = {"greedy": GreedyBot, "advanced": lambda: MinimaxBot(depth=5)}

games: dict[str, Game] = {}
opponents: dict[str, str] = {}  # id партии -> "human" / "greedy" / "advanced"
bots: dict[str, Bot] = {}  # бот играет чёрными


STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Chess")

lock = Lock()  # Game не рассчитан на параллельные запросы


class NewGameIn(BaseModel):
    opponent: str = "human"


class NoCacheStatic(StaticFiles):
    """Браузер проверяет файл у сервера при каждой загрузке (если не менялся, ответ 304)"""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


app.mount("/static", NoCacheStatic(directory=STATIC), name="static")


def state_of(game_id: str, game: Game) -> dict:
    return {**serialize(game), "opponent": opponents.get(game_id, "human")}


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
    opponent = body.opponent if body else "human"
    if opponent != "human" and opponent not in BOTS:
        raise HTTPException(400, "Неизвестный соперник")
    game_id = uuid.uuid4().hex
    with lock:
        games[game_id] = Game()
        opponents[game_id] = opponent
        if opponent != "human":
            bots[game_id] = BOTS[opponent]()
        return {"id": game_id, **state_of(game_id, games[game_id])}


@app.get("/api/games/{game_id}")
def get_state(game_id: str):
    game = get_game(game_id)
    with lock:
        return state_of(game_id, game)


@app.get("/api/games/{game_id}/moves")
def get_moves(game_id: str, square: str):
    """Легальные ходы фигуры с клетки square, чтобы подсветить их на доске"""
    game = get_game(game_id)
    try:
        source = Position.from_str(square)
    except ValueError as e:
        raise HTTPException(400, str(e))
    with lock:
        piece = game.board.get(source)
        if piece is None or piece.color is not game.turn:
            return {"moves": [], "promotions": []}
        destinations = game.legal_moves(source)
        return {
            "moves": sorted(str(d) for d in destinations),
            "promotions": sorted(str(d) for d in destinations if game.is_promotion(source, d)),
        }


@app.post("/api/games/{game_id}/move")
def make_move(game_id: str, body: MoveIn):
    game = get_game(game_id)
    promotion = None
    if body.promotion:
        promotion = Game.PROMOTION_PIECES.get(body.promotion.lower())
        if promotion is None:
            raise HTTPException(400, "Неизвестная фигура для превращения")
    try:
        with lock:
            game.make_move(Position.from_str(body.source),
                           Position.from_str(body.destination), promotion)
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
        with lock:
            if game.status() not in GAME_OVER and game.turn is Color.BLACK:
                game.make_move(*bot.choose_move(game))
            return state_of(game_id, game)  # не очередь бота или партия кончилась: просто состояние
    except ValueError as e:
        raise HTTPException(400, str(e))
