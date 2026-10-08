from enum import Enum


class Color(Enum):
    WHITE = "white"
    BLACK = "black"

    @property
    def opposite(self) -> "Color":
        return Color.BLACK if self is Color.WHITE else Color.WHITE

    def __str__(self) -> str:
        return self.value.capitalize()