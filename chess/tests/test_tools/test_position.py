import pytest
from tools.position import Position


def test_from_str():
    assert Position.from_str("e3") == Position(2, 4)


def test_str():
    assert str(Position(2, 4)) == "e3"


@pytest.mark.parametrize("s", ["", "e", "e33", "z1", "a9", "a0"])
def test_from_str_invalid(s):
    with pytest.raises(ValueError):
        Position.from_str(s)


def test_constructor_out_of_board():
    with pytest.raises(ValueError):
        Position(8, 0)


def test_offset_inside():
    assert Position.from_str("e3").offset(1, 0) == Position.from_str("e4")


def test_offset_outside_returns_none():
    assert Position.from_str("a1").offset(-1, 0) is None
    assert Position.from_str("h8").offset(0, 1) is None


def test_hashable_as_dict_key():
    d = {Position(2, 4): "x"}
    assert d[Position.from_str("e3")] == "x"