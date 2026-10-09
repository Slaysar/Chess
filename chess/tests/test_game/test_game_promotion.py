import pytest
from tools.color import Color
from tools.game_status import GameStatus
from pieces.king import King
from pieces.queen import Queen
from pieces.knight import Knight
from pieces.pawn import Pawn
from pieces.rook import Rook
from tests.helpers import pos


def put(game, square, piece):
    game.board.place(piece, pos(square))


def test_is_promotion(empty_game):
    put(empty_game, "e7", Pawn(Color.WHITE))
    put(empty_game, "a2", Pawn(Color.WHITE))
    assert empty_game.is_promotion(pos("e7"), pos("e8"))
    assert not empty_game.is_promotion(pos("a2"), pos("a3"))
    assert not empty_game.is_promotion(pos("c5"), pos("c6"))   # пустая клетка


def test_promotion_to_chosen_piece(empty_game):
    put(empty_game, "a1", King(Color.WHITE))
    put(empty_game, "h6", King(Color.BLACK))
    put(empty_game, "e7", Pawn(Color.WHITE))
    empty_game.make_move(pos("e7"), pos("e8"), Knight)
    assert isinstance(empty_game.board.get(pos("e8")), Knight)


def test_black_pawn_promotes_on_first_row(empty_game):
    put(empty_game, "a8", King(Color.BLACK))
    put(empty_game, "h6", King(Color.WHITE))
    put(empty_game, "e2", Pawn(Color.BLACK))
    empty_game.turn = Color.BLACK
    empty_game.make_move(pos("e2"), pos("e1"), Rook)
    piece = empty_game.board.get(pos("e1"))
    assert isinstance(piece, Rook)
    assert piece.color is Color.BLACK


def test_promotion_by_capture(empty_game):
    put(empty_game, "a1", King(Color.WHITE))
    put(empty_game, "h6", King(Color.BLACK))
    put(empty_game, "e7", Pawn(Color.WHITE))
    put(empty_game, "d8", Rook(Color.BLACK))
    empty_game.make_move(pos("e7"), pos("d8"), Queen)
    piece = empty_game.board.get(pos("d8"))
    assert isinstance(piece, Queen)
    assert piece.color is Color.WHITE


@pytest.mark.parametrize("impossible", [King, Pawn])
def test_invalid_promotion_piece_raises_and_changes_nothing(empty_game, impossible):
    pawn = Pawn(Color.WHITE)
    put(empty_game, "a1", King(Color.WHITE))
    put(empty_game, "h6", King(Color.BLACK))
    put(empty_game, "e7", pawn)
    with pytest.raises(ValueError, match="превратить нельзя"):
        empty_game.make_move(pos("e7"), pos("e8"), impossible)
    assert empty_game.board.get(pos("e7")) is pawn
    assert empty_game.board.get(pos("e8")) is None
    assert empty_game.turn == Color.WHITE


def test_ordinary_move_does_not_promote(game):
    game.make_move(pos("e2"), pos("e4"))
    assert isinstance(game.board.get(pos("e4")), Pawn)


def test_promotion_can_give_checkmate(empty_game):
    put(empty_game, "a1", King(Color.WHITE))
    put(empty_game, "g8", King(Color.BLACK))
    for s in ("f7", "g7", "h7"):
        put(empty_game, s, Pawn(Color.BLACK))
    put(empty_game, "e7", Pawn(Color.WHITE))
    empty_game.make_move(pos("e7"), pos("e8"), Queen)      # e8=Q#
    assert empty_game.status() == GameStatus.CHECKMATE