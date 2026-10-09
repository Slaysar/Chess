from tools.color import Color
from tools.position import Position
from pieces.bishop import Bishop
from pieces.pawn import Pawn


def sq(s: str) -> Position:
    return Position.from_str(s)


def moves(piece, board, at: str) -> set[str]:
    return {str(p) for p in piece.get_possible_moves(board, sq(at))}


def test_bishop_center_has_13_moves(board):
    bishop = Bishop(Color.WHITE)
    board.place(bishop, sq("d4"))
    assert len(moves(bishop, board, "d4")) == 13


def test_bishop_corner_has_7_moves(board):
    bishop = Bishop(Color.WHITE)
    board.place(bishop, sq("a1"))
    assert moves(bishop, board, "a1") == {"b2", "c3", "d4", "e5", "f6", "g7", "h8"}


def test_bishop_moves_only_diagonally(board):
    bishop = Bishop(Color.WHITE)
    board.place(bishop, sq("d4"))
    for m in moves(bishop, board, "d4"):
        assert m[0] != "d" and m[1] != "4"   # не по вертикали и не по горизонтали


def test_bishop_blocked_by_own_piece(board):
    bishop = Bishop(Color.WHITE)
    board.place(bishop, sq("c1"))
    board.place(Pawn(Color.WHITE), sq("d2"))
    assert moves(bishop, board, "c1") == {"b2", "a3"}


def test_bishop_captures_enemy_and_stops(board):
    bishop = Bishop(Color.WHITE)
    board.place(bishop, sq("c1"))
    board.place(Pawn(Color.BLACK), sq("e3"))
    assert moves(bishop, board, "c1") == {"d2", "e3", "b2", "a3"}   # f4 уже недоступна