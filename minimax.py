import chess
import math


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}


def evaluate_board(board):
    """Evaluate the material balance from White's perspective."""

    score = 0

    for piece_type, value in PIECE_VALUES.items():
        white_count = len(board.pieces(piece_type, chess.WHITE))
        black_count = len(board.pieces(piece_type, chess.BLACK))

        score += value * (white_count - black_count)

    return score


def minimax(board, depth, alpha, beta, maximizing, evaluate):
    """Search possible moves using Minimax and Alpha Beta pruning."""

    if board.is_game_over(claim_draw=True):
        outcome = board.outcome(claim_draw=True)

        if outcome.winner is None:
            return 0

        return 100000 if outcome.winner == chess.WHITE else -100000

    if depth == 0:
        return evaluate(board)

    if maximizing:
        best_score = -math.inf

        for move in board.legal_moves:
            board.push(move)

            score = minimax(
                board, depth - 1, alpha, beta, False, evaluate
            )

            board.pop()

            best_score = max(best_score, score)
            alpha = max(alpha, best_score)

            if beta <= alpha:
                break

        return best_score

    else:
        best_score = math.inf

        for move in board.legal_moves:
            board.push(move)

            score = minimax(
                board, depth - 1, alpha, beta, True, evaluate
            )

            board.pop()

            best_score = min(best_score, score)
            beta = min(beta, best_score)

            if beta <= alpha:
                break

        return best_score


def get_best_move(board, depth, evaluate=evaluate_board):
    """Choose the best legal move for the current player."""

    best_move = None

    maximizing = board.turn == chess.WHITE

    best_score = -math.inf if maximizing else math.inf

    for move in board.legal_moves:
        board.push(move)

        score = minimax(
            board,
            depth - 1,
            -math.inf,
            math.inf,
            not maximizing,
            evaluate
        )

        board.pop()

        if maximizing and score > best_score:
            best_score = score
            best_move = move

        elif not maximizing and score < best_score:
            best_score = score
            best_move = move

    return best_move