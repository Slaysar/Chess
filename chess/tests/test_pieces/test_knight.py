from tools.color import Color
from pieces.knight import Knight
from pieces.pawn import Pawn
from tests.helpers import pos, moves



def test_knight_center_has_8_moves(board):
    knight = Knight(Color.WHITE)
    board.place(knight, pos("d4"))
    assert moves(knight, board, "d4") == {"b3", "b5", "c2", "c6", "e2", "e6", "f3", "f5"}


def test_knight_corner_has_2_moves(board):
    knight = Knight(Color.WHITE)
    board.place(knight, pos("a1"))
    assert moves(knight, board, "a1") == {"b3", "c2"}


def test_knight_jumps_over_pieces(board):
    knight = Knight(Color.WHITE)
    board.place(knight, pos("g1"))
    for s in ["f2", "g2", "h2"]:
        board.place(Pawn(Color.WHITE), pos(s))
    assert moves(knight, board, "g1") == {"e2", "f3", "h3"}


def test_knight_cannot_land_on_own_piece(board):
    knight = Knight(Color.WHITE)
    board.place(knight, pos("d4"))
    board.place(Pawn(Color.WHITE), pos("f5"))
    assert "f5" not in moves(knight, board, "d4")


def test_knight_captures_enemy(board):
    knight = Knight(Color.WHITE)
    board.place(knight, pos("d4"))
    board.place(Pawn(Color.BLACK), pos("f5"))
    assert "f5" in moves(knight, board, "d4")