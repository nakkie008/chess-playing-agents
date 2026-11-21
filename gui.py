import tkinter as tk
from tkinter import ttk
import chess

from Agent1 import defensive_move

try:
    from aggressive_agent import aggressive_move
    AGGRESSIVE_READY = True
except ImportError:
    aggressive_move = defensive_move
    AGGRESSIVE_READY = False


class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("COMP3220 Chess AI")

        self.board = chess.Board()
        self.selected_square = None
        self.ai_depth = 2
        self.pending_job = None

        self.mode = tk.StringVar(value="Human vs Defensive")

        ttk.Label(root, text="Game Mode").pack(pady=5)

        self.mode_selector = ttk.Combobox(
            root,
            textvariable=self.mode,
            values=[
                "Human vs Defensive",
                "Human vs Aggressive",
                "Defensive vs Aggressive"
            ],
            state="readonly",
            width=25
        )
        self.mode_selector.pack(pady=5)
        self.mode_selector.bind("<<ComboboxSelected>>", self.change_mode)

        self.status = tk.Label(
            root,
            text="White to move",
            font=("Arial", 14)
        )
        self.status.pack(pady=10)

        self.board_frame = tk.Frame(root)
        self.board_frame.pack()

        self.buttons = {}

        self.draw_board()

        ttk.Button(
            root,
            text="New Game",
            command=self.new_game
        ).pack(pady=10)

    def draw_board(self):
        pieces = {
            "P": "♙", "N": "♘", "B": "♗",
            "R": "♖", "Q": "♕", "K": "♔",
            "p": "♟", "n": "♞", "b": "♝",
            "r": "♜", "q": "♛", "k": "♚"
        }

        for rank in range(7, -1, -1):
            for file in range(8):
                square = chess.square(file, rank)
                piece = self.board.piece_at(square)

                color = "#EEEED2" if (rank + file) % 2 else "#769656"

                if square == self.selected_square:
                    color = "#F6F669"

                symbol = pieces.get(piece.symbol(), "") if piece else ""

                if square not in self.buttons:
                    button = tk.Button(
                        self.board_frame,
                        font=("Segoe UI Symbol", 28),
                        width=2,
                        height=1,
                        command=lambda s=square: self.click_square(s)
                    )
                    button.grid(row=7-rank, column=file)
                    self.buttons[square] = button

                self.buttons[square].config(
                    text=symbol,
                    bg=color
                )

    def click_square(self, square):
        if self.mode.get() == "Defensive vs Aggressive":
            return

        if self.board.is_game_over(claim_draw=True):
            return

        if self.board.turn != chess.WHITE:
            return

        if self.selected_square is None:
            piece = self.board.piece_at(square)

            if piece and piece.color == chess.WHITE:
                self.selected_square = square
                self.draw_board()
            return

        piece = self.board.piece_at(self.selected_square)

        move = chess.Move(self.selected_square, square)

        if piece and piece.piece_type == chess.PAWN:
            if chess.square_rank(square) == 7:
                move = chess.Move(
                    self.selected_square,
                    square,
                    promotion=chess.QUEEN
                )

        self.selected_square = None

        if move in self.board.legal_moves:
            self.board.push(move)
            self.draw_board()
            self.update_status()

            if not self.board.is_game_over(claim_draw=True):
                self.schedule_ai_move()
        else:
            self.draw_board()

    def schedule_ai_move(self):
        if self.pending_job is not None:
            self.root.after_cancel(self.pending_job)

        self.pending_job = self.root.after(300, self.ai_move)

    def ai_move(self):
        self.pending_job = None

        if self.board.is_game_over(claim_draw=True):
            self.update_status()
            return

        mode = self.mode.get()

        if mode == "Human vs Defensive":
            move = defensive_move(self.board, self.ai_depth)

        elif mode == "Human vs Aggressive":
            move = aggressive_move(self.board, self.ai_depth)

        else:
            if self.board.turn == chess.WHITE:
                move = defensive_move(self.board, self.ai_depth)
            else:
                move = aggressive_move(self.board, self.ai_depth)

        if move is not None and move in self.board.legal_moves:
            self.board.push(move)

        self.draw_board()
        self.update_status()

        if (
            mode == "Defensive vs Aggressive"
            and not self.board.is_game_over(claim_draw=True)
        ):
            self.schedule_ai_move()

    def update_status(self):
        if self.board.is_game_over(claim_draw=True):
            outcome = self.board.outcome(claim_draw=True)
            self.status.config(
                text=f"Game Over: {outcome.result()}"
            )
        else:
            player = "White" if self.board.turn else "Black"
            self.status.config(text=f"{player} to move")

    def change_mode(self, event=None):
        self.new_game()

    def new_game(self):
        if self.pending_job is not None:
            self.root.after_cancel(self.pending_job)
            self.pending_job = None

        self.board.reset()
        self.selected_square = None

        self.draw_board()
        self.update_status()

        if self.mode.get() == "Defensive vs Aggressive":
            self.schedule_ai_move()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessGUI(root)
    root.mainloop()