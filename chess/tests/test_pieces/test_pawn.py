from tools.color import Color
from pieces.pawn import Pawn
from tests.helpers import pos, moves


def test_white_pawn_start_two_squares(board):
    pawn = Pawn(Color.WHITE)
    board.place(pawn, pos("e2"))
    assert moves(pawn, board, "e2") == {"e3", "e4"}


def test_white_pawn_after_start_one_square(board):
    pawn = Pawn(Color.WHITE)
    board.place(pawn, pos("e3"))
    assert moves(pawn, board, "e3") == {"e4"}


def test_black_pawn_moves_down(board):
    pawn = Pawn(Color.BLACK)
    board.place(pawn, pos("e7"))
    assert moves(pawn, board, "e7") == {"e6", "e5"}


def test_pawn_blocked_in_front(board):
    pawn = Pawn(Color.WHITE)
    board.place(pawn, pos("e2"))
    board.place(Pawn(Color.BLACK), pos("e3"))
    assert moves(pawn, board, "e2") == set()  # и двойной ход тоже закрыт


def test_pawn_cannot_jump_over_piece(board):
    pawn = Pawn(Color.WHITE)
    board.place(pawn, pos("e2"))
    board.place(Pawn(Color.BLACK), pos("e4"))
    assert moves(pawn, board, "e2") == {"e3"}


def test_pawn_captures_diagonally(board):
    pawn = Pawn(Color.WHITE)
    board.place(pawn, pos("e4"))
    board.place(Pawn(Color.BLACK), pos("d5"))
    board.place(Pawn(Color.WHITE), pos("f5"))  # своя, бить нельзя
    assert moves(pawn, board, "e4") == {"e5", "d5"}


def test_pawn_on_edge_no_crash(board):
    pawn = Pawn(Color.WHITE)
    board.place(pawn, pos("a4"))
    assert moves(pawn, board, "a4") == {"a5"}
