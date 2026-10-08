from __future__ import annotations
from typing import TYPE_CHECKING
from .piece import Piece

if TYPE_CHECKING:
    from tools.board import Board
    from tools.position import Position


class Rook(Piece):
    DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # (d_row, d_col)

    def get_possible_moves(self, board: Board, position: Position) -> set[Position]:
        moves = set()
        for d_row, d_col in self.DIRECTIONS:
            cur = position.offset(d_row, d_col)
            while cur is not None:
                target = board.get(cur)
                if target is None:
                    moves.add(cur)
                else:
                    if target.color is not self.color:
                        moves.add(cur)  # взятие
                    break               # дальше фигура не проходит
                cur = cur.offset(d_row, d_col)
        return moves

    def __repr__(self) -> str:
        return "Rook"