from tools.color import Color
from pieces.bishop import Bishop
from pieces.pawn import Pawn
from tests.helpers import pos, moves


def test_bishop_center_has_13_moves(board):
    bishop = Bishop(Color.WHITE)
    board.place(bishop, pos("d4"))
    assert len(moves(bishop, board, "d4")) == 13


def test_bishop_corner_has_7_moves(board):
    bishop = Bishop(Color.WHITE)
    board.place(bishop, pos("a1"))
    assert moves(bishop, board, "a1") == {"b2", "c3", "d4", "e5", "f6", "g7", "h8"}


def test_bishop_moves_only_diagonally(board):
    bishop = Bishop(Color.WHITE)
    board.place(bishop, pos("d4"))
    for m in moves(bishop, board, "d4"):
        assert m[0] != "d" and m[1] != "4"   # не по вертикали и не по горизонтали


def test_bishop_blocked_by_own_piece(board):
    bishop = Bishop(Color.WHITE)
    board.place(bishop, pos("c1"))
    board.place(Pawn(Color.WHITE), pos("d2"))
    assert moves(bishop, board, "c1") == {"b2", "a3"}


def test_bishop_captures_enemy_and_stops(board):
    bishop = Bishop(Color.WHITE)
    board.place(bishop, pos("c1"))
    board.place(Pawn(Color.BLACK), pos("e3"))
    assert moves(bishop, board, "c1") == {"d2", "e3", "b2", "a3"}   # f4 уже недоступна