from __future__ import annotations
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pieces.queen import Queen

if TYPE_CHECKING:
    from game import Game
    from pieces.piece import Piece
    from tools.position import Position


class Bot(ABC):
    name = "bot"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    @abstractmethod
    def choose_move(self, game: Game) -> tuple[Position, Position, type[Piece] | None]:
        ...

    def pick_best(self, scored):
        if not scored:
            raise ValueError("Нет легальных ходов")
        best = max(score for score, _ in scored)
        return self.rng.choice([move for score, move in scored if score == best])

    @staticmethod
    def finish_move(game: Game, source: Position, destination: Position):
        promotion = Queen if game.is_promotion(source, destination) else None
        return source, destination, promotion