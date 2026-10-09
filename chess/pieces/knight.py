from __future__ import annotations
from typing import TYPE_CHECKING
from .piece import Piece

if TYPE_CHECKING:
    from tools.board import Board
    from tools.position import Position


class Knight(Piece):

    SYMBOL = "N"
    JUMPS = [(2, 1), (2, -1), (-2, 1), (-2, -1),
             (1, 2), (1, -2), (-1, 2), (-1, -2)]

    def get_possible_moves(self, board: Board, position: Position) -> set[Position]:
        moves = set()
        for d_row, d_col in self.JUMPS:
            target_pos = position.offset(d_row, d_col)
            if target_pos is None:
                continue
            target = board.get(target_pos)
            if target is None or target.color is not self.color:
                moves.add(target_pos)
        return moves

