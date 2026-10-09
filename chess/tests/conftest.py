import pytest

from game import Game
from tools.board import Board


@pytest.fixture
def board():
    return Board()


@pytest.fixture
def game():
    return Game()


@pytest.fixture
def empty_game():
    game = Game()
    game.board.clear()
    return game
