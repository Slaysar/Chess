from __future__ import annotations
from typing import TYPE_CHECKING
from tools.board import Board
from tools.color import Color
from tools.position import Position
from tools.game_status import GameStatus
from pieces.pawn import Pawn
from pieces.queen import Queen
from pieces.rook import Rook
from pieces.bishop import Bishop
from pieces.knight import Knight
from pieces.king import King
from tools.move_record import MoveRecord, history_text

if TYPE_CHECKING:
    from pieces.piece import Piece


class Game:
    # ==================== Константы и состояние партии ====================

    FIFTY_MOVE_LIMIT = 100
    PROMOTION_PIECES = {"q": Queen, "r": Rook, "b": Bishop, "n": Knight}

    def __init__(self):
        self.board = Board()
        self.board.setup()
        self.turn = Color.WHITE
        self.history: list[MoveRecord] = []   # записи ходов для нотации
        self.half_move_clock = 0              # полуходы без взятия и хода пешки (правило 50 ходов)
        self.positions = [self.position_key()]  # ключи позиций (троекратное повторение)

    # ==================== Легальность ходов ====================

    def legal_moves(self, source: Position) -> set[Position]:
        """Ходы фигуры с source, после которых её король не под шахом"""
        piece = self.board.get(source)
        if piece is None:
            return set()
        result = set()
        for destination in piece.get_possible_moves(self.board, source):
            captured_pos = self.captured_square(source, destination)
            captured = self.board.get(captured_pos)
            self.board.move(source, destination)  # пробный ход
            if captured_pos != destination:
                self.board.remove(captured_pos)  # пешка, взятая на проходе
            if not self.board.is_in_check(piece.color):
                result.add(destination)
            self.board.move(destination, source)  # откат
            if captured is not None:
                self.board.place(captured, captured_pos)  # вернуть на её место
        if isinstance(piece, King):
            result = result.union(self.castling_moves(source))
        return result

    def has_legal_moves(self, color: Color) -> bool:
        return any(self.legal_moves(pos) for pos, _ in self.board.pieces_of(color))

    # ==================== Выполнение хода ====================

    def make_move(self, source: Position, destination: Position,
                  promotion: type[Piece] | None = None) -> None:
        # --- проверки (до них доска не меняется) ---
        piece = self.board.get(source)
        if piece is None:
            raise ValueError("На клетке нет фигуры")
        if piece.color is not self.turn:
            raise ValueError("Сейчас ходит другой цвет")
        if destination not in self.legal_moves(source):
            raise ValueError("Недопустимый ход")

        promotes = self.is_promotion(source, destination)
        if promotes and promotion not in self.PROMOTION_PIECES.values():
            raise ValueError("В эту фигуру пешку превратить нельзя")

        # --- факты о позиции ДО хода (после хода их уже не восстановить) ---
        castling = isinstance(piece, King) and abs(destination.col - source.col) == 2
        captured_pos = self.captured_square(source, destination)
        is_capture = captured_pos != destination or self.board.get(destination) is not None

        # --- запись хода в нотации (суффикс шаха и мата добавится после хода) ---
        rivals = [] if castling or isinstance(piece, Pawn) else self._rivals(piece, source, destination)
        record = MoveRecord.build(piece, source, destination,
                                  is_capture=is_capture, castling=castling,
                                  promotion=promotion if promotes else None, rivals=rivals)

        # --- изменение доски ---
        if captured_pos != destination:
            self.board.remove(captured_pos)  # взятие на проходе: жертва стоит не на destination
        if castling:
            rook_from = Position(source.row, 7 if destination.col > source.col else 0)
            rook_to = Position(source.row, (source.col + destination.col) // 2)
            self.board.move(rook_from, rook_to)
            self.board.get(rook_to).has_moved = True

        self.board.move(source, destination)
        piece.has_moved = True
        if promotes:
            self.board.place(promotion(piece.color), destination)

        # --- состояние после хода ---
        # проходное поле живёт ровно один ход
        self.board.en_passant_target = None
        if isinstance(piece, Pawn) and abs(destination.row - source.row) == 2:
            self.board.en_passant_target = Position((source.row + destination.row) // 2, source.col)

        self.turn = self.turn.opposite

        # счётчик: взятие и ход пешки его обнуляют (is_capture посчитан до хода)
        if is_capture or isinstance(piece, Pawn):
            self.half_move_clock = 0
        else:
            self.half_move_clock += 1

        # сохраняем позицию для правила повторения ходов
        self.positions.append(self.position_key())

        # --- шах и мат видны только после хода ---
        if self.board.is_in_check(self.turn):
            record = record.with_suffix("+" if self.has_legal_moves(self.turn) else "#")
        self.history.append(record)

    # ==================== Особые правила: превращение и взятие на проходе ====================

    def is_promotion(self, source: Position, destination: Position) -> bool:
        """Дойдёт ли пешка с source на destination до последнего ряда"""
        piece = self.board.get(source)
        return isinstance(piece, Pawn) and destination.row == piece.promotion_row

    def captured_square(self, source: Position, destination: Position) -> Position:
        """Клетка, с которой этот ход снимет фигуру"""
        piece = self.board.get(source)
        is_en_passant = (
                isinstance(piece, Pawn)
                and source.col != destination.col
                and self.board.get(destination) is None  # диагональ на пустую клетку
        )
        return Position(source.row, destination.col) if is_en_passant else destination

    # ==================== Особые правила: рокировка ====================

    def castling_moves(self, source: Position) -> set[Position]:
        """Клетки, на которые король с source может рокироваться, вычисляет рокировочные клетки"""
        king = self.board.get(source)
        if not isinstance(king, King) or king.has_moved:
            return set()
        home_row = 0 if king.color is Color.WHITE else 7
        if source != Position(home_row, 4):
            return set()
        if self.board.is_in_check(king.color):  # из-под шаха рокироваться нельзя
            return set()

        castling_moves = ((7, 1, (5, 6)), (0, -1, (1, 2, 3)))

        result = set()
        # (колонка ладьи, шаг короля, клетки между королём и ладьёй)
        for rook_col, step, between in castling_moves:
            rook = self.board.get(Position(home_row, rook_col))
            if not isinstance(rook, Rook) or rook.color is not king.color or rook.has_moved:
                continue
            if any(self.board.get(Position(home_row, c)) is not None for c in between):
                continue
            # король проходит одну клетку и встаёт на вторую: обе не должны быть под боем
            passed = Position(home_row, source.col + step)
            landing = Position(home_row, source.col + 2 * step)
            if self._king_safe_at(king, source, passed) and self._king_safe_at(king, source, landing):
                result.add(landing)

        return result

    def _king_safe_at(self, king: Piece, source: Position, square: Position) -> bool:
        """Не под шахом ли король, если поставить его на пустую square (пробный ход)"""
        self.board.move(source, square)
        safe = not self.board.is_in_check(king.color)
        self.board.move(square, source)
        return safe

    # ==================== Позиция и троекратное повторение ====================

    def _castling_rights(self) -> tuple[bool, ...]:
        """Сохранилось ли право на рокировку: (белые O-O, белые O-O-O, чёрные O-O, чёрные O-O-O)"""
        rights = []
        for color, row in ((Color.WHITE, 0), (Color.BLACK, 7)):
            king = self.board.get(Position(row, 4))
            for rook_col in (7, 0):
                rook = self.board.get(Position(row, rook_col))
                rights.append(
                    isinstance(king, King) and king.color is color and not king.has_moved
                    and isinstance(rook, Rook) and rook.color is color and not rook.has_moved
                )
        return tuple(rights)

    def _en_passant_key(self) -> Position | None:
        """Проходное поле считается, только если на него реально можно взять"""
        target = self.board.en_passant_target
        if target is None:
            return None
        for pos, piece in self.board.pieces_of(self.turn):
            if isinstance(piece, Pawn) and target in self.legal_moves(pos):
                return target
        return None

    def position_key(self) -> tuple:
        """Позиция для сравнения: расстановка, чей ход, права на рокировку, проходное поле"""
        return self.board.pieces_key(), self.turn, self._castling_rights(), self._en_passant_key()

    def repetition_count(self) -> int:
        """Сколько раз встречалась текущая позиция"""
        # после взятия или хода пешки старые позиции повториться не могут,
        # поэтому смотрим только на последние half_move_clock + 1 позиций
        window = self.positions[-(self.half_move_clock + 1):]
        return window.count(self.positions[-1])

    # ==================== Статус партии и ничьи ====================

    def draw_reason(self) -> str | None:
        if self.board.has_insufficient_material():
            return "недостаточно материала"
        if self.repetition_count() >= 3:
            return "троекратное повторение"
        if self.half_move_clock >= self.FIFTY_MOVE_LIMIT:
            return "правило 50 ходов"
        return None

    def status(self) -> GameStatus:
        if self.board.has_insufficient_material():
            return GameStatus.DRAW
        in_check = self.board.is_in_check(self.turn)
        if not self.has_legal_moves(self.turn):
            return GameStatus.CHECKMATE if in_check else GameStatus.STALEMATE
        if self.repetition_count() >= 3 or self.half_move_clock >= self.FIFTY_MOVE_LIMIT:
            return GameStatus.DRAW
        return GameStatus.CHECK if in_check else GameStatus.PLAYING

    # ==================== История и нотация ====================

    def _rivals(self, piece: Piece, source: Position, destination: Position) -> list[Position]:
        """Другие фигуры того же типа и цвета, которые тоже могут пойти на destination"""
        return [
            pos for pos, other in self.board.pieces_of(piece.color)
            if other is not piece and type(other) is type(piece)
               and destination in self.legal_moves(pos)
        ]

    def history_text(self) -> str:
        return history_text(self.history)