"""Бенчмарк перебора. Запуск из папки chess:

    python -m bots.benchmark        # глубины 1..4
    python -m bots.benchmark 5      # до глубины 5

Для каждой глубины считаем один и тот же ход тремя способами и печатаем:
сколько позиций просмотрено, за сколько секунд и сколько позиций в секунду.
"""
import os
import sys
import time

from bots.minimax import MinimaxBot
from game import Game
from tools.position import Position

OPENING = [("e2", "e4"), ("e7", "e5"), ("g1", "f3"), ("b8", "c6"), ("f1", "c4"), ("g8", "f6")]
# сложнее: после размена ферзей (чёрные ходят, ферзь d5 под боем)
TACTICS = [("e2", "e4"), ("d7", "d5"), ("e4", "d5"), ("d8", "d5"), ("b1", "c3")]


def make_game(moves) -> Game:
    game = Game()
    for source, destination in moves:
        game.make_move(Position.from_str(source), Position.from_str(destination))
    return game


def run(label: str, bot: MinimaxBot, game: Game) -> None:
    started = time.perf_counter()
    bot.choose_move(game)
    elapsed = time.perf_counter() - started
    speed = bot.nodes / elapsed if elapsed else 0
    print(f"  {label:<26} позиций: {bot.nodes:>10}   время: {elapsed:7.2f} с   {speed:>10,.0f} поз/с")


def main() -> None:
    max_depth = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    cores = os.cpu_count() or 1

    # прогрев: поднимаем процессы заранее, чтобы их запуск не попал в замер
    MinimaxBot(depth=1, workers=cores).choose_move(make_game(OPENING))

    for title, moves in (("дебют", OPENING), ("тактика", TACTICS)):
        for depth in range(1, max_depth + 1):
            print(f"{title}, глубина {depth}")
            run("без таблицы", MinimaxBot(depth, seed=1, use_tt=False), make_game(moves))
            run("с таблицей", MinimaxBot(depth, seed=1), make_game(moves))
            run(f"с таблицей, {cores} проц.", MinimaxBot(depth, seed=1, workers=cores), make_game(moves))


if __name__ == "__main__":      # без этой проверки процессы-рабочие (spawn) запустят всё заново
    main()