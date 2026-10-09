from tools.position import Position


def pos(s: str) -> Position:
    return Position.from_str(s)


def moves(piece, board, at: str) -> set[str]:
    return {str(p) for p in piece.get_possible_moves(board, pos(at))}