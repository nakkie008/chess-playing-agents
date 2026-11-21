import chess
from minimax import get_best_move

board = chess.Board()

print("Starting position:")
print(board)

move = get_best_move(board, depth=2)

print("\nAI selected:", move)

board.push(move)

print("\nBoard after AI move:")
print(board)