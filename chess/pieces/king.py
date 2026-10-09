from __future__ import annotations
from typing import TYPE_CHECKING
from .piece import Piece

if TYPE_CHECKING:
    from tools.board import Board
    from tools.position import Position


class King(Piece):

    SYMBOL = "K"
    DIR = [(1, 1), (1, 0), (1, -1), (0, -1),
           (-1, -1), (-1, 0), (-1, 1), (0, 1)]

    def get_possible_moves(self, board: Board, position: Position) -> set[Position]: # псевдоходы без проверки на шах
        moves = set()
        for d_row, d_col in self.DIR:
            target_pos = position.offset(d_row, d_col)
            if target_pos is None:
                continue
            target = board.get(target_pos)
            if target is None or target.color is not self.color:
                moves.add(target_pos)
        return moves

