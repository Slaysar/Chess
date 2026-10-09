import pytest
from tools.color import Color
from tools.game_status import GameStatus
from pieces.king import King
from pieces.rook import Rook
from pieces.knight import Knight
from pieces.pawn import Pawn
from tests.helpers import pos


def put(game, square, piece):
    game.board.place(piece, pos(square))


def legal(game, square) -> set[str]:
    return {str(p) for p in game.legal_moves(pos(square))}


# ---------- is_in_check ----------

def test_start_position_no_check_and_has_moves(game):
    assert not game.board.is_in_check(Color.WHITE)
    assert not game.board.is_in_check(Color.BLACK)
    assert game.has_legal_moves(Color.WHITE)


def test_check_by_rook(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "e8", Rook(Color.BLACK))
    assert empty_game.board.is_in_check(Color.WHITE)


def test_no_check_when_line_blocked(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "e4", Pawn(Color.WHITE))
    put(empty_game, "e8", Rook(Color.BLACK))
    assert not empty_game.board.is_in_check(Color.WHITE)


def test_check_by_knight(empty_game):
    put(empty_game, "e4", King(Color.WHITE))
    put(empty_game, "f6", Knight(Color.BLACK))
    assert empty_game.board.is_in_check(Color.WHITE)


def test_check_by_pawn_diagonal(empty_game):
    put(empty_game, "e4", King(Color.WHITE))
    put(empty_game, "d5", Pawn(Color.BLACK))
    assert empty_game.board.is_in_check(Color.WHITE)


def test_pawn_in_front_does_not_give_check(empty_game):
    put(empty_game, "e4", King(Color.WHITE))
    put(empty_game, "e5", Pawn(Color.BLACK))
    assert not empty_game.board.is_in_check(Color.WHITE)


def test_no_king_means_no_check(empty_game):
    put(empty_game, "e8", Rook(Color.BLACK))
    assert not empty_game.board.is_in_check(Color.WHITE)


# ---------- legal_moves ----------

def test_pinned_rook_can_only_move_along_pin_line(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "e2", Rook(Color.WHITE))
    put(empty_game, "e8", Rook(Color.BLACK))
    assert legal(empty_game, "e2") == {"e3", "e4", "e5", "e6", "e7", "e8"}


def test_king_cannot_step_onto_attacked_square(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "d8", Rook(Color.BLACK))
    assert legal(empty_game, "e1") == {"e2", "f1", "f2"}


def test_king_cannot_capture_protected_piece(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "e2", Rook(Color.BLACK))
    put(empty_game, "e8", Rook(Color.BLACK))
    assert "e2" not in legal(empty_game, "e1")


def test_under_check_only_resolving_moves_allowed(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "e8", Rook(Color.BLACK))
    put(empty_game, "a4", Rook(Color.WHITE))
    put(empty_game, "h2", Pawn(Color.WHITE))
    assert legal(empty_game, "a4") == {"e4"}
    assert legal(empty_game, "h2") == set()


def test_legal_moves_does_not_change_board(empty_game):
    king, rook, enemy = King(Color.WHITE), Rook(Color.WHITE), Rook(Color.BLACK)
    put(empty_game, "e1", king)
    put(empty_game, "e2", rook)
    put(empty_game, "e8", enemy)
    empty_game.legal_moves(pos("e2"))
    assert empty_game.board.get(pos("e1")) is king
    assert empty_game.board.get(pos("e2")) is rook
    assert empty_game.board.get(pos("e8")) is enemy
    assert empty_game.turn == Color.WHITE


# ---------- make_move ----------

def test_make_move_rejects_move_that_exposes_king(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "e2", Rook(Color.WHITE))
    put(empty_game, "e8", Rook(Color.BLACK))
    with pytest.raises(ValueError, match="Недопустимый ход"):
        empty_game.make_move(pos("e2"), pos("d2"))
    assert empty_game.turn == Color.WHITE
    assert isinstance(empty_game.board.get(pos("e2")), Rook)


# ---------- status ----------

def test_status_playing_at_start(game):
    assert game.status() == GameStatus.PLAYING


def test_status_check(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "e8", Rook(Color.BLACK))
    put(empty_game, "a2", Rook(Color.WHITE))  # может перекрыть, значит не мат
    assert empty_game.status() == GameStatus.CHECK


SCHOLARS_MATE = [
    ("e2", "e4"), ("e7", "e5"),
    ("d1", "h5"), ("b8", "c6"),
    ("f1", "c4"), ("g8", "f6"),
]


def play(game, moves):
    for src, dst in moves:
        game.make_move(pos(src), pos(dst))


def test_scholars_mate_not_over_before_last_move(game):
    play(game, SCHOLARS_MATE)
    assert game.status() == GameStatus.PLAYING  # перед Qxf7 партия ещё идёт


def test_scholars_mate_is_checkmate(game):
    play(game, SCHOLARS_MATE)
    game.make_move(pos("h5"), pos("f7"))  # Qxf7#
    assert game.status() == GameStatus.CHECKMATE
    assert game.turn == Color.BLACK
    assert game.board.is_in_check(Color.BLACK)


def test_scholars_mate_black_king_has_no_escape(game):
    play(game, SCHOLARS_MATE)
    game.make_move(pos("h5"), pos("f7"))
    assert not game.has_legal_moves(Color.BLACK)
    assert legal(game, "e8") == set()  # f7 защищена слоном c4, e7 бьёт ферзь


def test_scholars_mate_black_cannot_move_after_mate(game):
    play(game, SCHOLARS_MATE)
    game.make_move(pos("h5"), pos("f7"))
    with pytest.raises(ValueError, match="Недопустимый ход"):
        game.make_move(pos("e8"), pos("f7"))  # нельзя взять защищённого ферзя
