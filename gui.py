import queue
import threading
import tkinter as tk
from tkinter import ttk, font as tkfont

import chess

from chess_engine import create_board, make_move, is_game_over, game_result
from agent_a import defensive_move
from agent_b import aggressive_move

# tkinter gui: human vs agent and agent vs agent play on a visual board
# the user picks the mode, the human's colour and each agent's search depth
# the board highlights the last move, a dialog offers the promotion choice,
# and agent-vs-agent mode has pause, resume and single-step controls
# agents think on a background thread so the window stays responsive

AGENTS = {"Defensive": defensive_move, "Aggressive": aggressive_move}
MODES = [
    "Human vs Defensive",
    "Human vs Aggressive",
    "Defensive vs Aggressive",
]
GLYPHS = {
    "P": "\u2659", "N": "\u2658", "B": "\u2657", "R": "\u2656", "Q": "\u2655", "K": "\u2654",
    "p": "\u265f", "n": "\u265e", "b": "\u265d", "r": "\u265c", "q": "\u265b", "k": "\u265a",
}
LIGHT, DARK, SELECTED, LAST_MOVE = "#EEEED2", "#769656", "#F6F669", "#BACA44"
MIN_DEPTH, MAX_DEPTH = 1, 4

# width of each board square in text units, a larger number makes the board wider
SQUARE_WIDTH = 4


