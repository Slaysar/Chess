from tools.clock import Clock
from tools.color import Color


class FakeTimer:
    """Время, которым управляет тест: объект вызывается как функция и возвращает now,
    а тест сам меняет now. Так тесты не ждут настоящих секунд и не зависят от скорости машины."""
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def make(seconds=300):
    # часы с управляемым таймером; возвращаем и часы, и таймер, чтобы тест мог «перематывать» время
    timer = FakeTimer()
    return Clock(seconds, timer=timer), timer


def test_clock_does_not_run_before_first_move():
    # пока часы не запущены, время не уходит и флажка нет, хоть бы прошло 100 секунд
    clock, timer = make()
    timer.now = 100
    assert clock.remaining(Color.WHITE) == 300
    assert clock.running is None
    assert clock.flagged() is None


def test_running_clock_counts_down_only_for_current_player():
    # время уходит только у того, чьи часы запущены
    clock, timer = make()
    clock.start(Color.BLACK)
    timer.now = 40
    assert clock.remaining(Color.BLACK) == 260   # 300 - 40
    assert clock.remaining(Color.WHITE) == 300   # у второго без изменений


def test_switch_freezes_old_and_starts_new():
    # после switch время первого заморожено, второй начинает тратить своё
    clock, timer = make()
    clock.start(Color.BLACK)
    timer.now = 30
    clock.switch()
    timer.now = 50
    assert clock.running is Color.WHITE
    assert clock.remaining(Color.BLACK) == 270   # потратил 30 секунд и остановился
    assert clock.remaining(Color.WHITE) == 280   # идёт с 30-й секунды: 50 - 30 = 20 потрачено


def test_flagged_when_time_is_out():
    # флажок падает ровно когда время закончилось
    clock, timer = make(10)
    clock.start(Color.WHITE)
    timer.now = 9.9
    assert clock.flagged() is None
    timer.now = 10
    assert clock.flagged() is Color.WHITE
    assert clock.remaining(Color.WHITE) == 0     # в минус не уходит


def test_stop_freezes_clock():
    # после stop время больше не идёт и флажок упасть не может
    clock, timer = make()
    clock.start(Color.WHITE)
    timer.now = 20
    clock.stop()
    timer.now = 500
    assert clock.remaining(Color.WHITE) == 280
    assert clock.flagged() is None
