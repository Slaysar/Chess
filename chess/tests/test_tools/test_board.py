from tools.board import Board
from tools.color import Color
from tools.position import Position
from pieces.king import King
from pieces.queen import Queen
from pieces.pawn import Pawn
from tests.helpers import pos



def test_setup_has_32_pieces():
    board = Board()
    board.setup()
    count = sum(
        board.get(Position(r, c)) is not None
        for r in range(8) for c in range(8)
    )
    assert count == 32


def test_setup_kings_and_queens_placement():
    board = Board()
    board.setup()
    assert isinstance(board.get(pos("e1")), King) and board.get(pos("e1")).color is Color.WHITE
    assert isinstance(board.get(pos("d1")), Queen) and board.get(pos("d1")).color is Color.WHITE
    assert isinstance(board.get(pos("e8")), King) and board.get(pos("e8")).color is Color.BLACK
    assert isinstance(board.get(pos("d8")), Queen) and board.get(pos("d8")).color is Color.BLACK


def test_setup_pawn_rows():
    board = Board()
    board.setup()
    for col in range(8):
        white = board.get(Position(1, col))
        black = board.get(Position(6, col))
        assert isinstance(white, Pawn) and white.color is Color.WHITE
        assert isinstance(black, Pawn) and black.color is Color.BLACK


def test_setup_middle_is_empty():
    board = Board()
    board.setup()
    for row in range(2, 6):
        for col in range(8):
            assert board.get(Position(row, col)) is None


def test_setup_twice_does_not_duplicate():
    board = Board()
    board.setup()
    board.setup()
    assert board.get(pos("e1")) is not None