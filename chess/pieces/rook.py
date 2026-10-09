from .sliding_piece import SlidingPiece

class Rook(SlidingPiece):

    SYMBOL = "R"

    ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    @property
    def directions(self) -> list[tuple[int, int]]:
        return self.ROOK_DIRS
