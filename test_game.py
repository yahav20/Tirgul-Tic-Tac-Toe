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

def test_valid_move(game):
    """Check a valid move and turn switching"""
    success, msg = game.make_move(player=0, row=1, col=1)
    assert success is True
    assert game.board[1][1] == 'X'
    assert game.current_turn == 1 # Turn should pass to the second player

def test_out_of_bounds_move(game):
    """Edge case check: move outside board boundaries"""
    success, msg = game.make_move(player=0, row=3, col=0)
    assert success is False
    assert msg == "Out of bounds"

def test_wrong_turn(game):
    """Check that a player cannot play out of turn"""
    # Player 0 plays first (valid)
    game.make_move(player=0, row=0, col=0)
    # Player 0 tries to play again consecutively (invalid)
    success, msg = game.make_move(player=0, row=0, col=1)
    assert success is False
    assert msg == "Not your turn"

def test_winning_condition(game):
    """Check that the win algorithm detects a winning row"""
    game.make_move(player=0, row=0, col=0) # X
    game.make_move(player=1, row=1, col=0) # O
    game.make_move(player=0, row=0, col=1) # X
    game.make_move(player=1, row=1, col=1) # O
    game.make_move(player=0, row=0, col=2) # X wins on the top row
    
    winner = game.check_winner()
    assert winner == 'X'
    assert game.game_over is True

def test_overwrite_self(game):
    # Player 0 places X in the center
    game.make_move(player=1, row=1, col=1)
    # Player 1 tries to place O in the exact same cell
    success, msg = game.make_move(player=1, row=1, col=1)
    assert success is False, "Expected move to fail due to occupied cell"
    assert game.board[1][1] == 'X' # Original symbol should remain
    
def test_overwrite_cell_bug(game):
    # Player 0 places X in the center
    game.make_move(player=0, row=1, col=1)
    # Player 1 tries to place O in the exact same cell
    success, msg = game.make_move(player=1, row=1, col=1)
    assert success is False, "Expected move to fail due to occupied cell"
    assert game.board[1][1] == 'X' # Original symbol should remain