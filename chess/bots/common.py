from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game
    from tools.board import Board
    from tools.color import Color
    from tools.position import Position

VALUES = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}  # цена фигур в пешках
MATE = 1000  # оценка мата


def evaluate(board: Board, color: Color) -> int:
    mine = sum(VALUES[piece.SYMBOL] for _, piece in board.pieces_of(color))
    theirs = sum(VALUES[piece.SYMBOL] for _, piece in board.pieces_of(color.opposite))
    return mine - theirs


def all_moves(game: Game, color: Color) -> list[tuple[Position, Position]]:
    moves = []
    for source, _ in game.board.pieces_of(color):
        for destination in sorted(game.legal_moves(source), key=lambda p: (p.row, p.col)):
            moves.append((source, destination))
    return moves


def try_move(board: Board, source: Position, destination: Position):
    captured = board.get(destination)
    en_passant = board.en_passant_target
    board.move(source, destination)
    board.en_passant_target = None
    return captured, en_passant


def undo_move(board: Board, source: Position, destination: Position, saved) -> None:
    captured, en_passant = saved
    board.move(destination, source)
    if captured is not None:
        board.place(captured, destination)
    board.en_passant_target = en_passant


def is_checkmate(game: Game, color: Color) -> bool:
    return game.board.is_in_check(color) and not game.has_legal_moves(color)


def pseudo_moves(board: Board, color: Color) -> list[tuple[Position, Position]]:
    moves = []
    for source, piece in board.pieces_of(color):
        for destination in piece.get_possible_moves(board, source):
            moves.append((source, destination))
    return moves
