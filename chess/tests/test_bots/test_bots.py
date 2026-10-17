from bots.common import all_moves, try_move, undo_move
from bots.greedy import GreedyBot
from bots.match import play_game
from bots.minimax import MinimaxBot
from pieces.king import King
from pieces.pawn import Pawn
from pieces.queen import Queen
from pieces.rook import Rook
from tools.color import Color
from tests.helpers import pos, snapshot
from tools.game_status import GameStatus

def put(game, square, piece):
    game.board.place(piece, pos(square))


def back_rank_mate(game):
    """Белые ходят, Rb1-b8 даёт мат"""
    put(game, "e1", King(Color.WHITE))
    put(game, "b1", Rook(Color.WHITE))
    put(game, "g8", King(Color.BLACK))
    for square in ("f7", "g7", "h7"):
        put(game, square, Pawn(Color.BLACK))
    return pos("b1"), pos("b8"), None


def queen_takes_protected_pawn(game):
    """Qd2xd5 теряет ферзя за пешку: d5 защищена пешкой e6"""
    put(game, "e1", King(Color.WHITE))
    put(game, "d2", Queen(Color.WHITE))
    put(game, "e8", King(Color.BLACK))
    put(game, "d5", Pawn(Color.BLACK))
    put(game, "e6", Pawn(Color.BLACK))
    return pos("d2"), pos("d5"), None


# ---------- пробные ходы ----------

def test_try_move_and_undo_restore_board(game):
    before = snapshot(game.board)
    for source, destination in all_moves(game, Color.WHITE):
        saved = try_move(game.board, source, destination)
        undo_move(game.board, source, destination, saved)
        assert snapshot(game.board) == before


def test_undo_returns_captured_piece(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "e8", King(Color.BLACK))
    put(empty_game, "a1", Rook(Color.WHITE))
    victim = Queen(Color.BLACK)
    put(empty_game, "a8", victim)
    saved = try_move(empty_game.board, pos("a1"), pos("a8"))
    undo_move(empty_game.board, pos("a1"), pos("a8"), saved)
    assert empty_game.board.get(pos("a8")) is victim


# ---------- общее для обоих ботов ----------

def test_bots_return_legal_moves_from_start(game):
    for bot in (GreedyBot(seed=1), MinimaxBot(depth=2, seed=1)):
        source, destination, _ = bot.choose_move(game)
        assert destination in game.legal_moves(source)


def test_choose_move_does_not_change_the_board(game):
    before = snapshot(game.board)
    GreedyBot(seed=1).choose_move(game)
    MinimaxBot(depth=2, seed=1).choose_move(game)
    assert snapshot(game.board) == before


def test_bot_promotes_to_queen(empty_game):
    put(empty_game, "a1", King(Color.WHITE))
    put(empty_game, "h6", King(Color.BLACK))
    put(empty_game, "e7", Pawn(Color.WHITE))
    put(empty_game, "d8", Rook(Color.BLACK))
    move = GreedyBot(seed=1).choose_move(empty_game)
    if move[1] in (pos("e8"), pos("d8")):  # пешка идёт на последний ряд
        assert move[2] is Queen


# ---------- жадный ----------

def test_greedy_takes_free_queen(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "a1", Rook(Color.WHITE))
    put(empty_game, "e8", King(Color.BLACK))
    put(empty_game, "a8", Queen(Color.BLACK))
    assert GreedyBot(seed=1).choose_move(empty_game) == (pos("a1"), pos("a8"), None)


def test_greedy_falls_for_protected_pawn(empty_game):
    blunder = queen_takes_protected_pawn(empty_game)
    assert GreedyBot(seed=1).choose_move(empty_game) == blunder  # ответа соперника он не видит


# ---------- продвинутый ----------

def test_minimax_does_not_hang_queen(empty_game):
    blunder = queen_takes_protected_pawn(empty_game)
    assert MinimaxBot(depth=2, seed=1).choose_move(empty_game) != blunder


def test_minimax_finds_mate_in_one(empty_game):
    mate = back_rank_mate(empty_game)
    assert MinimaxBot(depth=2, seed=1).choose_move(empty_game) == mate


def test_minimax_takes_free_queen(empty_game):
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "a1", Rook(Color.WHITE))
    put(empty_game, "e8", King(Color.BLACK))
    put(empty_game, "a8", Queen(Color.BLACK))
    assert MinimaxBot(depth=2, seed=1).choose_move(empty_game) == (pos("a1"), pos("a8"), None)


# ---------- вариативность ----------

def test_same_seed_gives_same_game():
    first = play_game(GreedyBot(seed=7), GreedyBot(seed=7), max_plies=10)
    second = play_game(GreedyBot(seed=7), GreedyBot(seed=7), max_plies=10)
    assert first.game.history_text() == second.game.history_text()


def test_different_seeds_give_different_games():
    games = {
        play_game(GreedyBot(seed=s), GreedyBot(seed=s), max_plies=8).game.history_text()
        for s in range(5)
    }
    assert len(games) > 1


def test_minimax_depth_4_finds_mate_in_one(empty_game):
    mate = back_rank_mate(empty_game)
    assert MinimaxBot(depth=4, seed=1).choose_move(empty_game) == mate


def test_minimax_depth_3_does_not_hang_queen(empty_game):
    blunder = queen_takes_protected_pawn(empty_game)
    assert MinimaxBot(depth=3, seed=1).choose_move(empty_game) != blunder


def test_minimax_depth_4_finds_mate_in_two(empty_game):
    """Две ладьи против голого короля: Ra7, Kg8 (единственный ход), Rb8#"""
    put(empty_game, "e1", King(Color.WHITE))
    put(empty_game, "a2", Rook(Color.WHITE))
    put(empty_game, "b3", Rook(Color.WHITE))
    put(empty_game, "h8", King(Color.BLACK))
    bot = MinimaxBot(depth=4, seed=1)
    empty_game.make_move(*bot.choose_move(empty_game))
    reply = sorted(empty_game.legal_moves(pos("h8")), key=lambda p: (p.row, p.col))[0]
    empty_game.make_move(pos("h8"), reply)  # что бы чёрные ни ответили
    empty_game.make_move(*bot.choose_move(empty_game))
    assert empty_game.status() == GameStatus.CHECKMATE
