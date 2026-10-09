from .sliding_piece import SlidingPiece

class Queen(SlidingPiece):

    SYMBOL = "Q"

    @property
    def directions(self) -> tuple[tuple[int, int]]:
        return self.ROOK_DIRS + self.BISHOP_DIRS
