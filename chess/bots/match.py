from __future__ import annotations
from dataclasses import dataclass

from game import Game
from tools.color import Color
from tools.game_status import GameStatus
from bots.base import Bot
from bots.common import VALUES


@dataclass
class MatchResult:
    game: Game
    winner: Color | None
    reason: str


def material(game: Game, color: Color) -> int:
    return sum(VALUES[piece.SYMBOL] for _, piece in game.board.pieces_of(color))


def play_game(white: Bot, black: Bot, max_plies: int = 60, margin: int = 2) -> MatchResult:
    game = Game()
    bots = {Color.WHITE: white, Color.BLACK: black}
    while True:
        print(game.board)
        status = game.status()
        if status is GameStatus.CHECKMATE:
            return MatchResult(game, game.turn.opposite, "мат")
        if status in (GameStatus.STALEMATE, GameStatus.DRAW):
            return MatchResult(game, None, "пат или ничья")
        if len(game.history) >= max_plies:
            break
        game.make_move(*bots[game.turn].choose_move(game))

    diff = material(game, Color.WHITE) - material(game, Color.BLACK)
    if diff >= margin:
        return MatchResult(game, Color.WHITE, "по материалу")
    if diff <= -margin:
        return MatchResult(game, Color.BLACK, "по материалу")
    return MatchResult(game, None, "ничья по материалу")


if __name__ == "__main__":
    from bots.greedy import GreedyBot
    from bots.minimax import MinimaxBot

    for number, advanced_is_white in enumerate((True, False), start=1):
        advanced, greedy = MinimaxBot(depth=4), GreedyBot()
        white, black = (advanced, greedy) if advanced_is_white else (greedy, advanced)
        result = play_game(white, black)
        if result.winner is None:
            winner = "ничья"
        else:
            winner = "продвинутый" if (result.winner is Color.WHITE) == advanced_is_white else "жадный"
        print(f"Партия {number}: {winner} ({result.reason})")
        print(result.game.history_text())