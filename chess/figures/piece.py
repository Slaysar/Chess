from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from tools.color import Color

if TYPE_CHECKING:
    from tools.board import Board
    from tools.position import Position

class Piece(ABC):

    def __init__(self, color: Color):
        self._color = color

    @abstractmethod
    def __repr__(self) -> str:
        ...

    @property
    def color(self):
        return self._color

    @abstractmethod
    def get_possible_moves(self, board : Board, position : Position) -> set[Position]:
        """Узнать возможные ходы для фигуры"""
        ...
