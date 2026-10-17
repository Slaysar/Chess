import pytest

from bots.greedy import GreedyBot
from bots.match import play_game
from bots.minimax import MinimaxBot
from tools.color import Color


@pytest.mark.slow
def test_advanced_beats_greedy():
    advanced_points = greedy_points = 0.0
    # одна партия белыми, одна чёрными, чтобы цвет не влиял
    for seed, advanced_color in ((1, Color.WHITE), (2, Color.BLACK)):
        advanced, greedy = MinimaxBot(depth=2, seed=seed), GreedyBot(seed=seed)
        white, black = (advanced, greedy) if advanced_color is Color.WHITE else (greedy, advanced)
        result = play_game(white, black, max_plies=60)
        if result.winner is None:
            advanced_points += 0.5
            greedy_points += 0.5
        elif result.winner is advanced_color:
            advanced_points += 1
        else:
            greedy_points += 1
    assert advanced_points > greedy_points