import pytest
from tools.color import Color
from pieces.knight import Knight
from pieces.pawn import Pawn
from tests.helpers import pos


def test_turn_passes_to_black_after_white_move(game):
    game.make_move(pos("e2"), pos("e4"))
    assert game.turn == Color.BLACK


def test_knight_jumps_over_pawns_and_moves(game):
    game.make_move(pos("b1"), pos("c3"))
    assert game.board.get(pos("b1")) is None
    assert isinstance(game.board.get(pos("c3")), Knight)


def test_turn_passes_to_white_after_black_move(game):
    game.make_move(pos("e2"), pos("e4"))
    game.make_move(pos("e7"), pos("e6"))
    assert game.turn == Color.WHITE


def test_capture_replaces_enemy_piece(game):
    game.make_move(pos("e2"), pos("e4"))
    game.make_move(pos("d7"), pos("d5"))
    game.make_move(pos("e4"), pos("d5"))
    assert isinstance(game.board.get(pos("d5")), Pawn)
    assert game.board.get(pos("e4")) is None
    assert game.board.get(pos("d5")).color == Color.WHITE


def test_failed_move_changes_nothing(game):
    with pytest.raises(ValueError):
        game.make_move(pos("e2"), pos("e5"))
    assert game.turn == Color.WHITE
    assert isinstance(game.board.get(pos("e2")), Pawn)
    assert game.board.get(pos("e5")) is None


def test_move_not_in_possible_moves_raises(game):
    with pytest.raises(ValueError, match="Недопустимый ход"):
        game.make_move(pos("e2"), pos("e5"))


def test_move_from_empty_cell_raises(game):
    with pytest.raises(ValueError, match="На клетке нет фигуры"):
        game.make_move(pos("e3"), pos("e5"))


def test_black_cannot_move_first(game):
    with pytest.raises(ValueError, match="Сейчас ходит другой цвет"):
        game.make_move(pos("e7"), pos("e6"))
