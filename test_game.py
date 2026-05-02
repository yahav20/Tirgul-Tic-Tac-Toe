import pytest
from server import Game

@pytest.fixture
def game():
    """
    Fixture that creates a new game instance before each test.
    Ensures each test runs in a clean environment without dependencies.
    """
    g = Game()
    g.started = True # Simulate that the game has started to allow moves
    return g

def test_initial_state(game):
    """Check that the game is initialized correctly"""
    assert game.current_turn == 0
    assert game.started is True
    assert game.game_over is False
    assert game.board[0][0] == ''

