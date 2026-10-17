from tools.position import Position
from tools.color import Color


def pos(s: str) -> Position:
    return Position.from_str(s)


def moves(piece, board, at: str) -> set[str]:
    return {str(p) for p in piece.get_possible_moves(board, pos(at))}


def snapshot(board):
    """Состояние доски, которое меняют ходы: фигуры, флаги has_moved, проходное поле"""
    pieces = dict(board.pieces_of(Color.WHITE) + board.pieces_of(Color.BLACK))
    flags = {id(piece): piece.has_moved for piece in pieces.values()}
    return pieces, flags, board.en_passant_target
