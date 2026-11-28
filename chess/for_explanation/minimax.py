from __future__ import annotations
import random                                      # для генерации случайных чисел Zobrist-хеша
from concurrent.futures import ProcessPoolExecutor  # пул процессов для параллельного поиска

from bots.base import Bot                          # базовый бот: pick_best (выбор среди равных) и finish_move
from bots.common import MATE, VALUES, all_moves, evaluate, pseudo_moves, try_move, undo_move
from pieces.king import King                       # нужен, чтобы распознать «ход берёт короля» (= позиция нелегальна)
from tools.color import Color                      # цвет участвует в хеше позиции

INF = 10 ** 9                                      # «бесконечность»: больше любой оценки (мат ≈ 1000)
VICTIMS = {**VALUES, "K": 100}                     # ценность «жертвы» для сортировки ходов; король = 100,
                                                   # чтобы ход со взятием короля обрабатывался первым

# ======================= ТАБЛИЦА ТРАНСПОЗИЦИЙ =======================
# Одна и та же позиция часто получается разным порядком ходов. Результат поиска запоминаем
# по хешу позиции (Zobrist) и второй раз ту же позицию не считаем.

# Что именно записано в таблице про позицию:
#   EXACT   — точная оценка;
#   LOWER   — настоящая оценка НЕ МЕНЬШЕ записанной (был beta-отсечение);
#   UPPER   — настоящая оценка НЕ БОЛЬШЕ записанной (ничего лучше alpha не нашли);
#   ILLEGAL — позиция нелегальна (предыдущий ход оставил своего короля под боем).
EXACT, LOWER, UPPER, ILLEGAL = range(4)            # просто четыре числа 0..3
TT_LIMIT = 500_000                                 # когда записей столько, таблицу целиком очищаем (чтобы не съесть память)

_rng = random.Random(12345)                        # свой генератор с фиксированным зерном: во всех процессах числа одинаковые
# ZOBRIST[фигура][цвет][клетка] — случайное 64-битное число для пары «фигура на клетке»:
# по 6 фигур, по 2 цвета, по 64 клетки
ZOBRIST = {
    symbol: [[_rng.getrandbits(64) for _ in range(64)] for _ in range(2)]
    for symbol in "PNBRQK"
}
SIDE_KEY = _rng.getrandbits(64)                    # подмешивается, когда ходят чёрные (очередь хода — часть позиции)
ME_KEY = _rng.getrandbits(64)                      # подмешивается, когда бот играет чёрными: оценки считаются «с его стороны»


def piece_key(piece, pos) -> int:
    # число для «эта фигура стоит на этой клетке».
    # `piece.color is Color.BLACK` даёт True/False — Python использует их как индексы 1/0
    return ZOBRIST[piece.SYMBOL][piece.color is Color.BLACK][pos.row * 8 + pos.col]


def board_key(board, turn, me) -> int:
    """Полный хеш позиции. Считается ОДИН раз на корне, дальше хеш обновляется на каждом ходе
    только по изменившимся клеткам (см. child_key)."""
    key = 0
    for color in (Color.WHITE, Color.BLACK):
        for pos, piece in board.pieces_of(color):
            key ^= piece_key(piece, pos)           # XOR чисел всех фигур; XOR обратим — на этом держится обновление
    if turn is Color.BLACK:
        key ^= SIDE_KEY                            # ходят чёрные
    if me is Color.BLACK:
        key ^= ME_KEY                              # бот играет чёрными
    return key


def move_code(source, destination) -> int:
    """Ход одним числом (откуда * 64 + куда). Так лучший ход хранится в таблице
    обычным числом, и его легко сравнивать с ходами из списка."""
    return source.row * 512 + source.col * 64 + destination.row * 8 + destination.col


def mate_score(turn, me, depth) -> int:
    # чем больше глубины осталось в момент мата, тем раньше он наступил, поэтому ценится выше:
    # бот выбирает самый быстрый мат и оттягивает собственный
    score = MATE + depth
    # если мат поставили ходящему игроку-боту — это проигрыш (минус), иначе победа (плюс)
    return -score if turn is me else score


