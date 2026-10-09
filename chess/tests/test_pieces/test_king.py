from tools.color import Color
from pieces.king import King
from pieces.pawn import Pawn
from tests.helpers import pos, moves


def test_king_center_has_8_moves(board):
    king = King(Color.WHITE)
    board.place(king, pos("d4"))
    assert moves(king, board, "d4") == {"c3", "c4", "c5", "d3", "d5", "e3", "e4", "e5"}


def test_king_corner_has_3_moves(board):
    king = King(Color.WHITE)
    board.place(king, pos("a1"))
    assert moves(king, board, "a1") == {"a2", "b1", "b2"}


def test_king_cannot_step_on_own_piece(board):
    king = King(Color.WHITE)
    board.place(king, pos("d4"))
    board.place(Pawn(Color.WHITE), pos("d5"))
    assert "d5" not in moves(king, board, "d4")


def test_king_captures_enemy(board):
    king = King(Color.WHITE)
    board.place(king, pos("d4"))
    board.place(Pawn(Color.BLACK), pos("d5"))
    assert "d5" in moves(king, board, "d4")