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
from pieces.sliding_piece import SlidingPiece  # НОВОЕ: нужны константы направлений ROOK_DIRS и BISHOP_DIRS

if TYPE_CHECKING:
    from pieces.piece import Piece


class Board:
    START_POS_PIECES = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]

    def __init__(self):
        self._pieces: dict[Position, Piece] = {}        # клетка -> фигура; пустые клетки в словаре отсутствуют
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

    def all_pieces(self):
        """НОВОЕ. Все фигуры без позиций (для быстрой оценки материала).
        values() возвращает «вид» на значения словаря без копирования,
        а pieces_of каждый раз строил целый список."""
        return self._pieces.values()

    def find_king(self, color: Color) -> Position | None:
        # ИЗМЕНЕНО: идём прямо по словарю и останавливаемся на первом короле нужного цвета.
        # Раньше сначала строился список всех фигур цвета через pieces_of.
        for pos, piece in self._pieces.items():
            if piece.color is color and isinstance(piece, King):
                return pos
        return None

    def is_attacked(self, square: Position, by: Color) -> bool:
        """НОВОЕ. Бьёт ли хоть одна фигура цвета by клетку square.
        Смотрим из самой клетки наружу: прыжки коня, соседи-короли, две клетки пешек
        и лучи слонов/ладей/ферзей. Так не нужно строить все ходы соперника,
        как делала старая is_in_check."""
        get = self._pieces.get  # локальная ссылка на метод: обращаться к ней быстрее, чем искать атрибут каждый раз

        # --- кони ---
        # прыжок коня симметричен: если конь стоит «конским ходом» от клетки, он её бьёт
        for d_row, d_col in Knight.JUMPS:                # восемь прыжков коня
            pos = square.offset(d_row, d_col)            # клетка, где мог бы стоять вражеский конь
            if pos is not None:                          # None — вышли за доску
                piece = get(pos)                         # что там стоит
                if piece is not None and piece.color is by and isinstance(piece, Knight):
                    return True                          # вражеский конь бьёт клетку

        # --- король ---
        # короли не могут стоять рядом, поэтому соседний вражеский король тоже «бьёт» клетку
        for d_row, d_col in King.DIR:                    # восемь соседних клеток
            pos = square.offset(d_row, d_col)
            if pos is not None:
                piece = get(pos)
                if piece is not None and piece.color is by and isinstance(piece, King):
                    return True

        # --- пешки ---
        # белая пешка бьёт на ряд ВВЕРХ по диагонали, значит, чтобы бить square, она должна стоять
        # на ряд НИЖЕ (-1). Чёрная бьёт вниз и стоит на ряд ВЫШЕ (+1).
        back = -1 if by is Color.WHITE else 1
        for d_col in (-1, 1):                            # пешка слева или справа от нужной вертикали
            pos = square.offset(back, d_col)
            if pos is not None:
                piece = get(pos)
                if piece is not None and piece.color is by and isinstance(piece, Pawn):
                    return True

        # --- слоны, ладьи, ферзи: лучи ---
        # две группы лучей: прямые (бьют ладья и ферзь) и диагонали (бьют слон и ферзь)
        for directions, kinds in ((SlidingPiece.ROOK_DIRS, (Rook, Queen)),
                                  (SlidingPiece.BISHOP_DIRS, (Bishop, Queen))):
            for d_row, d_col in directions:
                pos = square.offset(d_row, d_col)        # первая клетка луча
                while pos is not None:                   # идём вдоль луча до края доски
                    piece = get(pos)
                    if piece is not None:                # встретили фигуру: луч дальше не идёт
                        if piece.color is by and isinstance(piece, kinds):
                            return True                  # это вражеская фигура подходящего типа: клетка под боем
                        break                            # своя или неподходящая фигура закрывает луч
                    pos = pos.offset(d_row, d_col)       # пусто: двигаемся дальше
        return False                                     # никто не бьёт

    def is_in_check(self, color: Color) -> bool:
        # ИЗМЕНЕНО: раньше строились ходы ВСЕХ фигур соперника, чтобы проверить одну клетку.
        # Теперь проверяется только клетка короля через is_attacked.
        king_pos = self.find_king(color)
        if king_pos is None:  # для тестиков
            return False
        return self.is_attacked(king_pos, color.opposite)

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
