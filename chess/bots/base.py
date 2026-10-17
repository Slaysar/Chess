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

    def pick_best(self, scored, board):
        if not scored:
            raise ValueError("Нет легальных ходов")

        best = max(score for score, _ in scored)

        best_moves = [
            move for score, move in scored
            if score == best
        ]

        best_center = max(
            self._centrality(move, board)
            for move in best_moves
        )

        center_moves = [
            move for move in best_moves
            if self._centrality(move, board) == best_center
        ]

        return self.rng.choice(center_moves)

    @staticmethod
    def finish_move(game: Game, source: Position, destination: Position):
        promotion = Queen if game.is_promotion(source, destination) else None
        return source, destination, promotion

    @staticmethod
    def _centrality(move, board):
        source, destination = move

        piece = board.get(source)
        if piece is None:
            return 0

        row, col = destination.row, destination.col

        distance = abs(row - 3.5) + abs(col - 3.5)
        center_score = 7 - distance

        weights = {
            "N": 2.5,
            "B": 1.5,
            "Q": 1.0,
            "R": 0.5,
            "P": 0.3,
            "K": 0.0,
        }

        weight = weights.get(piece.SYMBOL.upper(), 0.0)

        return center_score * weight
