from tools.color import Color
from tools.position import Position
from pieces.queen import Queen
from pieces.rook import Rook
from pieces.bishop import Bishop
from pieces.pawn import Pawn


def sq(s: str) -> Position:
    return Position.from_str(s)


def moves(piece, board, at: str) -> set[str]:
    return {str(p) for p in piece.get_possible_moves(board, sq(at))}


def test_queen_center_has_27_moves(board):
    queen = Queen(Color.WHITE)
    board.place(queen, sq("d4"))
    assert len(moves(queen, board, "d4")) == 27


def test_queen_corner_has_21_moves(board):
    queen = Queen(Color.WHITE)
    board.place(queen, sq("a1"))
    assert len(moves(queen, board, "a1")) == 21


def test_queen_is_rook_plus_bishop(board):
    queen = Queen(Color.WHITE)
    board.place(queen, sq("d4"))
    queen_moves = moves(queen, board, "d4")

    rook_moves = moves(Rook(Color.WHITE), board, "d4")
    bishop_moves = moves(Bishop(Color.WHITE), board, "d4")

    assert queen_moves == rook_moves | bishop_moves


def test_queen_surrounded_by_own_pieces_has_no_moves(board):
    queen = Queen(Color.WHITE)
    board.place(queen, sq("d4"))
    for s in ["c3", "c4", "c5", "d3", "d5", "e3", "e4", "e5"]:
        board.place(Pawn(Color.WHITE), sq(s))
    assert moves(queen, board, "d4") == set()


def test_queen_captures_straight_and_stops(board):
    queen = Queen(Color.WHITE)
    board.place(queen, sq("d4"))
    board.place(Pawn(Color.BLACK), sq("d6"))
    result = moves(queen, board, "d4")
    assert "d5" in result
    assert "d6" in result       # взятие
    assert "d7" not in result   # дальше не проходит


def test_queen_captures_diagonally_and_stops(board):
    queen = Queen(Color.WHITE)
    board.place(queen, sq("d4"))
    board.place(Pawn(Color.BLACK), sq("f6"))
    result = moves(queen, board, "d4")
    assert "e5" in result
    assert "f6" in result
    assert "g7" not in result