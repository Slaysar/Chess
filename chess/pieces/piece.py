from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from tools.color import Color

if TYPE_CHECKING:
    from tools.board import Board
    from tools.position import Position

class Piece(ABC):

    SYMBOL: str = "?"

    def __init__(self, color: Color):
        self._color = color
        self.has_moved = False

    def __repr__(self) -> str:
        return f"{self.SYMBOL}_{self._color.name[0]}"

    @property
    def color(self) -> Color:
        return self._color

    @abstractmethod
    def get_possible_moves(self, board : Board, position : Position) -> set[Position]:
        """Узнать возможные ходы для фигуры"""
        ...
