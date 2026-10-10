from enum import Enum


class GameStatus(Enum):
    CHECK = "check"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    PLAYING = "playing"
    DRAW = "draw"