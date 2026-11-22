#ID: 620154625
import chess
from minimax import get_best_move, evaluate_board, PIECE_VALUES

# agent a: the defensive strategy
# a position is good when it is safe and well structured
# the agent values a castled king with a pawn shield, protected pieces,
# developed minor pieces and a healthy pawn structure
# it does not measure piece activity or attacking chances

# starting squares of the knights and bishops for each colour
MINOR_START_SQUARES = {
    chess.WHITE: (chess.B1, chess.C1, chess.F1, chess.G1),
    chess.BLACK: (chess.B8, chess.C8, chess.F8, chess.G8),
}

# scores king safety: castled-king bonus, centre-king penalty,
# castling rights and the pawn shield in front of the king
def king_safety(board, color):
    king = board.king(color)

    if king is None:
        return 0

    file = chess.square_file(king)
    rank = chess.square_rank(king)
    home_rank = 0 if color == chess.WHITE else 7
    forward = 1 if color == chess.WHITE else -1
    value = 0

    # rewards a king on the typical castled squares
    if rank == home_rank and file in (2, 6):
        value += 60
    # penalises a king that wanders in the centre
    elif file in (3, 4) and rank != home_rank:
        value -= 50

    # rewards keeping the ability to castle
    if board.has_castling_rights(color):
        value += 15

    # rewards friendly pawns directly in front of the king
    for shield_file in (file - 1, file, file + 1):
        if not 0 <= shield_file <= 7:
            continue

        for step, bonus in ((1, 15), (2, 8)):
            shield_rank = rank + forward * step

            if 0 <= shield_rank <= 7:
                piece = board.piece_at(chess.square(shield_file, shield_rank))

                if piece and piece.piece_type == chess.PAWN and piece.color == color:
                    value += bonus

    return value

# penalises pieces that the enemy attacks and nothing defends
def piece_safety(board, color):
    value = 0

    for square, piece in board.piece_map().items():
        if piece.color != color or piece.piece_type == chess.KING:
            continue

        attacked = board.is_attacked_by(not color, square)
        defended = board.is_attacked_by(color, square)

        if attacked and not defended:
            value -= PIECE_VALUES[piece.piece_type] // 10

    return value

# penalises knights and bishops that have not left their starting squares
def development(board, color):
    value = 0

    for square in MINOR_START_SQUARES[color]:
        piece = board.piece_at(square)

        if piece and piece.color == color and piece.piece_type in (chess.KNIGHT, chess.BISHOP):
            value -= 15

    return value

# penalises doubled pawns (-10 per extra pawn) and isolated pawns (-10 each)
def pawn_structure(board, color):
    file_counts = [0] * 8

    for square in board.pieces(chess.PAWN, color):
        file_counts[chess.square_file(square)] += 1

    value = 0

    for file, count in enumerate(file_counts):
        if count == 0:
            continue

        if count > 1:
            value -= 10 * (count - 1)

        left = file_counts[file - 1] if file > 0 else 0
        right = file_counts[file + 1] if file < 7 else 0

        if left == 0 and right == 0:
            value -= 10 * count

    return value

# scores a position from white's perspective
# material plus king safety, piece safety, development and pawn structure for each side
def evaluate_defensive(board):
    score = evaluate_board(board)

    for color in (chess.WHITE, chess.BLACK):
        sign = 1 if color == chess.WHITE else -1

        score += sign * king_safety(board, color)
        score += sign * piece_safety(board, color)
        score += sign * development(board, color)
        score += sign * pawn_structure(board, color)

    return score

# returns the defensive agent's move after searching the given number of plies
def defensive_move(board, depth=2):
    return get_best_move(board, depth, evaluate_defensive)