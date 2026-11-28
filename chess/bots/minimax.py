from __future__ import annotations
import random
from concurrent.futures import ProcessPoolExecutor

from bots.base import Bot
from bots.common import MATE, VALUES, all_moves, evaluate, pseudo_moves, try_move, undo_move
from pieces.king import King
from tools.color import Color

INF = 10 ** 9
VICTIMS = {**VALUES, "K": 100}

# ---------- таблица транспозиций ----------
# Одна и та же позиция часто получается разным порядком ходов. Результат поиска запоминаем
# по хешу позиции и второй раз не считаем.
EXACT, LOWER, UPPER, ILLEGAL = range(4)   # что именно мы знаем про оценку
TT_LIMIT = 500_000                        # столько записей держим, потом таблицу сбрасываем

_rng = random.Random(12345)               # фиксированное зерно: хеши одинаковы во всех процессах
ZOBRIST = {
    symbol: [[_rng.getrandbits(64) for _ in range(64)] for _ in range(2)]
    for symbol in "PNBRQK"
}
SIDE_KEY = _rng.getrandbits(64)           # «ходят чёрные»
ME_KEY = _rng.getrandbits(64)             # «бот играет чёрными» (оценки считаются с его стороны)


def piece_key(piece, pos) -> int:
    return ZOBRIST[piece.SYMBOL][piece.color is Color.BLACK][pos.row * 8 + pos.col]


def board_key(board, turn, me) -> int:
    """Хеш позиции целиком; потом он обновляется на каждом ходе только по изменившимся клеткам"""
    key = 0
    for color in (Color.WHITE, Color.BLACK):
        for pos, piece in board.pieces_of(color):
            key ^= piece_key(piece, pos)
    if turn is Color.BLACK:
        key ^= SIDE_KEY
    if me is Color.BLACK:
        key ^= ME_KEY
    return key


def move_code(source, destination) -> int:
    """Ход одним числом: так проще сравнивать ход из таблицы с ходами в списке"""
    return source.row * 512 + source.col * 64 + destination.row * 8 + destination.col


def mate_score(turn, me, depth) -> int:
    score = MATE + depth
    return -score if turn is me else score


