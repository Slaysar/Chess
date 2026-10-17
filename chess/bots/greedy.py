from bots.base import Bot
from bots.common import all_moves, evaluate, try_move, undo_move


class GreedyBot(Bot):
    name = "greedy"

    def choose_move(self, game):
        me = game.turn
        scored = []
        for source, destination in all_moves(game, me):
            saved = try_move(game.board, source, destination)
            scored.append((evaluate(game.board, me), (source, destination)))
            undo_move(game.board, source, destination, saved)

        source, destination = self.pick_best(scored, game.board)
        return self.finish_move(game, source, destination)