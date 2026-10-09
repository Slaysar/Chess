from .sliding_piece import SlidingPiece

class Bishop(SlidingPiece):

    SYMBOL = "Bi"

    BISHOP_DIRS = [(1, 1), (-1, 1), (1, -1), (-1, -1)]

    @property
    def directions(self) -> list[tuple[int, int]]:
        return self.BISHOP_DIRS
