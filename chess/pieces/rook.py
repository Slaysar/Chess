from .sliding_piece import SlidingPiece

class Rook(SlidingPiece):

    SYMBOL = "R"

    @property
    def directions(self) -> tuple[tuple[int, int]]:
        return self.ROOK_DIRS
