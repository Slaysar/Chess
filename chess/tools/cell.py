from figures.figure import Figure
from .position import Position


class Cell:
    def __init__(self,figure : Figure | None = None):
        self.figure = figure

    def __repr__(self) -> str:
        str_figure = str(self.figure) if self.figure is not None else 'Empty'
        return f"{str_figure}"