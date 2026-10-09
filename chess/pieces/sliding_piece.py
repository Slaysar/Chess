from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING
from .piece import Piece

if TYPE_CHECKING:
    from tools.board import Board
    from tools.position import Position


class SlidingPiece(Piece):

    ROOK_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
    BISHOP_DIRS = ((1, 1), (-1, 1), (1, -1), (-1, -1))

    @property
    @abstractmethod
    def directions(self) -> list[tuple[int, int]]:
        ...

    def get_possible_moves(self, board: Board, position: Position) -> set[Position]:
        moves = set()
        for d_row, d_col in self.directions:
            cur = position.offset(d_row, d_col)
            while cur is not None:
                target = board.get(cur)
                if target is None:
                    moves.add(cur)
                else:
                    if target.color is not self.color:
                        moves.add(cur)  # взятие
                    break  # дальше фигура не проходит
                cur = cur.offset(d_row, d_col)
        return moves
