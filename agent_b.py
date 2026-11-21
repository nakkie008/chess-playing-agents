import chess
from minimax import get_best_move, PIECE_VALUES

def evaluate_aggressive(board):
    score = 0

    for color in [chess.WHITE, chess.BLACK]:

        sign = 1 if color == chess.WHITE else -1

        # material evaluation
        for piece_type, value in PIECE_VALUES.items():
            count = len(board.pieces(piece_type, color))
            score += sign * count * value

        # pieces activity and attacking pressure
        for square in board.pieces(chess.QUEEN, color):
            score += sign * len(board.attacks(square)) * 3

        for square in board.pieces(chess.ROOK, color):
            score += sign * len(board.attacks(square)) * 2

        for square in board.pieces(chess.BISHOP, color):
            score += sign * len(board.attacks(square)) * 2

        for square in board.pieces(chess.KNIGHT, color):
            score += sign * len(board.attacks(square)) * 3

        # rewards attacking enemy pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)

            if piece and piece.color == color:
                enemy_targets = board.attacks(square)

                for target in enemy_targets:
                    target_piece = board.piece_at(target)

                    if target_piece and target_piece.color != color:
                        score += sign * 10

        # rewards pawn advancement
        pawns = board.pieces(chess.PAWN, color)

        for square in pawns:
            rank = chess.square_rank(square)

            advancement = rank if color == chess.WHITE else 7 - rank

            score += sign * advancement * 8

        # rewards pressure around the enemy king
        enemy_king = board.king(not color)

        if enemy_king is not None:
            king_zone = chess.SquareSet(chess.BB_KING_ATTACKS[enemy_king])

            for square in king_zone:
                attackers = board.attackers(color, square)
                score += sign * len(attackers) * 15

            # rewards checking the enemy king
            if board.is_check() and board.turn != color:
                score += sign * 50

    return score

def aggressive_move(board, depth=2):
    return get_best_move(board, depth, evaluate_aggressive)
