from .sliding_piece import SlidingPiece
from tools.color import Color


class Rook(SlidingPiece):
    SYMBOL = "R"

    @property
    def directions(self) -> tuple[tuple[int, int]]:
        return self.ROOK_DIRS
