from __future__ import annotations
from .position import Position
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from figures.piece import Piece

class Board:
    def __init__(self):
        self._pieces : dict[Position, Piece] = {}

    def get(self, pos: Position) -> Piece | None:
        return self._pieces.get(pos)

    def place(self, piece: Piece, pos: Position) -> None:
        self._pieces[pos] = piece

    def move(self, source: Position, destination: Position) -> None:
        self._pieces[destination] = self._pieces.pop(source)

    def remove(self, pos: Position) -> None:
        self._pieces.pop(pos, None)

    def __repr__(self) -> str:
        rows = []
        for row in reversed(range(Position.SIZE)):
            cells = []
            for col in range(Position.SIZE):
                piece = self.get(Position(row, col))
                cells.append(str(piece) if piece is not None else ".")
            rows.append(f"{row + 1} " + " ".join(f"{c:>6}" for c in cells))
        rows.append("  " + " ".join(f"{ch:>6}" for ch in Position.CHARS))
        return "\n".join(rows)
