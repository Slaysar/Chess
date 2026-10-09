from .sliding_piece import SlidingPiece

class Bishop(SlidingPiece):

    SYMBOL = "B"

    @property
    def directions(self) -> tuple[tuple[int, int]]:
        return self.BISHOP_DIRS
