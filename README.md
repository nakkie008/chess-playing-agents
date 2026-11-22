# Chess-Playing Agent (Minimax + Alpha-Beta)

This project implements two chess agents share one Minimax search with alpha-beta pruning but use different evaluation strategies. It includes a Tkinter GUI and an agent-vs-agent match harness.

## Authors and agents

| Agent | Strategy | File | Built by |
|---|---|---|---|
| Agent A | Defensive: king safety, piece safety, development, pawn structure | `agent_a.py` | [620154625] |
| Agent B | Aggressive: piece activity, attacks, pawn advancement, pressure on the enemy king | `agent_b.py` | [620139183] |

The search (`minimax.py`), engine helpers, GUI and match harness are shared work.

**How the strategies differ:** Agent A looks inward: it rewards a castled king with a pawn shield, protected pieces, developed minor pieces and sound pawns, and measures no activity. Agent B looks outward: it rewards mobile pieces, attacks on enemy pieces, advanced pawns, pressure around the enemy king and giving check, and has no castling or pawn-shield terms. Both start from the same material count.

## Requirements

- Python 3.8 or later
- `python-chess` (imported as `chess`)
- Tkinter (bundled with most Python installs; on Debian/Ubuntu: `sudo apt install python3-tk`)

```
pip install -r requirements.txt
```

## Running

**GUI:**

```
python main.py
```

- **Game mode:** Human vs Defensive, Human vs Aggressive, Defensive vs Aggressive (Defensive plays White). Changing the mode starts a new game.
- **Play as:** White or Black (human modes). The board flips when you play Black.
- **Depth:** search depth (1-4 plies) for each agent, changeable at any time; higher is stronger but slower.
- **Moving:** click a piece, then its destination. Click another of your pieces to switch selection. Castle by moving the king two squares. A dialog asks which piece to promote to.
- **Agent vs agent:** moves play automatically; **Pause/Resume** and **Step** (one move at a time) are available. The last move is highlighted.

**Match harness:**

```
python match_harness.py                    # Defensive vs Aggressive, 20 games, depth 2
python match_harness.py --games 10 --depth 3 --seed 7
python match_harness.py --reference        # each agent vs a material-only reference agent
```

Options: `--games`, `--depth`, `--opening-plies` (random opening moves per game, default 4), `--seed`, `--output`. Colours alternate every game, and the two games of each pair share the same random opening so the colour comparison stays fair. Equal-scoring moves are chosen at random, so games differ; the seed makes a whole match reproducible.

The CSV has one row per game: `Game, White, Black, Result, Winner, Termination, Plies, White_sec, Black_sec, Moves` (`Moves` is the SAN move list, including the random opening).

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Entry point for the GUI |
| `gui.py` | Tkinter interface, game modes, depth controls |
| `minimax.py` | Piece values, material evaluation, move ordering, minimax with alpha-beta pruning, move selection |
| `agent_a.py` | Defensive evaluation and `defensive_move` |
| `agent_b.py` | Aggressive evaluation and `aggressive_move` |
| `chess_engine.py` | Board creation, move validation, game result, random openings |
| `match_harness.py` | Agent-vs-agent match runner and reference-agent matches |
| `requirements.txt` | Dependencies |

## Deliverables

- `Documentation.docx`: minimax, alpha-beta pruning and the strategy comparison
- `Match_Report.docx`: agent-vs-agent results with analysis (re-run the match with the updated code and refresh the numbers before submitting)