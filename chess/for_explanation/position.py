from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)  # frozen: объект неизменяем, значит его можно хешировать и класть в словарь/множество
class Position:
    SIZE = 8                # без аннотации типа: это атрибут КЛАССА, а не поле dataclass
    CHARS = "abcdefgh"      # буквы вертикалей

    row: int                # 0..7 с аннотацией это атрибут экземпляра
    col: int                # 0..7 с аннотацией это атрибут экземпляра

    def __post_init__(self): # после __init__, ну по названию можно догадаться
        # проверяем, что клетка лежит на доске
        if not self.is_valid(self.row, self.col):
            raise ValueError(f"Недопустимая позиция row={self.row}, col={self.col}")

    def __hash__(self) -> int:
        # ИЗМЕНЕНИЕ ДЛЯ СКОРОСТИ. Клетки постоянно лежат в словаре доски и в множествах ходов,
        # поэтому хеш считается миллионы раз. Хеш, который dataclass генерирует сам, строит кортеж
        # и хеширует его; наш вариант — одно умножение и одно сложение.
        # Числа 0..63 уникальны для каждой клетки, коллизий нет.
        # Явно заданный __hash__ dataclass не перезаписывает; __eq__ он по-прежнему генерирует сам,
        # а равные клетки дают равные хеши — контракт соблюдён.
        return self.row * 8 + self.col

    @classmethod
    def is_valid(cls, row: int, col: int) -> bool:
        return 0 <= row < cls.SIZE and 0 <= col < cls.SIZE

    @classmethod
    def from_str(cls, s: str) -> Position:
        """'e3' -> Position(row=2, col=4)"""
        # проверка формата — как раньше
        if not isinstance(s, str) or len(s) != 2 or s[0] not in cls.CHARS or s[1] not in "12345678":
            raise ValueError(f"Недопустимая позиция {s}")
        # (int(s[1]) - 1) — номер ряда, CHARS.index(s[0]) — номер колонки;
        # ряд * 8 + колонка — индекс в таблице готовых клеток _ALL (создаётся в конце файла).
        # Возвращаем готовый объект, а не создаём новый.
        return _ALL[(int(s[1]) - 1) * 8 + cls.CHARS.index(s[0])]

    def offset(self, d_row: int, d_col: int) -> Position | None:
        """Сдвиг на клетки; None, если вышли за доску.
        Берём готовый объект из таблицы: при переборе это самая частая операция,
        и создавать каждый раз новый Position (с проверкой в __post_init__) слишком дорого"""
        row, col = self.row + d_row, self.col + d_col     # новые координаты
        if 0 <= row < 8 and 0 <= col < 8:                 # границы проверяем обычным сравнением
            return _ALL[row * 8 + col]                    # внутри доски: возвращаем уже существующий объект
        return None                                       # за доской

    def __str__(self) -> str:
        return f"{self.CHARS[self.col]}{self.row + 1}"

    __repr__ = __str__


# Все 64 клетки создаются ОДИН раз при импорте модуля.
# Внешний цикл по row, внутренний по col, поэтому клетка (row, col) лежит под индексом row * 8 + col.
# Список стоит ПОСЛЕ класса, потому что ему нужен сам класс; методы обращаются к _ALL
# в момент вызова, к тому времени он уже существует.
# Обычный конструктор Position(r, c) работает как раньше (его, например, использует game.py):
# такие объекты равны кэшированным и хешируются так же.
_ALL = [Position(row, col) for row in range(Position.SIZE) for col in range(Position.SIZE)]
