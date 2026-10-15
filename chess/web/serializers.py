from __future__ import annotations
from game import Game
from tools.game_status import GameStatus
from tools.position import Position

GAME_OVER = {GameStatus.CHECKMATE, GameStatus.STALEMATE, GameStatus.DRAW}


def serialize(game: Game) -> dict:
    status = game.status()
    pieces = []
    for row in range(Position.SIZE):
        for col in range(Position.SIZE):
            pos = Position(row, col)
            piece = game.board.get(pos)
            if piece is not None:
                pieces.append({"square": str(pos), "type": piece.SYMBOL, "color": piece.color.value})

    check_square = None
    if status in (GameStatus.CHECK, GameStatus.CHECKMATE):
        king = game.board.find_king(game.turn)
        check_square = str(king) if king else None

    last = game.history[-1] if game.history else None
    return {
        "pieces": pieces,
        "turn": game.turn.value,
        "status": status.value,
        "game_over": status in GAME_OVER,
        "winner": game.turn.opposite.value if status is GameStatus.CHECKMATE else None,
        "draw_reason": game.draw_reason() if status is GameStatus.DRAW else None,
        "check_square": check_square,
        "last_move": {"source": str(last.source), "destination": str(last.destination)} if last else None,
        "history": [record.notation for record in game.history],
    }