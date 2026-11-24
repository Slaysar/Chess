from tools.clock import Clock
from tools.color import Color


class FakeTimer:
    """Время, которым управляет тест"""
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def make(seconds=300):
    timer = FakeTimer()
    return Clock(seconds, timer=timer), timer


def test_clock_does_not_run_before_first_move():
    clock, timer = make()
    timer.now = 100
    assert clock.remaining(Color.WHITE) == 300
    assert clock.running is None
    assert clock.flagged() is None


def test_running_clock_counts_down_only_for_current_player():
    clock, timer = make()
    clock.start(Color.BLACK)
    timer.now = 40
    assert clock.remaining(Color.BLACK) == 260
    assert clock.remaining(Color.WHITE) == 300


def test_switch_freezes_old_and_starts_new():
    clock, timer = make()
    clock.start(Color.BLACK)
    timer.now = 30
    clock.switch()
    timer.now = 50
    assert clock.running is Color.WHITE
    assert clock.remaining(Color.BLACK) == 270
    assert clock.remaining(Color.WHITE) == 280


def test_flagged_when_time_is_out():
    clock, timer = make(10)
    clock.start(Color.WHITE)
    timer.now = 9.9
    assert clock.flagged() is None
    timer.now = 10
    assert clock.flagged() is Color.WHITE
    assert clock.remaining(Color.WHITE) == 0


def test_stop_freezes_clock():
    clock, timer = make()
    clock.start(Color.WHITE)
    timer.now = 20
    clock.stop()
    timer.now = 500
    assert clock.remaining(Color.WHITE) == 280
    assert clock.flagged() is None