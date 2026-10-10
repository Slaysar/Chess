from tools.color import Color
from tools.game_status import GameStatus
from pieces.king import King
from pieces.pawn import Pawn
from pieces.rook import Rook
from tests.helpers import pos

CYCLE = [("g1", "f3"), ("g8", "f6"), ("f3", "g1"), ("f6", "g8")]   # возврат в ту же позицию


def put(game, square, piece):
    game.board.place(piece, pos(square))


def play(game, moves):
    for src, dst in moves:
        game.make_move(pos(src), pos(dst))


def test_start_position_counts_once(game):
    assert game.repetition_count() == 1


def test_one_cycle_gives_second_occurrence(game):
    play(game, CYCLE)
    assert game.repetition_count() == 2
    assert game.status() == GameStatus.PLAYING


def test_threefold_repetition_is_draw(game):
    play(game, CYCLE * 2)
    assert game.repetition_count() == 3
    assert game.status() == GameStatus.DRAW
    assert game.draw_reason() == "троекратное повторение"


def test_pawn_move_resets_repetition_window(game):
    play(game, CYCLE)
    game.make_move(pos("e2"), pos("e4"))
    assert game.repetition_count() == 1


def test_repetition_after_pawn_move_still_counts(game):
    play(game, [("e2", "e4"), ("e7", "e5")] + CYCLE * 2)
    assert game.status() == GameStatus.DRAW


def test_same_pieces_different_side_to_move_is_not_repetition(game):
    play(game, [("g1", "f3"), ("g8", "f6"), ("f3", "g1")])   # те же фигуры, но ход чёрных
    assert game.repetition_count() == 1


def test_position_key_depends_on_castling_rights(empty_game):
    rook = Rook(Color.WHITE)
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "h1", rook)
    put(empty_game, "e8", King(Color.BLACK))
    before = empty_game.position_key()
    rook.has_moved = True
    assert empty_game.position_key() != before


def test_en_passant_ignored_when_capture_impossible(game):
    game.make_move(pos("e2"), pos("e4"))
    assert game.position_key()[3] is None


def test_en_passant_counts_when_capture_possible(empty_game):
    put(empty_game, "a1", King(Color.WHITE))
    put(empty_game, "h8", King(Color.BLACK))
    put(empty_game, "e2", Pawn(Color.WHITE))
    put(empty_game, "d4", Pawn(Color.BLACK))
    empty_game.positions = [empty_game.position_key()]
    empty_game.make_move(pos("e2"), pos("e4"))
    assert empty_game.position_key()[3] == pos("e3")


def test_repetition_with_manual_board(empty_game):
    put(empty_game, "a1", King(Color.WHITE))
    put(empty_game, "h8", King(Color.BLACK))
    put(empty_game, "a2", Rook(Color.WHITE))
    empty_game.positions = [empty_game.position_key()]
    cycle = [("a2", "b2"), ("h8", "g8"), ("b2", "a2"), ("g8", "h8")]
    play(empty_game, cycle * 2)
    assert empty_game.status() == GameStatus.DRAW