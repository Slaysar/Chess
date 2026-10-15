from .sliding_piece import SlidingPiece
from tools.color import Color


class Rook(SlidingPiece):
    SYMBOL = "R"

    def __init__(self, color: Color):
        super().__init__(color)
        self.has_moved = False

    @property
    def directions(self) -> tuple[tuple[int, int]]:
        return self.ROOK_DIRS
