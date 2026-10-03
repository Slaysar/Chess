from .figure import Figure
from tools.position import Position


class Rook(Figure):

    def get_possible_moves(self) -> set[Position]:
        position = self._position
        moves : set[Position] = {position}

        for num_coord in Position.NUM_COORD:
            pos = Position(f"{position.letter_coord}{num_coord}")

        for letter_coord in Position.LETTERS_COORD:
            moves.add(Position(f"{letter_coord}{position.num_coord}"))

        return moves

    def __repr__(self) -> str:
        return f"Rook"

    __str__ = __repr__