class MinimaxBot(Bot):
    name = "advanced"

    def __init__(self, depth: int = 2, seed: int | None = None,
                 use_tt: bool = True, workers: int = 1):
        super().__init__(seed)
        self.depth = depth            # на сколько полуходов вперёд считаем
        self.use_tt = use_tt          # выключатель таблицы (нужен только чтобы бенчмарк мог сравнить «с» и «без»)
        self.workers = workers        # больше 1 -> корневые ходы считаются в разных процессах
        self.tt: dict[int, tuple] = {}  # таблица транспозиций: хеш -> (глубина, тип, оценка, лучший ход).
                                        # Живёт вместе с ботом, между ходами одной партии не сбрасывается:
                                        # запись не зависит от того, как мы в позицию пришли
        self.nodes = 0                # сколько позиций просмотрено за последний choose_move (для бенчмарка)
        self.last_scored = []         # [(оценка, (откуда, куда))] последнего choose_move (для тестов)

    def choose_move(self, game):
        me = game.turn                # за кого играем: оценки считаются с точки зрения этого цвета
        board = game.board
        self.nodes = 0                # счётчик обнуляется на каждый новый выбор хода
        # все легальные ходы; ordered ставит перспективные (взятия самых ценных фигур) впереди
        moves = self.ordered(board, all_moves(game, me))
        if self.workers > 1 and len(moves) > 1:
            scored = self.score_parallel(board, moves, me)     # корневые ходы раздаём процессам
        else:
            scored = self.score_sequential(board, moves, me)   # считаем по очереди в этом процессе
        self.last_scored = scored

        # дальше как раньше: pick_best выбирает лучший ход (среди равных — более центральный,
        # потом случайный), finish_move дописывает превращение в ферзя
        source, destination = self.pick_best(scored, board)
        return self.finish_move(game, source, destination)

    # ---------- корень дерева ----------

    def score_sequential(self, board, moves, me):
        scored = []
        best = -INF                                    # лучшая оценка среди уже просмотренных корневых ходов
        key = board_key(board, me, me)                 # хеш корневой позиции — один раз
        for source, destination in moves:
            # Для первого хода окно полное. Для остальных alpha = best - 1: нам нужны только ходы
            # НЕ ХУЖЕ лучшего найденного (из равных потом выбирается случайный).
            # Ходы хуже best отсекаются быстро, а ходы с оценкой ровно best получаются точными,
            # потому что best - 1 < best.
            alpha = best - 1 if scored else -INF
            score = self.score_move(board, key, source, destination, me, alpha)
            if score is None:                          # None — ход оказался нелегальным с точки зрения перебора
                continue
            scored.append((score, (source, destination)))
            best = max(best, score)
        return scored

    def score_parallel(self, board, moves, me):
        """Первый (самый перспективный) ход считаем сами, чтобы получить хорошую границу alpha,
        остальные раздаём процессам. Границу они не обновляют (процессы не общаются),
        поэтому отсечений чуть меньше, чем в последовательной версии,
        зато считают на всех ядрах."""
        key = board_key(board, me, me)
        scored = []
        rest = list(moves)                             # ходы, которые ещё не оценены
        best = -INF
        # считаем в этом процессе ходы по одному, пока не получим первую настоящую оценку
        # (первый ход может вернуть None — тогда берём следующий)
        while rest and not scored:
            source, destination = rest.pop(0)
            score = self.score_move(board, key, source, destination, me, -INF)
            if score is not None:
                scored.append((score, (source, destination)))
                best = score

        pool = get_pool(self.workers)                  # общий пул процессов (создаётся при первом обращении)
        # одна задача на каждый оставшийся ход; параметры (в том числе копия доски) уходят в процесс через pickle
        tasks = [(board, source, destination, me, self.depth, best - 1, self.use_tt)
                 for source, destination in rest]
        # pool.map раздаёт задачи свободным процессам; результаты приходят в том же порядке,
        # поэтому zip сопоставляет их с исходными ходами
        for (source, destination), (score, nodes) in zip(rest, pool.map(_root_task, tasks)):
            self.nodes += nodes                        # прибавляем узлы, посчитанные в процессе
            if score is not None:
                scored.append((score, (source, destination)))
        return scored

    def score_move(self, board, key, source, destination, me, alpha):
        """Оценить один корневой ход (общий кусок для последовательной и параллельной версий)"""
        # хеш позиции ПОСЛЕ хода; считаем до того, как ход сделан на доске
        child_key = self.child_key(board, key, source, destination)
        saved = try_move(board, source, destination)   # делаем ход на доске
        # оцениваем позицию: глубина на единицу меньше, ходит соперник, окно (alpha, INF)
        score = self.search(board, self.depth - 1, me.opposite, me, alpha, INF, child_key)
        undo_move(board, source, destination, saved)   # возвращаем доску как было
        return score

    # ---------- сам перебор ----------

    @staticmethod
    def child_key(board, key, source, destination) -> int:
        """Хеш позиции после хода без пересчёта всей доски: меняем только затронутые клетки"""
        piece = board.get(source)                      # кто ходит
        # убираем фигуру с исходной клетки, ставим на новую (XOR обратим), переключаем очередь хода
        key ^= piece_key(piece, source) ^ piece_key(piece, destination) ^ SIDE_KEY
        victim = board.get(destination)                # кого съели (если кого-то)
        if victim is not None:
            key ^= piece_key(victim, destination)      # снимаем съеденную фигуру
        return key

    def search(self, board, depth, turn, me, alpha, beta, key):
        """Минимакс с alpha-beta и таблицей транспозиций.
        depth — сколько полуходов осталось; turn — чей ход в этой позиции; me — за кого играет бот;
        [alpha, beta] — окно поиска; key — хеш позиции.
        Возвращает оценку с точки зрения me или None, если позиция нелегальна."""
        self.nodes += 1                                # каждая просмотренная позиция (включая листья) считается
        if depth == 0:                                 # конец перебора
            if board.is_in_check(turn.opposite):       # тот, кто только что сходил, оставил своего короля под боем,
                return None                            # значит позиция нелегальна
            return evaluate(board, me)                 # иначе просто материал

        # --- смотрим в таблицу ---
        hint = None                                    # лучший ход из таблицы (подсказка для сортировки)
        if self.use_tt:
            entry = self.tt.get(key)
            if entry is not None:
                stored_depth, flag, value, hint = entry
                if flag == ILLEGAL:                    # нелегальность не зависит от глубины
                    return None
                # оценкой пользуемся только при ТОЙ ЖЕ глубине: оценки мата зависят от оставшейся глубины
                if stored_depth == depth:
                    if flag == EXACT:
                        return value                   # точная оценка — считать не нужно
                    if flag == LOWER and value >= beta:
                        return value                   # настоящая оценка не меньше value, а это уже >= beta: отсечение
                    if flag == UPPER and value <= alpha:
                        return value                   # настоящая оценка не больше value, а это <= alpha: отсечение

        maximizing = turn is me                        # ходит бот — максимизируем, ходит соперник — минимизируем
        best = -INF if maximizing else INF             # стартуем с заведомо худшего значения
        best_move = None                               # ход, давший best (запишем в таблицу)
        has_legal_move = False                         # был ли хоть один легальный ход (иначе мат или пат)
        orig_alpha, orig_beta = alpha, beta            # исходное окно: нужно в конце, чтобы определить тип записи
                                                       # (alpha и beta внутри цикла меняются)

        # перебираем ПСЕВДОходы (без проверки шаха), отсортированные: ход из таблицы первым,
        # потом взятия по убыванию ценности жертвы
        for source, destination in self.ordered(board, pseudo_moves(board, turn), hint):
            # король получает самую большую ценность жертвы, поэтому ход со взятием короля идёт первым.
            # Если такой ход есть, предыдущая сторона оставила короля под боем: позиция нелегальна.
            if isinstance(board.get(destination), King):
                if self.use_tt:
                    self.tt[key] = (depth, ILLEGAL, 0, None)  # запоминаем нелегальность
                return None

            child_key = self.child_key(board, key, source, destination)  # хеш потомка (до хода на доске)
            saved = try_move(board, source, destination)                 # ход на доске
            score = self.search(board, depth - 1, turn.opposite, me, alpha, beta, child_key)  # рекурсия
            undo_move(board, source, destination, saved)                 # откат

            if score is None:                          # этот ход нелегален (оставил своего короля под боем)
                continue
            has_legal_move = True

            if maximizing:
                if score > best:
                    best, best_move = score, move_code(source, destination)  # запоминаем лучший ход
                alpha = max(alpha, best)               # максимизирующий игрок поднимает нижнюю границу
            else:
                if score < best:
                    best, best_move = score, move_code(source, destination)
                beta = min(beta, best)                 # минимизирующий игрок опускает верхнюю границу
            if beta <= alpha:                          # эта ветка уже не повлияет на результат выше: отсечение
                break

        # --- итог по позиции ---
        if not has_legal_move:
            # нет легальных ходов: если король под шахом — мат, иначе пат (ноль); оценка точная
            score = mate_score(turn, me, depth) if board.is_in_check(turn) else 0
            flag = EXACT
        else:
            score = best
            # тип записи зависит от того, как итог соотносится с ИСХОДНЫМ окном
            if best <= orig_alpha:
                flag = UPPER      # ничего лучше alpha не нашли: настоящая оценка не больше
            elif best >= orig_beta:
                flag = LOWER      # было отсечение: настоящая оценка не меньше
            else:
                flag = EXACT      # оценка внутри окна: точная

        if self.use_tt:
            if len(self.tt) >= TT_LIMIT:
                self.tt.clear()                        # таблица разрослась: просто очищаем целиком
            self.tt[key] = (depth, flag, score, best_move)  # запоминаем результат
        return score

    @staticmethod
    def ordered(board, moves, hint=None):
        """Порядок ходов сильно влияет на число отсечений: сначала нужно проверять лучшие.
        Первым идёт ход из таблицы, потом взятия по убыванию ценности взятой фигуры."""
        def priority(move):
            source, destination = move
            # ходы сравниваем по числовому коду, а не по объектам Position
            if hint is not None and move_code(source, destination) == hint:
                return 1000                            # ход из таблицы: выше любого взятия (макс. 100)
            victim = board.get(destination)
            return 0 if victim is None else VICTIMS[victim.SYMBOL]
        # sorted стабилен: ходы с одинаковым приоритетом остаются в исходном порядке (результат детерминирован)
        return sorted(moves, key=priority, reverse=True)


