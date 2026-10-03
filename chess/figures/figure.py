from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from tools.position import Position
from tools.color import Color

if TYPE_CHECKING:
    from tools.board import Board

class Figure(ABC):

    def __init__(self, board : Board, position: Position, color: Color):
        self._position = position
        self._color = color
        self.board = board
        board.add_figure(self)
        self._possible_moves = self.get_possible_moves()

    @abstractmethod
    def __repr__(self) -> str:
        ...

    __str__ = __repr__

    @property
    def color(self):
        return self._color

    @property
    def position(self):
        return self._position

    @abstractmethod
    def get_possible_moves(self) -> set[Position]:
        """"Узнать возможные ходы для фигуры"""
        ...

    def move_to(self, position: Position):
        """Переместить фигуру на заданную позицию"""
        pass

    def death(self):
        """Фигуру съели"""
        pass
