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

    @classmethod
    def is_valid(cls, row: int, col: int) -> bool:
        return 0 <= row < cls.SIZE and 0 <= col < cls.SIZE

    @classmethod
    def from_str(cls, s: str) -> Position:
        """'e3' -> Position(row=2, col=4)"""
        if not isinstance(s, str) or len(s) != 2 or s[0] not in cls.CHARS or s[1] not in "12345678":
            raise ValueError(f"Недопустимая позиция {s}")
        return cls(row=int(s[1]) - 1, col=cls.CHARS.index(s[0]))

    def offset(self, d_row: int, d_col: int) -> Position | None:
        """Сдвиг на клетки; None, если вышли за доску"""
        row, col = self.row + d_row, self.col + d_col
        return Position(row, col) if self.is_valid(row, col) else None

    def __str__(self) -> str:
        return f"{self.CHARS[self.col]}{self.row + 1}"

    __repr__ = __str__