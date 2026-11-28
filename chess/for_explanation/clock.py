from __future__ import annotations  # аннотации не вычисляются при определении класса, поэтому можно писать `Color | None`
import time                         # нужен time.monotonic: таймер, который не прыгает при переводе системных часов

from tools.color import Color       # цвета игроков будут ключами словаря с оставшимся временем


class Clock:
    """Шахматные часы. Пока никто не сходил, время не идёт;
    после каждого хода останавливаются часы того, кто сходил, и запускаются часы соперника.

    Отдельного потока-таймера нет: «живое» время считается по требованию
    как (сохранённый остаток) минус (сколько прошло с момента запуска часов)."""

    def __init__(self, seconds: float, timer=time.monotonic):
        # сколько секунд осталось у каждого НА МОМЕНТ ПОСЛЕДНЕЙ ОСТАНОВКИ его часов
        # (это не «живое» значение, живое считает remaining)
        self.left = {Color.WHITE: float(seconds), Color.BLACK: float(seconds)}
        # чьи часы идут прямо сейчас; None — не идёт никто (до первого хода и после конца партии)
        self.running: Color | None = None
        # функция, откуда берём текущее время; в тестах подменяется управляемым FakeTimer
        self._timer = timer
        # отметка времени, когда запустили часы текущего игрока
        self._since = 0.0

    def remaining(self, color: Color) -> float:
        """Сколько секунд осталось у игрока color прямо сейчас"""
        left = self.left[color]                      # сохранённый остаток
        if self.running is color:                    # если часы этого игрока идут,
            left -= self._timer() - self._since      # вычитаем то, что прошло с момента запуска
        return max(left, 0.0)                        # отрицательного времени не бывает

    def start(self, color: Color) -> None:
        """Запустить часы игрока color (часы предыдущего игрока замораживаются)"""
        self.stop()                                  # сначала фиксируем время прежнего игрока, иначе оно потеряется
        self.running = color                         # теперь идут часы color
        self._since = self._timer()                  # и считаем от этого момента

    def stop(self) -> None:
        """Заморозить часы (например, партия окончена)"""
        if self.running is not None:                 # если что-то шло
            self.left[self.running] = self.remaining(self.running)  # записываем живое значение в остаток
            self.running = None                      # и ни у кого часы больше не идут

    def switch(self) -> None:
        """Ход сделан: время передаётся сопернику"""
        if self.running is not None:                 # до первого хода часы не идут: переключать нечего
            # self.running.opposite вычисляется ДО вызова start, а start внутри делает stop,
            # который замораживает того, кто только что сходил
            self.start(self.running.opposite)

    def flagged(self) -> Color | None:
        """Цвет того, у кого упал флажок (время вышло), иначе None"""
        # флажок падает у того, чьи часы идут и чьё время закончилось
        if self.running is not None and self.remaining(self.running) <= 0:
            return self.running
        return None
