import argparse
import csv
import random
import time

import chess

from chess_engine import create_board, make_move, is_game_over, game_result, play_random_opening
from minimax import get_best_move
from agent_a import defensive_move
from agent_b import aggressive_move

# agent-vs-agent match harness
# plays a fixed number of games with alternating colours and logs every move (san),
# the result, the termination reason, the game length and the thinking time to a csv file
# games differ from each other through a few random opening moves and a random
# choice among equally scored moves, and everything is seeded so a match is reproducible
# both colour assignments of a pair of games (1 and 2, 3 and 4, ...) share the same
# random opening, which keeps the colour comparison fair
#
# usage:
#   python match_harness.py                    defensive vs aggressive
#   python match_harness.py --games 20 --depth 2 --seed 1
#   python match_harness.py --reference        each agent vs the material-only reference

# basic reference agent: minimax with a material-only evaluation
def reference_move(board, depth=2):
    return get_best_move(board, depth)


AGENTS = {
    "Defensive": defensive_move,
    "Aggressive": aggressive_move,
    "Reference": reference_move,
}

CSV_HEADER = ["Game", "White", "Black", "Result", "Winner", "Termination",
              "Plies", "White_sec", "Black_sec", "Moves"]


# plays one game and returns a dict that describes it
def play_game(white_name, black_name, depth, opening_plies, opening_seed, game_seed):
    agents = {chess.WHITE: AGENTS[white_name], chess.BLACK: AGENTS[black_name]}

    # seeds the random tie-breaking inside the search
    random.seed(game_seed)

    board = create_board()
    moves = play_random_opening(board, opening_plies, random.Random(opening_seed))
    seconds = {chess.WHITE: 0.0, chess.BLACK: 0.0}

    # moves already holds the random opening in san, the agents' moves follow
    while not is_game_over(board):
        side = board.turn

        start = time.perf_counter()
        move = agents[side](board, depth)
        seconds[side] += time.perf_counter() - start

        if move is None or move not in board.legal_moves:
            raise ValueError(f"Agent returned an invalid move: {move}")

        moves.append(board.san(move))
        make_move(board, move)

    result, winner_colour, termination = game_result(board)

    if winner_colour is None:
        winner = "Draw"
    else:
        winner = white_name if winner_colour == chess.WHITE else black_name

    return {
        "result": result,
        "winner": winner,
        "termination": termination,
        "moves": moves,
        "white_sec": seconds[chess.WHITE],
        "black_sec": seconds[chess.BLACK],
    }

# plays the given number of games between name_a and name_b and returns the tally
# name_a plays white in odd-numbered games and name_b plays white in even-numbered games
def run_match(name_a="Defensive", name_b="Aggressive", number_of_games=20, depth=2,
              opening_plies=4, seed=1, output="match_results.csv"):
    results = {name_a: 0, name_b: 0, "Draws": 0}

    with open(output, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADER)

        for game_number in range(1, number_of_games + 1):
            if game_number % 2 == 1:
                white, black = name_a, name_b
            else:
                white, black = name_b, name_a

            # games 1 and 2 share pair 1, games 3 and 4 share pair 2, and so on
            pair_index = (game_number + 1) // 2

            print(f"\nStarting game {game_number}: {white} (White) vs {black} (Black)...")

            game = play_game(
                white, black, depth, opening_plies,
                opening_seed=seed * 1000 + pair_index,
                game_seed=seed * 1000 + game_number,
            )

            if game["winner"] == "Draw":
                results["Draws"] += 1
            else:
                results[game["winner"]] += 1

            writer.writerow([
                game_number,
                white,
                black,
                game["result"],
                game["winner"],
                game["termination"],
                len(game["moves"]),
                f"{game['white_sec']:.2f}",
                f"{game['black_sec']:.2f}",
                " ".join(game["moves"]),
            ])
            file.flush()

            print(f"Game {game_number}: {game['winner']} ({game['result']}, "
                  f"{game['termination']}, {len(game['moves'])} plies)")

    print(f"\nFinal match results ({name_a} vs {name_b}, depth {depth}, seed {seed}):")
    print(f"{name_a} wins: {results[name_a]}")
    print(f"{name_b} wins: {results[name_b]}")
    print(f"Draws: {results['Draws']}")
    print(f"Points: {name_a} {results[name_a] + results['Draws'] / 2} - "
          f"{name_b} {results[name_b] + results['Draws'] / 2}")

    return results

# reads the command-line options and runs the requested match
def main():
    parser = argparse.ArgumentParser(description="Run a chess agent match.")
    parser.add_argument("--games", type=int, default=20, help="number of games (default 20)")
    parser.add_argument("--depth", type=int, default=2, help="search depth in plies (default 2)")
    parser.add_argument("--opening-plies", type=int, default=4,
                        help="random opening plies per game (default 4, 0 disables)")
    parser.add_argument("--seed", type=int, default=1, help="random seed (default 1)")
    parser.add_argument("--output", default="match_results.csv", help="csv output file")
    parser.add_argument("--reference", action="store_true",
                        help="play each agent against the material-only reference agent")
    args = parser.parse_args()

    if args.reference:
        for name in ("Defensive", "Aggressive"):
            run_match(name, "Reference", args.games, args.depth, args.opening_plies,
                      args.seed, f"match_results_{name.lower()}_vs_reference.csv")
    else:
        run_match("Defensive", "Aggressive", args.games, args.depth, args.opening_plies,
                  args.seed, args.output)

if __name__ == "__main__":
    main()