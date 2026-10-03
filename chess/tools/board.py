from figures.figure import Figure
from .cell import Cell
from .position import Position

class Board:
    def __init__(self):
        self._board = self._create_board()

    @property
    def board(self):
        return self._board

    def __repr__(self) -> str:
        pass # TODO

    def add_figure(self, figure : Figure):
        self._board[figure.position] = Cell(figure)

    @staticmethod
    def _create_board() -> dict[Position, Cell]:
        board = {}
        for num in Position.NUM_COORD:
            for letter in Position.LETTERS_COORD:
                board[Position(f"{letter}{num}")] = Cell()
        return board


