from __future__ import annotations
from typing import TYPE_CHECKING
from .piece import Piece
from tools.color import Color

if TYPE_CHECKING:
    from tools.board import Board
    from tools.position import Position


class Pawn(Piece):
    SYMBOL = "P"

    @property
    def promotion_row(self) -> int:
        return 7 if self.color is Color.WHITE else 0

    def get_possible_moves(self, board: Board, position: Position) -> set[Position]:
        moves = set()
        step = 1 if self.color is Color.WHITE else -1
        start_row = 1 if self.color is Color.WHITE else 6

        forward = position.offset(step, 0)
        if forward is not None and board.get(forward) is None:
            moves.add(forward)
            if position.row == start_row:
                double = position.offset(2 * step, 0)
                if double is not None and board.get(double) is None:
                    moves.add(double)

        for d_col in (-1, 1):
            diag = position.offset(step, d_col)
            if diag is None:
                continue
            target = board.get(diag)
            if target is not None and target.color is not self.color:
                moves.add(diag)
            elif target is None and diag == board.en_passant_target: # для взятия на проходе
                pos = position.offset(0, d_col)
                if pos is not None:
                    victim = board.get(pos)  # клетка слева/справа от пешки
                    if isinstance(victim, Pawn) and victim.color is not self.color:
                        moves.add(diag)  # взятие на проходе

        return moves
