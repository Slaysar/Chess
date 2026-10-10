from __future__ import annotations
from typing import TYPE_CHECKING
from unittest import result

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

if TYPE_CHECKING:
    from pieces.piece import Piece


class Game:
    PROMOTION_PIECES = {"q": Queen, "r": Rook, "b": Bishop, "n": Knight}

    def __init__(self):
        self.board = Board()
        self.board.setup()
        self.turn = Color.WHITE

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

    def make_move(self, source: Position, destination: Position,
                  promotion: type[Piece] | None = None) -> None:
        piece = self.board.get(source)
        if piece is None:
            raise ValueError("На клетке нет фигуры")
        if piece.color is not self.turn:
            raise ValueError("Сейчас ходит другой цвет")
        if destination not in self.legal_moves(source):
            raise ValueError("Недопустимый ход")

        promotes = self.is_promotion(source, destination)
        if promotes:
            if promotion not in self.PROMOTION_PIECES.values():
                raise ValueError("В эту фигуру пешку превратить нельзя")

        castling = isinstance(piece, King) and abs(destination.col - source.col) == 2

        captured_pos = self.captured_square(source, destination)  # считаем ДО хода
        if captured_pos != destination:
            self.board.remove(captured_pos)

        if castling:
            rook_from = Position(source.row, 7 if destination.col > source.col else 0)
            rook_to = Position(source.row, (source.col + destination.col) // 2)
            self.board.move(rook_from, rook_to)
            self.board.get(rook_to).has_moved = True

        self.board.move(source, destination)
        piece.has_moved = True
        if promotes:
            self.board.place(promotion(piece.color), destination)

        # взятие на проходе живёт ровно один ход
        self.board.en_passant_target = None
        if isinstance(piece, Pawn) and abs(destination.row - source.row) == 2:
            self.board.en_passant_target = Position((source.row + destination.row) // 2, source.col)

        self.turn = self.turn.opposite

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

    def castling_moves(self, source: Position) -> set[Position]:
        """Клетки, на которые король с source может рокироваться"""
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

    def status(self) -> GameStatus:
        """'playing', 'check', 'checkmate' или 'stalemate' для стороны, которая ходит"""
        in_check = self.board.is_in_check(self.turn)
        if self.has_legal_moves(self.turn):
            return GameStatus.CHECK if in_check else GameStatus.PLAYING
        return GameStatus.CHECKMATE if in_check else GameStatus.STALEMATE
