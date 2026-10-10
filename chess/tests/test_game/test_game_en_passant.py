import pytest
from tools.color import Color
from pieces.king import King
from pieces.pawn import Pawn
from pieces.rook import Rook
from tests.helpers import pos


def put(game, square, piece):
    game.board.place(piece, pos(square))


def legal(game, square) -> set[str]:
    return {str(p) for p in game.legal_moves(pos(square))}


def base(empty_game):
    """Белая пешка e5, чёрная d7, чёрные ходят"""
    put(empty_game, "a1", King(Color.WHITE))
    put(empty_game, "h8", King(Color.BLACK))
    put(empty_game, "e5", Pawn(Color.WHITE))
    put(empty_game, "d7", Pawn(Color.BLACK))
    empty_game.turn = Color.BLACK


def test_double_step_sets_target_and_next_move_clears_it(game):
    game.make_move(pos("e2"), pos("e4"))
    assert game.board.en_passant_target == pos("e3")
    game.make_move(pos("a7"), pos("a6"))
    assert game.board.en_passant_target is None


def test_en_passant_capture(empty_game):
    base(empty_game)
    empty_game.make_move(pos("d7"), pos("d5"))
    empty_game.make_move(pos("e5"), pos("d6"))
    pawn = empty_game.board.get(pos("d6"))
    assert isinstance(pawn, Pawn) and pawn.color is Color.WHITE
    assert empty_game.board.get(pos("d5")) is None    # чёрная пешка снята
    assert empty_game.board.get(pos("e5")) is None


def test_en_passant_must_be_used_immediately(empty_game):
    base(empty_game)
    put(empty_game, "a2", Pawn(Color.WHITE))
    put(empty_game, "h7", Pawn(Color.BLACK))
    empty_game.make_move(pos("d7"), pos("d5"))
    empty_game.make_move(pos("a2"), pos("a3"))        # не воспользовались
    empty_game.make_move(pos("h7"), pos("h6"))
    with pytest.raises(ValueError, match="Недопустимый ход"):
        empty_game.make_move(pos("e5"), pos("d6"))


def test_no_en_passant_after_single_step(empty_game):
    put(empty_game, "a1", King(Color.WHITE))
    put(empty_game, "h8", King(Color.BLACK))
    put(empty_game, "e5", Pawn(Color.WHITE))
    put(empty_game, "d6", Pawn(Color.BLACK))
    empty_game.turn = Color.BLACK
    empty_game.make_move(pos("d6"), pos("d5"))        # одна клетка
    assert legal(empty_game, "e5") == {"e6"}


def test_en_passant_illegal_if_it_exposes_king(empty_game):
    put(empty_game, "a5", King(Color.WHITE))
    put(empty_game, "e5", Pawn(Color.WHITE))
    put(empty_game, "d7", Pawn(Color.BLACK))
    put(empty_game, "h5", Rook(Color.BLACK))
    put(empty_game, "h8", King(Color.BLACK))
    empty_game.turn = Color.BLACK
    empty_game.make_move(pos("d7"), pos("d5"))
    # после e5xd6 с пятого ряда исчезли бы обе пешки, и ладья h5 дала бы шах
    assert "d6" not in legal(empty_game, "e5")


def test_legal_moves_does_not_change_board_for_en_passant(empty_game):
    base(empty_game)
    white, black = empty_game.board.get(pos("e5")), empty_game.board.get(pos("d7"))
    empty_game.make_move(pos("d7"), pos("d5"))
    empty_game.legal_moves(pos("e5"))
    assert empty_game.board.get(pos("e5")) is white
    assert empty_game.board.get(pos("d5")) is black
    assert empty_game.board.get(pos("d6")) is None
    assert empty_game.board.en_passant_target == pos("d6")