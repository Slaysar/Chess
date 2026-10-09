from tools.color import Color
from tools.position import Position
from pieces.rook import Rook
from pieces.pawn import Pawn


def pos(s: str) -> Position:
    return Position.from_str(s)


def moves(piece, board, at: str) -> set[str]:
    return {str(p) for p in piece.get_possible_moves(board, pos(at))}


def test_rook_empty_board_has_14_moves(board):
    rook = Rook(Color.WHITE)
    board.place(rook, pos("d4"))
    assert len(moves(rook, board, "d4")) == 14


def test_rook_blocked_by_own_piece(board):
    rook = Rook(Color.WHITE)
    board.place(rook, pos("e3"))
    board.place(Pawn(Color.WHITE), pos("d3"))
    assert "d3" not in moves(rook, board, "e3")
    assert "c3" not in moves(rook, board, "e3")


def test_rook_captures_enemy_and_stops(board):
    rook = Rook(Color.WHITE)
    board.place(rook, pos("e3"))
    board.place(Pawn(Color.BLACK), pos("e5"))
    result = moves(rook, board, "e3")
    assert "e4" in result
    assert "e5" in result       # взятие
    assert "e6" not in result   # дальше не проходит


def test_rook_example(board):
    rook = Rook(Color.WHITE)
    board.place(rook, pos("e3"))
    board.place(Pawn(Color.BLACK), pos("e4"))
    board.place(Pawn(Color.WHITE), pos("d3"))
    assert moves(rook, board, "e3") == {"e1", "e2", "e4", "f3", "g3", "h3"}