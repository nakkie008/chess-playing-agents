import chess

def create_board():
    return chess.Board()

def display_board(board):
    print(board)

def get_legal_moves(board):
    return list(board.legal_moves)


if __name__ == "__main__":
    board = create_board()

    print("Initial Chessboard:")
    display_board(board)

    print("\nLegal Moves:")
    print(get_legal_moves(board))
