from __future__ import annotations
from typing import TYPE_CHECKING
from .piece import Piece

if TYPE_CHECKING:
    from tools.board import Board
    from tools.position import Position

class Pawn(Piece):

    def get_possible_moves(self, board : Board, position : Position) -> set[Position]:
        moves = set()

        #TODO

        return moves

    def __repr__(self) -> str:
        return f'Pawn'

