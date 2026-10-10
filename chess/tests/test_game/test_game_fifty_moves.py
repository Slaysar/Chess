import pytest
from tools.color import Color
from tools.game_status import GameStatus
from pieces.king import King
from pieces.knight import Knight
from pieces.pawn import Pawn
from pieces.rook import Rook
from tests.helpers import pos


def put(game, square, piece):
    game.board.place(piece, pos(square))


def rook_endgame(game):
    """Короли и белая ладья на a2: материала достаточно, ничьей по материалу нет"""
    put(game, "e1", King(Color.WHITE))
    put(game, "e8", King(Color.BLACK))
    put(game, "a2", Rook(Color.WHITE))


# ---------- счётчик ----------

def test_clock_starts_at_zero(game):
    assert game.half_move_clock == 0


def test_clock_counts_quiet_moves(game):
    game.make_move(pos("g1"), pos("f3"))
    assert game.half_move_clock == 1
    game.make_move(pos("b8"), pos("c6"))
    assert game.half_move_clock == 2


def test_clock_resets_on_pawn_move(game):
    game.make_move(pos("g1"), pos("f3"))
    game.make_move(pos("b8"), pos("c6"))
    game.make_move(pos("e2"), pos("e4"))
    assert game.half_move_clock == 0


def test_clock_resets_on_capture(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "e8", King(Color.BLACK))
    put(empty_game, "a1", Rook(Color.WHITE))
    put(empty_game, "a5", Knight(Color.BLACK))
    empty_game.half_move_clock = 10
    empty_game.make_move(pos("a1"), pos("a5"))
    assert empty_game.half_move_clock == 0


def test_clock_resets_on_en_passant(empty_game):
    put(empty_game, "a1", King(Color.WHITE))
    put(empty_game, "h8", King(Color.BLACK))
    put(empty_game, "e5", Pawn(Color.WHITE))
    put(empty_game, "d7", Pawn(Color.BLACK))
    empty_game.turn = Color.BLACK
    empty_game.make_move(pos("d7"), pos("d5"))
    empty_game.half_move_clock = 7
    empty_game.make_move(pos("e5"), pos("d6"))
    assert empty_game.half_move_clock == 0


def test_clock_increases_after_castling(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "h1", Rook(Color.WHITE))
    put(empty_game, "e8", King(Color.BLACK))
    empty_game.half_move_clock = 4
    empty_game.make_move(pos("e1"), pos("g1"))
    assert empty_game.half_move_clock == 5


def test_failed_move_does_not_change_clock(game):
    game.half_move_clock = 5
    with pytest.raises(ValueError):
        game.make_move(pos("e2"), pos("e5"))
    assert game.half_move_clock == 5


# ---------- ничья ----------

def test_draw_at_100_half_moves(empty_game):
    rook_endgame(empty_game)
    empty_game.half_move_clock = 99
    empty_game.make_move(pos("a2"), pos("a3"))
    assert empty_game.half_move_clock == 100
    assert empty_game.status() == GameStatus.DRAW
    assert empty_game.draw_reason() == "правило 50 ходов"


def test_no_draw_at_99_half_moves(empty_game):
    rook_endgame(empty_game)
    empty_game.half_move_clock = 98
    empty_game.make_move(pos("a2"), pos("a3"))
    assert empty_game.half_move_clock == 99
    assert empty_game.status() == GameStatus.PLAYING


def test_checkmate_on_100th_half_move_is_still_checkmate(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "a1", Rook(Color.WHITE))
    put(empty_game, "g8", King(Color.BLACK))
    for square in ("f7", "g7", "h7"):
        put(empty_game, square, Pawn(Color.BLACK))
    empty_game.half_move_clock = 99
    empty_game.make_move(pos("a1"), pos("a8"))
    assert empty_game.half_move_clock == 100
    assert empty_game.status() == GameStatus.CHECKMATE
    assert empty_game.history[-1].notation == "Ra8#"


# ---------- суффикс шаха не теряется при ничьей ----------

def test_check_suffix_kept_when_move_ends_in_draw(empty_game):
    rook_endgame(empty_game)
    empty_game.half_move_clock = 99
    empty_game.make_move(pos("a2"), pos("a8"))      # шах по восьмому ряду
    assert empty_game.status() == GameStatus.DRAW
    assert empty_game.history[-1].notation == "Ra8+"


def test_check_suffix_kept_with_insufficient_material(empty_game):
    put(empty_game, "a1", King(Color.WHITE))
    put(empty_game, "e8", King(Color.BLACK))
    put(empty_game, "f5", Knight(Color.WHITE))
    empty_game.make_move(pos("f5"), pos("d6"))      # конь с d6 бьёт e8
    assert empty_game.status() == GameStatus.DRAW   # король и конь против короля
    assert empty_game.history[-1].notation == "Nd6+"


# ---------- причина ничьей ----------

def test_draw_reason_none_in_normal_game(game):
    assert game.draw_reason() is None


def test_draw_reason_insufficient_material(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "e8", King(Color.BLACK))
    assert empty_game.draw_reason() == "недостаточно материала"