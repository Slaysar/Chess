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
        self.moves_made = 0  # сколько ходов бот уже сделал в партии

    @abstractmethod
    def choose_move(self, game: Game) -> tuple[Position, Position, type[Piece] | None]:
        ...

    def pick_best(self, scored, board):
        if not scored:
            raise ValueError("Нет легальных ходов")

        best = max(score for score, _ in scored)

        best_moves = [
            move for score, move in scored
            if score == best
        ]

        self.moves_made += 1

        if self.moves_made <= 3:
            best_center = max(self._centrality(move) for move in best_moves)
            best_moves = [
                move for move in best_moves
                if self._centrality(move) >= best_center - 2.5
            ]

        return self.rng.choice(best_moves)

    @staticmethod
    def _center_dist_sq(pos: Position) -> float:
        return (pos.row - 3.5) ** 2 + (pos.col - 3.5) ** 2

    @classmethod
    def _centrality(cls, move) -> float:
        source, destination = move
        source_dist = cls._center_dist_sq(source)
        dest_dist = cls._center_dist_sq(destination)

        progress = source_dist - dest_dist
        return -dest_dist + 0.1 * progress

    @staticmethod
    def finish_move(game: Game, source: Position, destination: Position):
        promotion = Queen if game.is_promotion(source, destination) else None
        return source, destination, promotion