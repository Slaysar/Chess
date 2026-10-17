import time

from game import Game
from tools.position import Position
from bots.minimax import MinimaxBot

game = Game()
for source, destination in [("e2", "e4"), ("e7", "e5"), ("g1", "f3"), ("b8", "c6"), ("f1", "c4"), ("g8", "f6")]:
    game.make_move(Position.from_str(source), Position.from_str(destination))

for depth in (1, 2, 3, 4):
    started = time.perf_counter()
    MinimaxBot(depth=depth, seed=1).choose_move(game)
    print(f"depth {depth}: {time.perf_counter() - started:.2f} с")