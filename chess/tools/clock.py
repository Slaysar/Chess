from __future__ import annotations
import time

from tools.color import Color


class Clock:
    """Шахматные часы. Пока никто не сходил, время не идёт;
    после каждого хода останавливаются часы того, кто сходил, и запускаются часы соперника"""

    def __init__(self, seconds: float, timer=time.monotonic):
        self.left = {Color.WHITE: float(seconds), Color.BLACK: float(seconds)}
        self.running: Color | None = None
        self._timer = timer          # подменяется в тестах
        self._since = 0.0            # когда запустили часы текущего игрока

    def remaining(self, color: Color) -> float:
        left = self.left[color]
        if self.running is color:
            left -= self._timer() - self._since
        return max(left, 0.0)

    def start(self, color: Color) -> None:
        self.stop()
        self.running = color
        self._since = self._timer()

    def stop(self) -> None:
        """Заморозить часы (партия окончена)"""
        if self.running is not None:
            self.left[self.running] = self.remaining(self.running)
            self.running = None

    def switch(self) -> None:
        """Ход сделан: время передаётся сопернику"""
        if self.running is not None:
            self.start(self.running.opposite)

    def flagged(self) -> Color | None:
        """Цвет того, у кого упал флажок (время вышло), иначе None"""
        if self.running is not None and self.remaining(self.running) <= 0:
            return self.running
        return None