# ======================= НЕСКОЛЬКО ПРОЦЕССОВ =======================
# Потоки в Python не ускоряют вычисления (GIL), поэтому нужны именно процессы.
# Пул один на всё приложение, чтобы партии не плодили свои процессы.

_pool: ProcessPoolExecutor | None = None                 # общий пул (создаётся лениво)
_worker_bots: dict[tuple[int, bool], MinimaxBot] = {}    # используется только ВНУТРИ процессов-рабочих


def get_pool(workers: int) -> ProcessPoolExecutor:
    global _pool                                          # функция меняет переменную уровня модуля
    if _pool is None:
        _pool = ProcessPoolExecutor(max_workers=workers)  # размер берётся из первого вызова
    return _pool


def _root_task(args):
    """Задача для процесса-рабочего: оценить один корневой ход.
    Функция обязана лежать на верхнем уровне модуля, иначе её нельзя передать между процессами.
    Доска пришла копией, поэтому ход на ней можно делать свободно (score_move всё равно откатывает).
    Бот живёт между задачами, поэтому его таблица транспозиций копится."""
    board, source, destination, me, depth, alpha, use_tt = args
    bot = _worker_bots.get((depth, use_tt))               # один бот на пару «глубина, таблица включена»
    if bot is None:
        bot = _worker_bots[(depth, use_tt)] = MinimaxBot(depth=depth, use_tt=use_tt)
    bot.nodes = 0                                         # считаем узлы только этой задачи
    key = board_key(board, me, me)                        # хеш корня считаем заново: доска в этом процессе своя
    score = bot.score_move(board, key, source, destination, me, alpha)
    return score, bot.nodes                               # основной процесс просуммирует числа узлов
