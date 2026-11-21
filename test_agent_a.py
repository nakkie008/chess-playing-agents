import chess
from agent_a import defensive_move, evaluate_defensive

board = chess.Board()
print("Initial evaluation:", evaluate_defensive(board))

move = defensive_move(board, depth=2)
print("Defensive AI selected:", move)

board.push(move)
print(board)
print("New evaluation:", evaluate_defensive(board))
