import tkinter as tk
from tkinter import simpledialog, messagebox
import random
import numpy as np

SIZE = 4

class Game2048:
    def __init__(self, master):
        self.master = master
        self.master.title("2048 with Manual & Auto Play")

        self.board = np.zeros((SIZE, SIZE), dtype=int)

        self.labels = [[None] * SIZE for _ in range(SIZE)]
        self.create_ui()
        self.update_ui()

        self.automation_running = False
        self.move_count = 0
        self.LOG2_TABLE = {2**i: i for i in range(1, 20)}  # 2^1=2, 2^19=524288

    def create_ui(self):
        frame = tk.Frame(self.master)
        frame.pack()

        for r in range(SIZE):
            for c in range(SIZE):
                label = tk.Label(frame, text='', width=6, height=3, font=('Arial', 18), relief='solid', borderwidth=1)
                label.grid(row=r, column=c, padx=5, pady=5)
                label.bind("<Button-1>", lambda e, row=r, col=c: self.manual_tile(row, col))
                self.labels[r][c] = label

        button_frame = tk.Frame(self.master)
        button_frame.pack()

        tk.Button(button_frame, text="Up", command=lambda: self.make_move('up')).grid(row=0, column=1)
        tk.Button(button_frame, text="Left", command=lambda: self.make_move('left')).grid(row=1, column=0)
        tk.Button(button_frame, text="Right", command=lambda: self.make_move('right')).grid(row=1, column=2)
        tk.Button(button_frame, text="Down", command=lambda: self.make_move('down')).grid(row=2, column=1)

        tk.Button(button_frame, text="Start Auto", command=self.start_automation).grid(row=3, column=0, pady=10)
        tk.Button(button_frame, text="Stop Auto", command=self.stop_automation).grid(row=3, column=2, pady=10)

        tk.Label(button_frame, text="AI Depth:").grid(row=4, column=0, pady=5)
        self.depth_var = tk.IntVar(value=4)  # default depth
        tk.Spinbox(button_frame, from_=1, to=6, textvariable=self.depth_var, width=5).grid(row=4, column=1, pady=5)


        self.best_move_label = tk.Label(self.master, text="Best move: ")
        self.best_move_label.pack()

        self.move_count_label = tk.Label(self.master, text="Moves made: 0")
        self.move_count_label.pack()

    def update_ui(self):
        for r in range(SIZE):
            for c in range(SIZE):
                val = self.board[r][c]
                self.labels[r][c]['text'] = str(val) if val != 0 else ''

    def manual_tile(self, row, col):
        if self.board[row][col] != 0:
            return
        value = simpledialog.askinteger("Insert Tile", "Enter 2 or 4", minvalue=2, maxvalue=4)
        if value in [2, 4]:
            self.board[row][col] = value
            self.update_ui()
            best = self.find_best_move(self.board)
            self.best_move_label.config(text=f"Best move: {best}")

    def slide_and_merge(self, row):
        non_zero = row[row != 0]
        new_row = []
        skip = False
        for j in range(len(non_zero)):
            if skip:
                skip = False
                continue
            if j + 1 < len(non_zero) and non_zero[j] == non_zero[j + 1]:
                new_row.append(non_zero[j] * 2)
                skip = True
            else:
                new_row.append(non_zero[j])
        return np.array(new_row + [0] * (SIZE - len(new_row)))

    def move_board(self, board, direction):
        rotated = board
        if direction == 'up':
            rotated = np.rot90(board, -1)
        elif direction == 'down':
            rotated = np.rot90(board, 1)
        elif direction == 'right':
            rotated = np.rot90(board, 2)

        new_board = np.array([self.slide_and_merge(row) for row in rotated])

        if direction == 'up':
            new_board = np.rot90(new_board, 1)
        elif direction == 'down':
            new_board = np.rot90(new_board, -1)
        elif direction == 'right':
            new_board = np.rot90(new_board, 2)

        return new_board

    def can_move(self, board):
        if np.any(board == 0):
            return True
        for r in range(SIZE):
            for c in range(SIZE - 1):
                if board[r][c] == board[r][c + 1]:
                    return True
        for c in range(SIZE):
            for r in range(SIZE - 1):
                if board[r][c] == board[r + 1][c]:
                    return True
        return False

    def evaluate(self, board):
        board = np.array(board)
        empty_cells = np.sum(board == 0)

        # Smoothness: penalty for differences between neighbors
        smoothness = 0
        for r in range(4):
            for c in range(4):
                if board[r, c] != 0:
                    value = self.LOG2_TABLE.get(board[r, c], np.log2(board[r, c]))
                    for dr, dc in [(1,0), (0,1)]:  # right & down neighbors
                        if 0 <= r+dr < 4 and 0 <= c+dc < 4 and board[r+dr, c+dc] != 0:
                            target = self.LOG2_TABLE.get(board[r+dr, c+dc], np.log2(board[r+dr, c+dc]))
                            smoothness -= abs(value - target)

        # Monotonicity
        monotonicity = 0
        for r in range(4):
            row = [board[r, c] for c in range(4) if board[r, c] != 0]
            if len(row) > 1:
                diffs = [self.LOG2_TABLE.get(row[i], np.log2(row[i])) - self.LOG2_TABLE.get(row[i+1], np.log2(row[i+1])) for i in range(len(row)-1)]
                if all(d >= 0 for d in diffs) or all(d <= 0 for d in diffs):
                    monotonicity += sum(abs(d) for d in diffs)

        for c in range(4):
            col = [board[r, c] for r in range(4) if board[r, c] != 0]
            if len(col) > 1:
                diffs = [self.LOG2_TABLE.get(col[i], np.log2(col[i])) - self.LOG2_TABLE.get(col[i+1], np.log2(col[i+1])) for i in range(len(col)-1)]
                if all(d >= 0 for d in diffs) or all(d <= 0 for d in diffs):
                    monotonicity += sum(abs(d) for d in diffs)

        # Max tile in a corner
        max_tile = np.max(board)
        corner_bonus = max_tile if max_tile in [board[0,0], board[0,3], board[3,0], board[3,3]] else 0

        return (
            empty_cells * 250.0 +
            smoothness * 0.1 +
            monotonicity * 1.0 +
            corner_bonus * 2.0
        )

    def expectimax(self, board, depth, is_ai):
        if depth == 0 or not self.can_move(board):
            return self.evaluate(board)

        if is_ai:
            best = float('-inf')
            for move in ['up', 'down', 'left', 'right']:
                new_board = self.move_board(board, move)
                if np.array_equal(new_board, board):
                    continue
                best = max(best, self.expectimax(new_board, depth - 1, False))
            return best
        else:
            empty = list(zip(*np.where(board == 0)))
            if not empty:
                return self.evaluate(board)
            score = 0
            for r, c in empty:
                for val, prob in [(2, 0.9), (4, 0.1)]:
                    new_board = board.copy()
                    new_board[r][c] = val
                    score += prob * self.expectimax(new_board, depth - 1, True)
            return score / len(empty)

    def find_best_move(self, board):
        best_move, best_score = None, float('-inf')
        for move in ['up', 'down', 'left', 'right']:
            new_board = self.move_board(board, move)
            if np.array_equal(new_board, board):
                continue
            score = self.expectimax(new_board, self.depth_var.get(), False)
            if score > best_score:
                best_score, best_move = score, move
        return best_move if best_move else "None"

    def make_move(self, direction):
        new_board = self.move_board(self.board, direction)
        if np.array_equal(new_board, self.board):
            return
        self.board = new_board
        self.move_count += 1
        self.update_ui()
        self.update_move_count()
        best = self.find_best_move(self.board)
        self.best_move_label.config(text=f"Best move: {best}")

    def place_random_tile(self):
        empty = list(zip(*np.where(self.board == 0)))
        if not empty:
            return
        r, c = random.choice(empty)
        self.board[r][c] = 2 if random.random() < 0.9 else 4

    def step_automation(self):
        if not self.automation_running:
            return
        if not self.can_move(self.board):
            messagebox.showinfo("Game Over", "No more moves possible!")
            self.stop_automation()
            return
        self.place_random_tile()
        self.update_ui()
        best = self.find_best_move(self.board)
        if best != "None":
            self.make_move(best)
        self.master.after(300, self.step_automation)

    def start_automation(self):
        if not self.automation_running:
            self.automation_running = True
            self.step_automation()

    def stop_automation(self):
        self.automation_running = False

    def update_move_count(self):
        self.move_count_label.config(text=f"Moves made: {self.move_count}")

if __name__ == "__main__":
    root = tk.Tk()
    game = Game2048(root)
    root.mainloop()