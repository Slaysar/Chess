from bots.base import Bot
from bots.common import MATE, VALUES, all_moves, evaluate, pseudo_moves, try_move, undo_move
from pieces.king import King

INF = 10 ** 9
VICTIMS = {**VALUES, "K": 100}     # для порядка перебора: бить короля важнее всего


def mate_score(turn, me, depth) -> int:
    """Игроку turn поставлен мат. Чем больше осталось глубины, тем раньше мат и тем он важнее"""
    score = MATE + depth
    return -score if turn is me else score


class MinimaxBot(Bot):
    """Перебирает ходы на depth полуходов вперёд.
    Свои ходы выбирает с максимальной оценкой, ходы соперника с минимальной.
    Ускорение: отсечение (alpha-beta), взятия смотрим первыми, шах внутри перебора не проверяем."""
    name = "advanced"

    def __init__(self, depth: int = 2, seed: int | None = None):
        super().__init__(seed)
        self.depth = depth

    def choose_move(self, game):
        me = game.turn
        board = game.board
        scored = []
        best = -INF
        # первый ход выбираем только из настоящих легальных ходов
        for source, destination in self.ordered(board, all_moves(game, me)):
            saved = try_move(board, source, destination)
            # окно на 1 шире лучшего: равные лучшему ходы получают точную оценку, и выбор между ними случаен
            alpha = best - 1 if scored else -INF
            score = self.search(board, self.depth - 1, me.opposite, me, alpha, INF)
            undo_move(board, source, destination, saved)
            if score is None:
                continue
            scored.append((score, (source, destination)))
            best = max(best, score)

        source, destination = self.pick_best(scored)
        return self.finish_move(game, source, destination)

    def search(self, board, depth, turn, me, alpha, beta):
        """Оценка позиции для me. Ходит turn, осталось depth полуходов.
        alpha: что я уже гарантированно имею, beta: что гарантированно имеет соперник.
        Возвращает None, если позиция невозможна: предыдущий ход оставил короля под шахом."""
        if depth == 0:
            if board.is_in_check(turn.opposite):
                return None
            return evaluate(board, me)

        maximizing = turn is me
        best = -INF if maximizing else INF
        has_legal_move = False

        for source, destination in self.ordered(board, pseudo_moves(board, turn)):
            if isinstance(board.get(destination), King):
                return None            # можем взять короля: предыдущий ход был невозможен

            saved = try_move(board, source, destination)
            score = self.search(board, depth - 1, turn.opposite, me, alpha, beta)
            undo_move(board, source, destination, saved)

            if score is None:          # этот ход оставил моего короля под шахом: он нелегальный
                continue
            has_legal_move = True

            if maximizing:
                best = max(best, score)
                alpha = max(alpha, best)
            else:
                best = min(best, score)
                beta = min(beta, best)
            if beta <= alpha:          # дальше смотреть незачем: эту ветку противник не допустит
                break

        if not has_legal_move:         # ходов нет: мат или пат
            if board.is_in_check(turn):
                return mate_score(turn, me, depth)
            return 0
        return best

    @staticmethod
    def ordered(board, moves):
        """Взятия вперёд, самые дорогие жертвы первыми: от этого отсечений больше"""
        def victim_value(move):
            victim = board.get(move[1])
            return 0 if victim is None else VICTIMS[victim.SYMBOL]
        return sorted(moves, key=victim_value, reverse=True)