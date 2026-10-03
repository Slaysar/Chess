from .figure import Figure
from tools.position import Position

class Pawn(Figure):

    def get_possible_moves(self) -> set[Position]:
        position = self._position
        moves = {position}
        move = None

        if self.color.is_white():
            move = lambda x: x + 1
        if self.color.is_black():
            move = lambda x: x - 1

        new_pos = f"{position.letter_coord}{move(int(position.num_coord))}"

        if Position.is_correct_move(new_pos):
            moves.add(Position(new_pos))

        return moves

    def __repr__(self) -> str:
        return f'Pawn'

    __str__ = __repr__