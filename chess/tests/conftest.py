import pytest
from tools.board import Board


@pytest.fixture
def board():
    return Board()