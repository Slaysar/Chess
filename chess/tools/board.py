from __future__ import annotations
from typing import TYPE_CHECKING
from .position import Position
from .color import Color
from pieces.rook import Rook
from pieces.knight import Knight
from pieces.bishop import Bishop
from pieces.queen import Queen
from pieces.king import King
from pieces.pawn import Pawn

if TYPE_CHECKING:
    from pieces.piece import Piece


class Board:
    START_POS_PIECES = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]

    def __init__(self):
        self._pieces: dict[Position, Piece] = {}
        self.en_passant_target: Position | None = None  # клетка, через которую прошла пешка

    def setup(self) -> None:
        """Начальная расстановка"""
        self.clear()
        for color, back_row, pawn_row in ((Color.WHITE, 0, 1), (Color.BLACK, 7, 6)):
            for col, piece_cls in enumerate(self.START_POS_PIECES):
                self.place(piece_cls(color), Position(back_row, col))
            for col in range(Position.SIZE):
                self.place(Pawn(color), Position(pawn_row, col))

    def get(self, pos: Position) -> Piece | None:
        return self._pieces.get(pos)

    def place(self, piece: Piece, pos: Position) -> None:
        self._pieces[pos] = piece

    def move(self, source: Position, destination: Position) -> None:
        self._pieces[destination] = self._pieces.pop(source)

    def remove(self, pos: Position) -> None:
        self._pieces.pop(pos, None)

    def clear(self) -> None:
        self._pieces.clear()
        self.en_passant_target = None

    def pieces_of(self, color: Color):
        """Все (позиция, фигура) заданного цвета"""
        return [(p, piece) for p, piece in self._pieces.items() if piece.color is color]

    def find_king(self, color: Color) -> Position | None:
        for pos, piece in self.pieces_of(color):
            if isinstance(piece, King):
                return pos
        return None

    def is_in_check(self, color: Color) -> bool:
        king_pos = self.find_king(color)
        if king_pos is None:  # для тестиков
            return False
        return any(king_pos in piece.get_possible_moves(self, pos) for pos, piece in self.pieces_of(color.opposite))

    def has_insufficient_material(self) -> bool:
        """Мат невозможен ни у одной из сторон"""
        others = [(pos, p) for pos, p in self._pieces.items() if not isinstance(p, King)]
        if not others:  # король против короля
            return True
        if len(others) == 1 and isinstance(others[0][1], (Bishop, Knight)):
            return True  # король + слон/конь против короля
        if all(isinstance(p, Bishop) for _, p in others):  # только слоны одного цвета полей
            return len({(pos.row + pos.col) % 2 for pos, _ in others}) == 1
        return False

    def pieces_key(self) -> tuple:
        """Расстановка в виде хешируемого кортежа"""
        return tuple(sorted(
            (pos.row, pos.col, piece.SYMBOL, piece.color.name)
            for pos, piece in self._pieces.items()
        ))

    def __repr__(self) -> str:
        rows = []
        for row in reversed(range(Position.SIZE)):
            cells = []
            for col in range(Position.SIZE):
                piece = self.get(Position(row, col))
                cells.append(str(piece) if piece is not None else ".")
            rows.append(f"{row + 1} " + " ".join(f"{c:>6}" for c in cells))
        rows.append("  " + " ".join(f"{ch:>6}" for ch in Position.CHARS))
        return "\n\n\n".join(rows)