class MinimaxBot(Bot):
    name = "advanced"

    def __init__(self, depth: int = 2, seed: int | None = None,
                 use_tt: bool = True, workers: int = 1):
        super().__init__(seed)
        self.depth = depth
        self.use_tt = use_tt          # можно выключить, чтобы сравнить в бенчмарке
        self.workers = workers        # больше 1 -> корневые ходы считаются в разных процессах
        self.tt: dict[int, tuple] = {}
        self.nodes = 0                # сколько позиций просмотрено за последний choose_move
        self.last_scored = []         # [(оценка, (откуда, куда))] последнего choose_move

    def choose_move(self, game):
        me = game.turn
        board = game.board
        self.nodes = 0
        moves = self.ordered(board, all_moves(game, me))
        if self.workers > 1 and len(moves) > 1:
            scored = self.score_parallel(board, moves, me)
        else:
            scored = self.score_sequential(board, moves, me)
        self.last_scored = scored

        source, destination = self.pick_best(scored, board)
        return self.finish_move(game, source, destination)

    # ---------- корень дерева ----------

    def score_sequential(self, board, moves, me):
        scored = []
        best = -INF
        key = board_key(board, me, me)
        for source, destination in moves:
            alpha = best - 1 if scored else -INF
            score = self.score_move(board, key, source, destination, me, alpha)
            if score is None:
                continue
            scored.append((score, (source, destination)))
            best = max(best, score)
        return scored

    def score_parallel(self, board, moves, me):
        key = board_key(board, me, me)
        scored = []
        rest = list(moves)
        best = -INF
        while rest and not scored:
            source, destination = rest.pop(0)
            score = self.score_move(board, key, source, destination, me, -INF)
            if score is not None:
                scored.append((score, (source, destination)))
                best = score

        pool = get_pool(self.workers)

        tasks = [(board, source, destination, me, self.depth, best - 1, self.use_tt)
                 for source, destination in rest]

        for (source, destination), (score, nodes) in zip(rest, pool.map(_root_task, tasks)):
            self.nodes += nodes
            if score is not None:
                scored.append((score, (source, destination)))

        return scored

    def score_move(self, board, key, source, destination, me, alpha):
        child_key = self.child_key(board, key, source, destination)
        saved = try_move(board, source, destination)
        score = self.search(board, self.depth - 1, me.opposite, me, alpha, INF, child_key)
        undo_move(board, source, destination, saved)
        return score

    # ---------- сам перебор ----------

    @staticmethod
    def child_key(board, key, source, destination) -> int:
        """Хеш позиции после хода: убрали фигуру с source, поставили на destination, сняли взятую"""
        piece = board.get(source)
        key ^= piece_key(piece, source) ^ piece_key(piece, destination) ^ SIDE_KEY
        victim = board.get(destination)
        if victim is not None:
            key ^= piece_key(victim, destination)
        return key

    def search(self, board, depth, turn, me, alpha, beta, key):
        self.nodes += 1
        if depth == 0:
            if board.is_in_check(turn.opposite):
                return None
            return evaluate(board, me)

        hint = None
        if self.use_tt:
            entry = self.tt.get(key)
            if entry is not None:
                stored_depth, flag, value, hint = entry
                if flag == ILLEGAL:
                    return None
                # берём только запись той же глубины: оценки мата зависят от оставшейся глубины
                if stored_depth == depth:
                    if flag == EXACT:
                        return value
                    if flag == LOWER and value >= beta:
                        return value
                    if flag == UPPER and value <= alpha:
                        return value

        maximizing = turn is me
        best = -INF if maximizing else INF
        best_move = None
        has_legal_move = False
        orig_alpha, orig_beta = alpha, beta

        for source, destination in self.ordered(board, pseudo_moves(board, turn), hint):
            if isinstance(board.get(destination), King):
                if self.use_tt:
                    self.tt[key] = (depth, ILLEGAL, 0, None)  # предыдущий ход оставил короля под боем
                return None

            child_key = self.child_key(board, key, source, destination)
            saved = try_move(board, source, destination)
            score = self.search(board, depth - 1, turn.opposite, me, alpha, beta, child_key)
            undo_move(board, source, destination, saved)

            if score is None:
                continue
            has_legal_move = True

            if maximizing:
                if score > best:
                    best, best_move = score, move_code(source, destination)
                alpha = max(alpha, best)
            else:
                if score < best:
                    best, best_move = score, move_code(source, destination)
                beta = min(beta, best)
            if beta <= alpha:
                break

        if not has_legal_move:
            score = mate_score(turn, me, depth) if board.is_in_check(turn) else 0
            flag = EXACT
        else:
            score = best
            if best <= orig_alpha:
                flag = UPPER      # ничего лучше alpha не нашли: настоящая оценка не больше
            elif best >= orig_beta:
                flag = LOWER      # отсечение: настоящая оценка не меньше
            else:
                flag = EXACT

        if self.use_tt:
            if len(self.tt) >= TT_LIMIT:
                self.tt.clear()
            self.tt[key] = (depth, flag, score, best_move)
        return score

    @staticmethod
    def ordered(board, moves, hint=None):
        """Сначала ход из таблицы (лучший в прошлый раз), потом взятия самых ценных фигур"""
        def priority(move):
            source, destination = move
            if hint is not None and move_code(source, destination) == hint:
                return 1000
            victim = board.get(destination)
            return 0 if victim is None else VICTIMS[victim.SYMBOL]
        return sorted(moves, key=priority, reverse=True)


_pool: ProcessPoolExecutor | None = None
_worker_bots: dict[tuple[int, bool], MinimaxBot] = {}


def get_pool(workers: int) -> ProcessPoolExecutor:
    global _pool
    if _pool is None:
        _pool = ProcessPoolExecutor(max_workers=workers)
    return _pool


def _root_task(args):
    board, source, destination, me, depth, alpha, use_tt = args
    bot = _worker_bots.get((depth, use_tt))
    if bot is None:
        bot = _worker_bots[(depth, use_tt)] = MinimaxBot(depth=depth, use_tt=use_tt)
    bot.nodes = 0
    key = board_key(board, me, me)
    score = bot.score_move(board, key, source, destination, me, alpha)
    return score, bot.nodes