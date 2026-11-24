from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    SIZE = 8
    CHARS = "abcdefgh"

    row: int                # 0..7 с аннотацией это атрибут экземпляра
    col: int                # 0..7 с аннотацией это атрибут экземпляра

    def __post_init__(self): # после __init__, ну по названию можно догадаться
        if not self.is_valid(self.row, self.col):
            raise ValueError(f"Недопустимая позиция row={self.row}, col={self.col}")

    def __hash__(self) -> int:
        # своя простая хеш-функция: быстрее сгенерированной dataclass-ом, а клетки лежат в словарях
        return self.row * 8 + self.col

    @classmethod
    def is_valid(cls, row: int, col: int) -> bool:
        return 0 <= row < cls.SIZE and 0 <= col < cls.SIZE

    @classmethod
    def from_str(cls, s: str) -> Position:
        """'e3' -> Position(row=2, col=4)"""
        if not isinstance(s, str) or len(s) != 2 or s[0] not in cls.CHARS or s[1] not in "12345678":
            raise ValueError(f"Недопустимая позиция {s}")
        return _ALL[(int(s[1]) - 1) * 8 + cls.CHARS.index(s[0])]

    def offset(self, d_row: int, d_col: int) -> Position | None:
        """Сдвиг на клетки; None, если вышли за доску.
        Берём готовый объект из таблицы: при переборе это самая частая операция,
        и создавать каждый раз новый Position (с проверкой в __post_init__) слишком дорого"""
        row, col = self.row + d_row, self.col + d_col
        if 0 <= row < 8 and 0 <= col < 8:
            return _ALL[row * 8 + col]
        return None

    def __str__(self) -> str:
        return f"{self.CHARS[self.col]}{self.row + 1}"

    __repr__ = __str__


_ALL = [Position(row, col) for row in range(Position.SIZE) for col in range(Position.SIZE)]