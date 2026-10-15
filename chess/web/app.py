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
from web.serializers import serialize


# клик -> app.js -> HTTP-запрос -> uvicorn -> FastAPI -> функция в app.py
#      -> Game (правила) -> serialize() -> JSON -> uvicorn -> app.js -> render()

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Chess")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

games: dict[str, Game] = {}   # партии живут в памяти, после перезапуска пропадают
lock = Lock()                 # Game не рассчитан на параллельные запросы


class MoveIn(BaseModel):
    source: str
    destination: str
    promotion: str | None = None   # 'q', 'r', 'b', 'n'


def get_game(game_id: str) -> Game:
    game = games.get(game_id)
    if game is None:
        raise HTTPException(404, "Партия не найдена")
    return game


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.post("/api/games")
def create_game():
    game_id = uuid.uuid4().hex
    with lock:
        games[game_id] = Game()
        return {"id": game_id, **serialize(games[game_id])}


@app.get("/api/games/{game_id}")
def get_state(game_id: str):
    game = get_game(game_id)
    with lock:
        return serialize(game)


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
            return serialize(game)
    except ValueError as e:               # все ошибки правил это ValueError
        raise HTTPException(400, str(e))