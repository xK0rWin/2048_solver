import numpy as np
import tkinter as tk
import random

# Directions
UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3
move_names = {UP: "UP", DOWN: "DOWN", LEFT: "LEFT", RIGHT: "RIGHT"}

# --- Game logic ------------------------------------------------------------
def slide_and_merge(row):
    new_row = [i for i in row if i != 0]
    for i in range(len(new_row) - 1):
        if new_row[i] == new_row[i + 1]:
            new_row[i] *= 2
            new_row[i + 1] = 0
    new_row = [i for i in new_row if i != 0]
    return new_row + [0] * (len(row) - len(new_row))

def move(board, direction):
    b = np.copy(board)
    if direction == LEFT:
        return np.array([slide_and_merge(row) for row in b])
    if direction == RIGHT:
        return np.array([slide_and_merge(row[::-1])[::-1] for row in b])
    if direction == UP:
        b = b.T
        return move(b, LEFT).T
    if direction == DOWN:
        b = b.T
        return move(b, RIGHT).T
    return b

# --- Heuristic & Expectimax ------------------------------------------------
def heuristic(board):
    empty_cells = np.sum(board == 0)
    max_tile = np.max(board)
    smoothness = -np.sum(np.abs(board[:, :-1] - board[:, 1:])) - np.sum(np.abs(board[:-1, :] - board[1:, :]))
    return empty_cells * 1000 + np.log(max_tile + 1) * 100 + smoothness

def expectimax(board, depth, player_turn=True):
    if depth == 0:
        return heuristic(board)

    if player_turn:
        best = -float("inf")
        for d in [UP, DOWN, LEFT, RIGHT]:
            new_board = move(board, d)
            if np.array_equal(new_board, board):
                continue
            val = expectimax(new_board, depth - 1, False)
            best = max(best, val)
        return best if best != -float("inf") else heuristic(board)
    else:
        cells = list(zip(*np.where(board == 0)))
        if not cells:
            return heuristic(board)
        exp_val = 0
        for (i, j) in cells:
            for val, p in [(2, 0.9), (4, 0.1)]:
                new_board = np.copy(board)
                new_board[i, j] = val
                exp_val += p * (expectimax(new_board, depth - 1, True) / len(cells))
        return exp_val

def find_best_move(board, depth=3):
    best_move, best_val = None, -float("inf")
    for d in [UP, DOWN, LEFT, RIGHT]:
        new_board = move(board, d)
        if np.array_equal(new_board, board):
            continue
        val = expectimax(new_board, depth - 1, False)
        if val > best_val:
            best_move, best_val = d, val
    return best_move

# --- UI --------------------------------------------------------------------
class Game2048UI:
    def __init__(self, root):
        self.root = root
        self.root.title("2048 Manual UI")

        # Initialize board
        self.board = np.zeros((4, 4), dtype=int)

        # UI setup
        self.canvas = tk.Canvas(root, width=400, height=400, bg="white")
        self.canvas.grid(row=0, column=0, columnspan=4)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.draw_board()

        # Buttons for moves
        tk.Button(root, text="Up", command=lambda: self.do_move(UP)).grid(row=1, column=1)
        tk.Button(root, text="Down", command=lambda: self.do_move(DOWN)).grid(row=3, column=1)
        tk.Button(root, text="Left", command=lambda: self.do_move(LEFT)).grid(row=2, column=0)
        tk.Button(root, text="Right", command=lambda: self.do_move(RIGHT)).grid(row=2, column=2)

        # Best move label
        self.best_label = tk.Label(root, text="Best Move: -", font=("Arial", 14, "bold"))
        self.best_label.grid(row=4, column=0, columnspan=4, pady=10)

        # Start/Stop automation
        self.running = False
        self.start_button = tk.Button(root, text="Start Auto", command=self.start_auto)
        self.start_button.grid(row=5, column=0, columnspan=2, pady=5)
        self.stop_button = tk.Button(root, text="Stop Auto", command=self.stop_auto)
        self.stop_button.grid(row=5, column=2, columnspan=2, pady=5)

    def draw_board(self):
        self.canvas.delete("all")
        size = 100
        for i in range(4):
            for j in range(4):
                x1, y1 = j * size, i * size
                x2, y2 = x1 + size, y1 + size
                val = self.board[i, j]
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="lightgray", outline="black")
                if val != 0:
                    self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                            text=str(val), font=("Arial", 20, "bold"))

    def do_move(self, direction):
        new_board = move(self.board, direction)
        if not np.array_equal(new_board, self.board):
            self.board = new_board
        self.draw_board()
        self.update_best_move()

    def on_canvas_click(self, event):
        size = 100
        row, col = event.y // size, event.x // size
        if 0 <= row < 4 and 0 <= col < 4:
            self.ask_tile_value(row, col)

    def ask_tile_value(self, row, col):
        win = tk.Toplevel(self.root)
        win.title("Choose Tile")
        tk.Label(win, text=f"Place tile at ({row}, {col})").pack(pady=5)
        tk.Button(win, text="2", command=lambda: self.set_tile(row, col, 2, win)).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(win, text="4", command=lambda: self.set_tile(row, col, 4, win)).pack(side=tk.RIGHT, padx=10, pady=10)

    def set_tile(self, row, col, value, win):
        self.board[row, col] = value
        win.destroy()
        self.draw_board()
        self.update_best_move()

    def update_best_move(self):
        best = find_best_move(self.board, depth=3)
        if best is not None:
            self.best_label.config(text=f"Best Move: {move_names[best]}")
        else:
            self.best_label.config(text="Best Move: -")

    def start_auto(self):
        self.running = True
        self.auto_step()

    def stop_auto(self):
        self.running = False

    def auto_step(self):
        if not self.running:
            return
        # Place random tile
        empty = list(zip(*np.where(self.board == 0)))
        if not empty:
            self.stop_auto()
            return
        i, j = random.choice(empty)
        self.board[i, j] = 2 if random.random() < 0.9 else 4

        # Make best move
        best = find_best_move(self.board, depth=3)
        if best is None:
            self.stop_auto()
            return
        self.board = move(self.board, best)

        self.draw_board()
        self.update_best_move()
        self.root.after(200, self.auto_step)  # repeat every 200ms

# --- Main -------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    game = Game2048UI(root)
    root.mainloop()
