class Color:

    COLORS = {"white", "black"}

    def __init__(self, color: str):
        if color not in self.COLORS:
            raise ValueError(f"Недопустимый цвет {color}")
        self._color = color

    @property
    def color(self):
        return self._color

    def __repr__(self):
        return f"{self.color}".capitalize()

    __str__ = __repr__

    def is_white(self) -> bool:
        return self._color == 'white'

    def is_black(self) -> bool:
        return  self._color == 'black'