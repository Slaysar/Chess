from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game
    from tools.board import Board
    from tools.color import Color
    from tools.position import Position

VALUES = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}  # стоимость фигур для оценки материала
MATE = 1000                                                  # базовая «стоимость» мата, больше любого материала


def evaluate(board: Board, color: Color) -> int:
    """Материал color минус материал соперника.
    ИЗМЕНЕНО: один проход по фигурам без промежуточных списков
    (раньше pieces_of вызывался дважды, и каждый вызов строил список)."""
    total = 0                                        # итоговая разность
    for piece in board.all_pieces():                 # все фигуры обоих цветов
        value = VALUES[piece.SYMBOL]                 # стоимость этой фигуры
        total += value if piece.color is color else -value  # своя прибавляет, чужая вычитает
    return total


def all_moves(game: Game, color: Color) -> list[tuple[Position, Position]]:
    """Все ЛЕГАЛЬНЫЕ ходы цвета color в виде (откуда, куда)"""
    moves = []
    for source, _ in game.board.pieces_of(color):
        for destination in sorted(game.legal_moves(source), key=lambda p: (p.row, p.col)):  # сортировка = детерминизм
            moves.append((source, destination))
    return moves


def try_move(board: Board, source: Position, destination: Position):
    """Пробный ход прямо на доске; возвращает то, что нужно для отката"""
    captured = board.get(destination)         # съеденная фигура (или None)
    en_passant = board.en_passant_target      # проходное поле до хода
    board.move(source, destination)
    board.en_passant_target = None            # внутри перебора взятие на проходе не используется
    return captured, en_passant


def undo_move(board: Board, source: Position, destination: Position, saved) -> None:
    """Откат хода, сделанного try_move"""
    captured, en_passant = saved
    board.move(destination, source)           # фигура возвращается на старое место
    if captured is not None:
        board.place(captured, destination)    # съеденная фигура возвращается
    board.en_passant_target = en_passant


def is_checkmate(game: Game, color: Color) -> bool:
    return game.board.is_in_check(color) and not game.has_legal_moves(color)


def pseudo_moves(board: Board, color: Color) -> list[tuple[Position, Position]]:
    """Псевдоходы: по правилам ходов фигур, но БЕЗ проверки, остался ли свой король под шахом"""
    moves = []
    for source, piece in board.pieces_of(color):
        for destination in piece.get_possible_moves(board, source):
            moves.append((source, destination))
    return moves
