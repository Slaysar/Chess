import pytest

from bots.greedy import GreedyBot
from bots.minimax import MinimaxBot
from game import Game
from tools.color import Color
from tools.game_status import GameStatus
from tests.helpers import pos

# чёрные ходят, ферзь d5 под боем коня c3: оценки ходов заметно различаются
TACTICS = [("e2", "e4"), ("d7", "d5"), ("e4", "d5"), ("d8", "d5"), ("b1", "c3")]


def tactics_game() -> Game:
    game = Game()
    for source, destination in TACTICS:
        game.make_move(pos(source), pos(destination))
    return game


def naive_in_check(board, color) -> bool:
    """Старый способ: строим все ходы соперника и смотрим, есть ли среди них взятие короля"""
    king = board.find_king(color)
    return any(king in piece.get_possible_moves(board, square)
               for square, piece in board.pieces_of(color.opposite))


def test_is_in_check_matches_naive_version():
    game = Game()
    bot = GreedyBot(seed=3)
    for _ in range(60):
        for color in (Color.WHITE, Color.BLACK):
            assert game.board.is_in_check(color) == naive_in_check(game.board, color)
        if game.status() in (GameStatus.CHECKMATE, GameStatus.STALEMATE, GameStatus.DRAW):
            break
        game.make_move(*bot.choose_move(game))


def best_score(bot: MinimaxBot, game: Game) -> int:
    bot.choose_move(game)
    return max(score for score, _ in bot.last_scored)


def test_transposition_table_does_not_change_best_score():
    plain = best_score(MinimaxBot(depth=3, seed=1, use_tt=False), tactics_game())
    cached = best_score(MinimaxBot(depth=3, seed=1, use_tt=True), tactics_game())
    assert plain == cached


def test_table_survives_between_moves():
    bot = MinimaxBot(depth=2, seed=1)
    game = tactics_game()
    first = best_score(bot, game)
    assert bot.tt                       # что-то запомнили
    assert best_score(bot, game) == first   # со «старой» таблицей та же оценка


def test_nodes_are_counted():
    bot = MinimaxBot(depth=2, seed=1)
    bot.choose_move(Game())
    assert bot.nodes > 0


@pytest.mark.slow
def test_parallel_search_gives_same_best_score():
    sequential = best_score(MinimaxBot(depth=2, seed=1), tactics_game())
    parallel = best_score(MinimaxBot(depth=2, seed=1, workers=2), tactics_game())
    assert sequential == parallel