class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess AI - Minimax with Alpha-Beta Pruning")

        self.board = create_board()
        self.selected_square = None
        self.last_move = None

        # increases on every new game so stale agent results get dropped
        self.game_id = 0
        self.thinking = False
        self.paused = False
        self.pending_job = None
        self.buttons = {}

        self.mode = tk.StringVar(value=MODES[0])
        self.human_colour = tk.StringVar(value="White")
        self.depths = {"Defensive": tk.IntVar(value=2), "Aggressive": tk.IntVar(value=2)}
        self.pause_text = tk.StringVar(value="Pause")
        self.piece_font = self.pick_font()

        # the controls sit on the left and the board sits on the right,
        # so the window stays short enough to show the whole board
        self.left_panel = ttk.Frame(root)
        self.left_panel.pack(side="left", anchor="n", padx=8, pady=8)

        self.right_panel = ttk.Frame(root)
        self.right_panel.pack(side="left", padx=8, pady=8)

        self.build_controls()

        self.status = tk.Label(self.right_panel, text="White to move", font=("Arial", 14))
        self.status.pack(pady=(0, 6))

        self.board_frame = tk.Frame(self.right_panel)
        self.board_frame.pack()

        self.new_game()

    # ---------- layout ----------

    # chooses an installed font that draws the chess symbols
    def pick_font(self):
        installed = set(tkfont.families())

        for name in ("Segoe UI Symbol", "DejaVu Sans", "Arial Unicode MS", "Apple Symbols"):
            if name in installed:
                return (name, 28)

        return ("TkDefaultFont", 28)

    # builds the mode, colour and depth selectors and the control buttons
    # the widgets stack vertically in the left panel
    def build_controls(self):
        frame = ttk.Frame(self.left_panel)
        frame.pack(anchor="w")

        ttk.Label(frame, text="Game mode").grid(row=0, column=0, sticky="w", pady=(0, 2))
        mode_box = ttk.Combobox(
            frame, textvariable=self.mode, values=MODES, state="readonly", width=24
        )
        mode_box.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))
        mode_box.bind("<<ComboboxSelected>>", lambda e: self.new_game())

        ttk.Label(frame, text="Play as").grid(row=2, column=0, sticky="w", pady=2)
        self.colour_box = ttk.Combobox(
            frame, textvariable=self.human_colour, values=["White", "Black"],
            state="readonly", width=8
        )
        self.colour_box.grid(row=2, column=1, sticky="w", padx=6, pady=2)
        self.colour_box.bind("<<ComboboxSelected>>", lambda e: self.new_game())

        ttk.Label(frame, text="Defensive depth").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Spinbox(
            frame, from_=MIN_DEPTH, to=MAX_DEPTH, width=4,
            textvariable=self.depths["Defensive"]
        ).grid(row=3, column=1, sticky="w", padx=6, pady=2)

        ttk.Label(frame, text="Aggressive depth").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Spinbox(
            frame, from_=MIN_DEPTH, to=MAX_DEPTH, width=4,
            textvariable=self.depths["Aggressive"]
        ).grid(row=4, column=1, sticky="w", padx=6, pady=2)

        ttk.Button(frame, text="New Game", command=self.new_game).grid(
            row=5, column=0, columnspan=2, sticky="we", pady=(12, 2)
        )

        self.pause_button = ttk.Button(
            frame, textvariable=self.pause_text, command=self.toggle_pause
        )
        self.pause_button.grid(row=6, column=0, columnspan=2, sticky="we", pady=2)

        self.step_button = ttk.Button(frame, text="Step", command=self.step)
        self.step_button.grid(row=7, column=0, columnspan=2, sticky="we", pady=2)

    # ---------- mode helpers ----------

    # returns true when both sides are agents
    def is_agent_vs_agent(self):
        return not self.mode.get().startswith("Human")

    # returns the colour the human plays
    def human_color(self):
        return chess.WHITE if self.human_colour.get() == "White" else chess.BLACK

    # returns the name of the agent that plays the side to move
    def agent_name_to_move(self):
        parts = self.mode.get().split(" vs ")

        if self.is_agent_vs_agent():
            return parts[0] if self.board.turn == chess.WHITE else parts[1]

        return parts[1]

    # returns the search depth chosen for an agent, kept within the allowed range
    def depth_for(self, name):
        try:
            return max(MIN_DEPTH, min(MAX_DEPTH, int(self.depths[name].get())))
        except (tk.TclError, ValueError):
            return 2

    # enables or disables the controls that only apply to one kind of mode
    def update_controls(self):
        ava = self.is_agent_vs_agent()

        self.colour_box.config(state="disabled" if ava else "readonly")

        state = "normal" if ava else "disabled"
        self.pause_button.config(state=state)
        self.step_button.config(state=state)

        self.pause_text.set("Resume" if self.paused else "Pause")

    # ---------- drawing ----------

    # draws the board, flipped when the human plays black
    def draw_board(self):
        flipped = (not self.is_agent_vs_agent()) and self.human_color() == chess.BLACK

        for rank in range(8):
            for file in range(8):
                square = chess.square(file, rank)

                if square not in self.buttons:
                    self.buttons[square] = tk.Button(
                        self.board_frame,
                        font=self.piece_font,
                        width=SQUARE_WIDTH,
                        height=1,
                        command=lambda s=square: self.click_square(s),
                    )

                row = rank if flipped else 7 - rank
                col = 7 - file if flipped else file
                self.buttons[square].grid(row=row, column=col)

                color = LIGHT if (rank + file) % 2 else DARK

                if self.last_move and square in (self.last_move.from_square, self.last_move.to_square):
                    color = LAST_MOVE

                if square == self.selected_square:
                    color = SELECTED

                piece = self.board.piece_at(square)
                symbol = GLYPHS[piece.symbol()] if piece else ""
                self.buttons[square].config(text=symbol, bg=color)

    # updates the status line with the turn, check, thinking state or final result
    def update_status(self):
        if is_game_over(self.board):
            result, _, termination = game_result(self.board)
            text = f"Game over: {result} ({termination.replace('_', ' ').title()})"
        else:
            side = "White" if self.board.turn == chess.WHITE else "Black"

            if self.thinking:
                text = f"{self.agent_name_to_move()} ({side}) is thinking..."
            else:
                text = f"{side} to move" + (" - check!" if self.board.is_check() else "")

        self.status.config(text=text)

    # ---------- human input ----------

    # handles a click on a square: selects a piece or plays the selected piece there
    def click_square(self, square):
        if (self.is_agent_vs_agent() or self.thinking or is_game_over(self.board)
                or self.board.turn != self.human_color()):
            return

        piece = self.board.piece_at(square)

        # the first click, or a click on another own piece, selects that piece
        if self.selected_square is None or (piece and piece.color == self.human_color()):
            if piece and piece.color == self.human_color():
                self.selected_square = square
                self.draw_board()
            return

        move = self.build_move(self.selected_square, square)
        self.selected_square = None

        if move in self.board.legal_moves:
            self.apply_move(move)

            if not is_game_over(self.board):
                self.schedule_ai_move()
        else:
            self.draw_board()

    # creates the move and asks for the promotion piece when a pawn reaches the last rank
    def build_move(self, from_square, to_square):
        piece = self.board.piece_at(from_square)
        move = chess.Move(from_square, to_square)
        last_rank = 7 if self.board.turn == chess.WHITE else 0

        if piece and piece.piece_type == chess.PAWN and chess.square_rank(to_square) == last_rank:
            queen_move = chess.Move(from_square, to_square, promotion=chess.QUEEN)

            if queen_move in self.board.legal_moves:
                move = chess.Move(from_square, to_square, promotion=self.ask_promotion())

        return move

    # shows a small modal dialog to choose the promotion piece
    def ask_promotion(self):
        choice = {"piece": chess.QUEEN}

        win = tk.Toplevel(self.root)
        win.title("Promote pawn to")
        win.transient(self.root)
        win.resizable(False, False)

        def pick(piece):
            choice["piece"] = piece
            win.destroy()

        for name, piece in (("Queen", chess.QUEEN), ("Rook", chess.ROOK),
                            ("Bishop", chess.BISHOP), ("Knight", chess.KNIGHT)):
            ttk.Button(win, text=name, command=lambda p=piece: pick(p)).pack(
                side="left", padx=4, pady=8
            )

        win.wait_visibility()
        win.grab_set()
        self.root.wait_window(win)

        return choice["piece"]

    # plays a move on the board and refreshes the display
    def apply_move(self, move):
        make_move(self.board, move)
        self.last_move = move
        self.selected_square = None
        self.draw_board()
        self.update_status()

    # ---------- agent moves ----------

    # cancels the agent move that waits to start
    def cancel_pending(self):
        if self.pending_job is not None:
            self.root.after_cancel(self.pending_job)
            self.pending_job = None

    # starts the next agent move shortly, so the board redraws first
    def schedule_ai_move(self):
        if self.thinking or self.pending_job is not None or is_game_over(self.board):
            return

        self.pending_job = self.root.after(300, self.start_ai_thinking)

    # runs the agent on a background thread and polls for its answer
    def start_ai_thinking(self):
        self.pending_job = None

        if self.thinking or is_game_over(self.board):
            return

        name = self.agent_name_to_move()
        agent = AGENTS[name]
        depth = self.depth_for(name)

        # the worker thread searches a copy, so it never touches the live board
        board_copy = self.board.copy()
        results = queue.Queue()
        game_id = self.game_id

        self.thinking = True
        self.update_status()

        def work():
            results.put(agent(board_copy, depth))

        threading.Thread(target=work, daemon=True).start()
        self.poll_ai(results, game_id)

    # checks whether the agent has answered and plays its move when it has
    def poll_ai(self, results, game_id):
        # a new game started in the meantime, so the result is dropped
        if game_id != self.game_id:
            return

        try:
            move = results.get_nowait()
        except queue.Empty:
            self.root.after(50, lambda: self.poll_ai(results, game_id))
            return

        self.thinking = False

        if move is not None and move in self.board.legal_moves:
            self.apply_move(move)

        self.update_status()

        if self.is_agent_vs_agent() and not self.paused and not is_game_over(self.board):
            self.schedule_ai_move()

    # ---------- controls ----------

    # pauses or resumes the agent-vs-agent game
    def toggle_pause(self):
        if not self.is_agent_vs_agent():
            return

        self.paused = not self.paused
        self.update_controls()

        if self.paused:
            self.cancel_pending()
        else:
            self.schedule_ai_move()

    # plays exactly one agent move in agent-vs-agent mode
    def step(self):
        if not self.is_agent_vs_agent() or self.thinking or is_game_over(self.board):
            return

        self.cancel_pending()
        self.start_ai_thinking()

    # resets the board and starts the agents when they play first
    def new_game(self):
        self.cancel_pending()

        # invalidates any move that an agent still computes
        self.game_id += 1
        self.thinking = False
        self.paused = False
        self.board = create_board()
        self.selected_square = None
        self.last_move = None

        self.update_controls()
        self.draw_board()
        self.update_status()

        if self.is_agent_vs_agent():
            self.schedule_ai_move()
        # the agent opens when the human plays black
        elif self.board.turn != self.human_color():
            self.schedule_ai_move()