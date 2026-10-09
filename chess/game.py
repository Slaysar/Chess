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
            captured = self.board.get(destination)
            self.board.move(source, destination)  # пробный ход
            if not self.board.is_in_check(piece.color):
                result.add(destination)
            self.board.move(destination, source)  # откат
            if captured is not None:
                self.board.place(captured, destination)  # вернуть съеденную
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

        self.board.move(source, destination)
        if promotes:
            self.board.place(promotion(piece.color), destination)

        self.turn = self.turn.opposite

    def is_promotion(self, source: Position, destination: Position) -> bool:
        """Дойдёт ли пешка с source на destination до последнего ряда"""
        piece = self.board.get(source)
        return isinstance(piece, Pawn) and destination.row == piece.promotion_row

    def status(self) -> GameStatus:
        """'playing', 'check', 'checkmate' или 'stalemate' для стороны, которая ходит"""
        in_check = self.board.is_in_check(self.turn)
        if self.has_legal_moves(self.turn):
            return GameStatus.CHECK if in_check else GameStatus.PLAYING
        return GameStatus.CHECKMATE if in_check else GameStatus.STALEMATE
