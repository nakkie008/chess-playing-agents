import chess
from minimax import get_best_move, evaluate_board

# agent b: the aggressive strategy
# a position is good when it creates pressure
# the agent values active pieces, attacks on enemy pieces, advanced pawns,
# pressure around the enemy king and giving check
# it has no castling or pawn-shield terms, its own king is only protected
# indirectly because attackers near either king score for the attacking side

# points per square a piece can move to or capture on (own-occupied squares do not count)
# minor pieces weigh more than the queen, which has many more squares available
ACTIVITY_WEIGHTS = {
    chess.KNIGHT: 4,
    chess.BISHOP: 3,
    chess.ROOK: 2,
    chess.QUEEN: 1,
}
ATTACK_ON_ENEMY_PIECE = 10
PAWN_ADVANCE_PER_RANK = 8
KING_ZONE_PER_ATTACKER = 15
CHECK_BONUS = 50

# scores piece mobility plus a bonus for each attack on an enemy piece
def activity_and_attacks(board, color):
    value = 0

    for square, piece in board.piece_map().items():
        if piece.color != color:
            continue

        mobility = 0

        for target in board.attacks(square):
            occupant = board.piece_at(target)

            if occupant is None:
                mobility += 1
            elif occupant.color != color:
                mobility += 1
                value += ATTACK_ON_ENEMY_PIECE

        value += ACTIVITY_WEIGHTS.get(piece.piece_type, 0) * mobility

    return value

# rewards each rank a pawn has advanced from its own side
def pawn_advancement(board, color):
    value = 0

    for square in board.pieces(chess.PAWN, color):
        rank = chess.square_rank(square)
        advanced = rank if color == chess.WHITE else 7 - rank
        value += advanced * PAWN_ADVANCE_PER_RANK

    return value

# rewards attackers around the enemy king and giving check
def king_attack(board, color):
    enemy_king = board.king(not color)

    if enemy_king is None:
        return 0

    value = 0

    for square in chess.SquareSet(chess.BB_KING_ATTACKS[enemy_king]):
        value += len(board.attackers(color, square)) * KING_ZONE_PER_ATTACKER

    # the enemy is in check when it is their turn and the king is attacked
    if board.is_check() and board.turn != color:
        value += CHECK_BONUS

    return value

# scores a position from white's perspective
# material plus activity, attacks, pawn advancement and king pressure for each side
def evaluate_aggressive(board):
    score = evaluate_board(board)

    for color in (chess.WHITE, chess.BLACK):
        sign = 1 if color == chess.WHITE else -1

        score += sign * activity_and_attacks(board, color)
        score += sign * pawn_advancement(board, color)
        score += sign * king_attack(board, color)

    return score

# returns the aggressive agent's move after searching the given number of plies
def aggressive_move(board, depth=2):
    return get_best_move(board, depth, evaluate_aggressive)