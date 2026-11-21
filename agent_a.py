import chess
from minimax import get_best_move, PIECE_VALUES

def evaluate_defensive(board):
    score = 0

    for color in [chess.WHITE, chess.BLACK]:

        sign = 1 if color == chess.WHITE else -1

        # 1. Material evaluation
        for piece_type, value in PIECE_VALUES.items():
            count = len(board.pieces(piece_type, color))
            score += sign * count * value

        # 2. King safety
        king_square = board.king(color)

        if king_square is not None:
            king_file = chess.square_file(king_square)
            king_rank = chess.square_rank(king_square)

            home_rank = 0 if color == chess.WHITE else 7

            # Reward a king in a typical castled position
            if king_rank == home_rank and king_file in [2, 6]:
                score += sign * 60

            # Penalize an exposed king in the centre
            if king_file in [3, 4] and king_rank != home_rank:
                score -= sign * 50

            # Reward friendly pawns defending the king's square
            for square in board.attackers(color, king_square):
                piece = board.piece_at(square)

                if piece and piece.piece_type == chess.PAWN:
                    score += sign * 15
        # 3. Pawn structure
        pawns = board.pieces(chess.PAWN, color)

        for square in pawns:
            file = chess.square_file(square)

            # Penalize doubled pawns
            same_file = [
                p for p in pawns
                if chess.square_file(p) == file
            ]

            if len(same_file) > 1:
                score -= sign * 10

            # Reward pawns with friendly pawns on adjacent files
            adjacent_pawns = [
                p for p in pawns
                if abs(chess.square_file(p) - file) == 1
            ]

            if adjacent_pawns:
                score += sign * 5

    return score


def defensive_move(board, depth=2):
    return get_best_move(board, depth, evaluate_defensive)