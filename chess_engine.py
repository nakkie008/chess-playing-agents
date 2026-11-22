import random
import chess

# shared game-engine helpers built on python-chess
# the gui and the match harness use these instead of touching the rules directly

# creates a new chess game in the standard starting position
def create_board():
    return chess.Board()

# displays the current board in the terminal
def display_board(board):
    print(board)

# returns all legal moves for the current position
def get_legal_moves(board):
    return list(board.legal_moves)

# plays a move after checking it is legal, raises a value error otherwise
def make_move(board, move):
    if move is None or move not in board.legal_moves:
        raise ValueError(f"Illegal move: {move}")

    board.push(move)

# returns true if the game is over, including claimable draws
def is_game_over(board):
    return board.is_game_over(claim_draw=True)

# returns (result string, winning colour or none, termination name)
def game_result(board):
    outcome = board.outcome(claim_draw=True)

    if outcome is None:
        return "*", None, "UNFINISHED"

    return outcome.result(), outcome.winner, outcome.termination.name

# plays up to the given number of random legal moves and returns them as san strings
# the match harness uses this so repeated games do not start from the same position
def play_random_opening(board, plies, rng=None):
    rng = rng or random
    played = []

    for _ in range(plies):
        if is_game_over(board):
            break

        move = rng.choice(get_legal_moves(board))
        played.append(board.san(move))
        make_move(board, move)

    return played

if __name__ == "__main__":
    board = create_board()

    print("Initial Chessboard:")
    display_board(board)

    print("\nLegal Moves:")
    print(get_legal_moves(board))