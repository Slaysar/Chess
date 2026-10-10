from tools.color import Color
from pieces.king import King
from pieces.rook import Rook
from pieces.knight import Knight
from tests.helpers import pos


def put(game, square, piece):
    game.board.place(piece, pos(square))


def legal(game, square) -> set[str]:
    return {str(p) for p in game.legal_moves(pos(square))}


def white_setup(game):
    king, rook_a, rook_h = King(Color.WHITE), Rook(Color.WHITE), Rook(Color.WHITE)
    put(game, "e1", king)
    put(game, "a1", rook_a)
    put(game, "h1", rook_h)
    put(game, "h8", King(Color.BLACK))
    return king, rook_a, rook_h


def test_white_kingside_castling(empty_game):
    king, _, rook = white_setup(empty_game)
    empty_game.make_move(pos("e1"), pos("g1"))
    assert empty_game.board.get(pos("g1")) is king
    assert empty_game.board.get(pos("f1")) is rook
    assert empty_game.board.get(pos("e1")) is None
    assert empty_game.board.get(pos("h1")) is None
    assert empty_game.turn == Color.BLACK


def test_white_queenside_castling(empty_game):
    king, rook, _ = white_setup(empty_game)
    empty_game.make_move(pos("e1"), pos("c1"))
    assert empty_game.board.get(pos("c1")) is king
    assert empty_game.board.get(pos("d1")) is rook
    assert empty_game.board.get(pos("a1")) is None
    assert empty_game.board.get(pos("e1")) is None


def test_black_castling_both_sides(empty_game):
    put(empty_game, "e8", King(Color.BLACK))
    put(empty_game, "a8", Rook(Color.BLACK))
    put(empty_game, "h8", Rook(Color.BLACK))
    put(empty_game, "d1", King(Color.WHITE))
    empty_game.turn = Color.BLACK
    assert {"g8", "c8"} <= legal(empty_game, "e8")
    empty_game.make_move(pos("e8"), pos("c8"))
    assert isinstance(empty_game.board.get(pos("d8")), Rook)
    assert isinstance(empty_game.board.get(pos("c8")), King)


def test_castling_in_real_game(game):
    for src, dst in [("e2", "e4"), ("e7", "e5"), ("g1", "f3"),
                     ("b8", "c6"), ("f1", "c4"), ("g8", "f6")]:
        game.make_move(pos(src), pos(dst))
    game.make_move(pos("e1"), pos("g1"))
    assert isinstance(game.board.get(pos("g1")), King)
    assert isinstance(game.board.get(pos("f1")), Rook)


def test_flags_set_after_castling(empty_game):
    king, _, rook = white_setup(empty_game)
    empty_game.make_move(pos("e1"), pos("g1"))
    assert king.has_moved
    assert rook.has_moved


def test_no_castling_if_king_moved(empty_game):
    king, _, _ = white_setup(empty_game)
    king.has_moved = True
    assert "g1" not in legal(empty_game, "e1")
    assert "c1" not in legal(empty_game, "e1")


def test_no_castling_with_rook_that_moved(empty_game):
    _, _, rook_h = white_setup(empty_game)
    rook_h.has_moved = True
    assert "g1" not in legal(empty_game, "e1")
    assert "c1" in legal(empty_game, "e1")            # с другой ладьёй можно


def test_no_castling_through_pieces(empty_game):
    white_setup(empty_game)
    put(empty_game, "b1", Knight(Color.WHITE))        # мешает только длинной
    assert "c1" not in legal(empty_game, "e1")
    assert "g1" in legal(empty_game, "e1")


def test_no_castling_out_of_check(empty_game):
    white_setup(empty_game)
    put(empty_game, "e8", Rook(Color.BLACK))
    assert "g1" not in legal(empty_game, "e1")
    assert "c1" not in legal(empty_game, "e1")


def test_no_castling_through_attacked_square(empty_game):
    white_setup(empty_game)
    put(empty_game, "f8", Rook(Color.BLACK))          # бьёт f1
    assert "g1" not in legal(empty_game, "e1")
    assert "c1" in legal(empty_game, "e1")


def test_no_castling_into_attacked_square(empty_game):
    white_setup(empty_game)
    put(empty_game, "g8", Rook(Color.BLACK))          # бьёт g1
    assert "g1" not in legal(empty_game, "e1")


def test_queenside_allowed_when_b1_attacked(empty_game):
    white_setup(empty_game)
    put(empty_game, "b8", Rook(Color.BLACK))          # b1 под боем, но король там не идёт
    assert "c1" in legal(empty_game, "e1")


def test_no_castling_if_king_not_on_start_square(empty_game):
    put(empty_game, "d1", King(Color.WHITE))
    put(empty_game, "h1", Rook(Color.WHITE))
    put(empty_game, "h8", King(Color.BLACK))
    assert "f1" not in legal(empty_game, "d1")


def test_legal_moves_does_not_change_board_for_castling(empty_game):
    king, rook_a, rook_h = white_setup(empty_game)
    empty_game.legal_moves(pos("e1"))
    assert empty_game.board.get(pos("e1")) is king
    assert empty_game.board.get(pos("a1")) is rook_a
    assert empty_game.board.get(pos("h1")) is rook_h
    assert empty_game.board.get(pos("f1")) is None
    assert not king.has_moved