class Position:

    LETTERS_COORD : list[str] = ["a", "b", "c", "d", "e", "f", "g", "h"]
    NUM_COORD : list[str] = ["1", "2", "3", "4", "5", "6", "7", "8"]

    def __init__(self, position: str):
        self._validate(position)
        self._letter_coord = position[0]
        self._num_coord = position[1]

    def __repr__(self) -> str:
        return f"Position: {self._letter_coord}{self._num_coord}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Position):
            return NotImplemented
        return self._letter_coord == other._letter_coord and self._num_coord == self.num_coord

    def __hash__(self) -> int:
        return hash((self._letter_coord, self._num_coord))

    __str__ = __repr__

    @property
    def letter_coord(self) -> str:
        return self._letter_coord

    @property
    def num_coord(self) -> str:
        return self._num_coord

    @classmethod
    def _validate(cls, position: str) -> None:

        if not isinstance(position, str) or len(position) != 2:
            raise TypeError(f"Неверный формат хода {position}")

        if position[0] not in cls.LETTERS_COORD or position[1] not in cls.NUM_COORD:
            raise ValueError(f"Недопустимый ход {position}")

    @classmethod
    def is_correct_move(cls, position: str):

        if not isinstance(position, str) or len(position) != 2:
            return False

        if position[0] not in cls.LETTERS_COORD or position[1] not in cls.NUM_COORD:
            return False

        return True