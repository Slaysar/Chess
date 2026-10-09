from .sliding_piece import SlidingPiece

class Queen(SlidingPiece):

    SYMBOL = "Q"

    ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    BISHOP_DIRS = [(1, 1), (-1, 1), (1, -1), (-1, -1)]

    @property
    def directions(self) -> list[tuple[int, int]]:
        return self.ROOK_DIRS + self.BISHOP_DIRS
