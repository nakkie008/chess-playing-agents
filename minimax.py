import math
import random

import chess

# shared search code: piece values, material evaluation, minimax with
# alpha-beta pruning, move ordering and move selection
# scores are always from white's point of view (positive favours white)

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# score magnitude of a checkmate
# the remaining depth is added so faster mates score higher
# and slower losses score better than distant ones
MATE_SCORE = 100000

# counts the positions minimax visits since the last reset_stats call
_stats = {"nodes": 0}

# resets the visited-node counter
def reset_stats():
    _stats["nodes"] = 0

# returns how many nodes minimax visits since the last reset_stats call
def node_count():
    return _stats["nodes"]

# evaluates the material balance from white's perspective
# this is also the evaluation of the reference agent
def evaluate_board(board):
    score = 0

    for piece_type, value in PIECE_VALUES.items():
        white_count = len(board.pieces(piece_type, chess.WHITE))
        black_count = len(board.pieces(piece_type, chess.BLACK))
        score += value * (white_count - black_count)

    return score

# returns the legal moves sorted so the promising ones come first
# captures (valuable victim, cheap attacker first), promotions and checks
# come before quiet moves, which lets alpha-beta cut off far more branches
# the sort is stable, so equal moves keep the library's generation order
def order_moves(board):
    def priority(move):
        score = 0

        if board.is_capture(move):
            victim = board.piece_type_at(move.to_square)

            # en passant has no piece on the target square, the victim is a pawn
            if victim is None:
                victim = chess.PAWN

            attacker = board.piece_type_at(move.from_square)
            score += 10 * PIECE_VALUES[victim] - PIECE_VALUES[attacker]

        if move.promotion:
            score += PIECE_VALUES[move.promotion]

        if board.gives_check(move):
            score += 50

        return -score

    return sorted(board.legal_moves, key=priority)

# searches possible moves using minimax and alpha-beta pruning
# alpha is the best score the maximiser already guarantees on this path
# beta is the best score the minimiser already guarantees on this path
# when beta <= alpha the remaining moves cannot change the decision, so they are skipped
# prune=False searches the full tree, which the test uses to check the pruning
def minimax(board, depth, alpha, beta, maximizing, evaluate, prune=True):
    _stats["nodes"] += 1

    if board.is_game_over(claim_draw=True):
        outcome = board.outcome(claim_draw=True)

        if outcome is None or outcome.winner is None:
            return 0

        mate = MATE_SCORE + depth
        return mate if outcome.winner == chess.WHITE else -mate

    if depth == 0:
        return evaluate(board)

    if maximizing:
        best_score = -math.inf

        for move in order_moves(board):
            board.push(move)

            score = minimax(
                board, depth - 1, alpha, beta, False, evaluate, prune
            )

            board.pop()

            best_score = max(best_score, score)
            alpha = max(alpha, best_score)

            if prune and beta <= alpha:
                break

        return best_score

    else:
        best_score = math.inf

        for move in order_moves(board):
            board.push(move)

            score = minimax(
                board, depth - 1, alpha, beta, True, evaluate, prune
            )

            board.pop()

            best_score = min(best_score, score)
            beta = min(beta, best_score)

            if prune and beta <= alpha:
                break

        return best_score

# returns (move, score) for the side to move
# the best score so far passes down as the alpha (white) or beta (black) bound
# for each later root move, so pruning works from the first level
# the bound widens by 1 so moves that tie the best score still get an exact score
# (all scores are integers), then one of the tied moves is picked at random
# which stops the agents from replaying identical games
def search_best_move(board, depth, evaluate=evaluate_board, prune=True, rng=None):
    if depth < 1:
        raise ValueError("depth must be at least 1")

    rng = rng or random

    maximizing = board.turn == chess.WHITE
    best_score = -math.inf if maximizing else math.inf
    best_moves = []

    for move in order_moves(board):
        board.push(move)

        if not prune:
            alpha, beta = -math.inf, math.inf
        elif maximizing:
            alpha, beta = best_score - 1, math.inf
        else:
            alpha, beta = -math.inf, best_score + 1

        score = minimax(
            board, depth - 1, alpha, beta, not maximizing, evaluate, prune
        )

        board.pop()

        if score == best_score:
            best_moves.append(move)
        elif (maximizing and score > best_score) or (not maximizing and score < best_score):
            best_score = score
            best_moves = [move]

    if not best_moves:
        return None, best_score

    return rng.choice(best_moves), best_score

# chooses the best legal move for the current player, or none if there is no move
# depth is the number of plies searched, including the agent's own move
def get_best_move(board, depth, evaluate=evaluate_board, prune=True, rng=None):
    move, _ = search_best_move(board, depth, evaluate, prune, rng)
    return move