"""Бенчмарк перебора. Запуск из папки chess:

    python -m bots.benchmark        # глубины 1..4
    python -m bots.benchmark 5      # до глубины 5

Для каждой глубины считаем один и тот же ход тремя способами и печатаем:
сколько позиций просмотрено, за сколько секунд и сколько позиций в секунду.
(Старый bots/timing.py можно удалить: это его замена.)
"""
import os
import sys
import time

from bots.minimax import MinimaxBot
from game import Game
from tools.position import Position

# Две позиции для замера, заданные списком ходов от начала партии.
# Дебют: обычная позиция, ходят белые.
OPENING = [("e2", "e4"), ("e7", "e5"), ("g1", "f3"), ("b8", "c6"), ("f1", "c4"), ("g8", "f6")]
# Тактика: чёрный ферзь под боем коня, оценки ходов заметно различаются, дерево разнообразнее.
TACTICS = [("e2", "e4"), ("d7", "d5"), ("e4", "d5"), ("d8", "d5"), ("b1", "c3")]


def make_game(moves) -> Game:
    """Новая партия с проигранными ходами. Каждый замер получает свежую партию,
    поэтому режимы не влияют друг на друга."""
    game = Game()
    for source, destination in moves:
        game.make_move(Position.from_str(source), Position.from_str(destination))
    return game


def run(label: str, bot: MinimaxBot, game: Game) -> None:
    started = time.perf_counter()                        # perf_counter — самый точный таймер для коротких интервалов
    bot.choose_move(game)                                # замеряем только выбор хода
    elapsed = time.perf_counter() - started
    speed = bot.nodes / elapsed if elapsed else 0        # позиций в секунду (защита от деления на ноль)
    # форматирование выравнивает столбцы: :<26 — по левому краю, :>10 — по правому,
    # :7.2f — два знака после запятой, :>10,.0f — целое с разделителем тысяч
    print(f"  {label:<26} позиций: {bot.nodes:>10}   время: {elapsed:7.2f} с   {speed:>10,.0f} поз/с")


def main() -> None:
    max_depth = int(sys.argv[1]) if len(sys.argv) > 1 else 4   # максимальная глубина из командной строки
    cores = os.cpu_count() or 1                                # число ядер (если не определилось — 1)

    # прогрев: поднимаем процессы пула заранее, чтобы их запуск не попал в замер
    MinimaxBot(depth=1, workers=cores).choose_move(make_game(OPENING))

    for title, moves in (("дебют", OPENING), ("тактика", TACTICS)):
        for depth in range(1, max_depth + 1):
            print(f"{title}, глубина {depth}")
            # три режима, одинаковое зерно (seed=1) — одинаковые условия выбора среди равных ходов
            run("без таблицы", MinimaxBot(depth, seed=1, use_tt=False), make_game(moves))
            run("с таблицей", MinimaxBot(depth, seed=1), make_game(moves))
            run(f"с таблицей, {cores} проц.", MinimaxBot(depth, seed=1, workers=cores), make_game(moves))


if __name__ == "__main__":      # без этой проверки процессы-рабочие (spawn на Windows) запустят всё заново
    main()
