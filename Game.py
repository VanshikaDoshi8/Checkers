import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import ImageTk, Image
from Checkers import Checkers, Positions
from enum import Enum

class Mode(Enum):
    SINGLE_PLAYER = 0
    MULTIPLE_PLAYER = 1

class Algorithm(Enum):
    MINIMAX = 0
    RANDOM = 1

CHECKER_SIZE = 8
GAME_MODE = Mode.SINGLE_PLAYER
STARTING_PLAYER = Checkers.BLACK
USED_ALGORITHM = Algorithm.MINIMAX
MAX_DEPTH = 5
EVALUATION_FUNCTION = Checkers.evaluate2
INCREASE_DEPTH = True
IMG_SIZE = 60

def from_rgb(rgb):
    r, g, b = rgb
    return f'#{r:02x}{g:02x}{b:02x}'

# Difficulty selection dialog before game start
class DifficultyDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Select AI Difficulty:", font=("Arial", 12)).pack(padx=10, pady=10)
        self.var = tk.StringVar(value="Medium")
        for option in ["Easy", "Medium", "Hard"]:
            tk.Radiobutton(master, text=option, variable=self.var, value=option).pack(anchor=tk.W)
        return None
    def apply(self):
        self.result = self.var.get()

class GUI:
    def __init__(self, window, maxDepth):
        self.window = window  # Store window reference here
        self.maxDepth = maxDepth
        self.game = Checkers(CHECKER_SIZE)
        self.history = [self.game.getBoard()]
        self.historyPtr = 0
        self.player = STARTING_PLAYER
        self.lastX = None
        self.lastY = None
        self.willCapture = False
        self.cnt = 0
        self.last_played = None  # For highlighting last move
        self.btn = [[None]*self.game.size for _ in range(self.game.size)]

        # Load images
        self.black_man_img = ImageTk.PhotoImage(Image.open('assets/black_man.png').resize((IMG_SIZE, IMG_SIZE)))
        self.black_king_img = ImageTk.PhotoImage(Image.open('assets/black_king.png').resize((IMG_SIZE, IMG_SIZE)))
        self.white_man_img = ImageTk.PhotoImage(Image.open('assets/white_man.png').resize((IMG_SIZE, IMG_SIZE)))
        self.white_king_img = ImageTk.PhotoImage(Image.open('assets/white_king.png').resize((IMG_SIZE, IMG_SIZE)))
        self.blank_img = ImageTk.PhotoImage(Image.open('assets/blank.png').resize((IMG_SIZE, IMG_SIZE)))

        # Board UI setup
        frm_board = tk.Frame(master=self.window)
        frm_board.pack(fill=tk.BOTH, expand=True)
        for i in range(self.game.size):
            frm_board.columnconfigure(i, weight=1, minsize=IMG_SIZE)
            frm_board.rowconfigure(i, weight=1, minsize=IMG_SIZE)
            for j in range(self.game.size):
                frame = tk.Frame(master=frm_board)
                frame.grid(row=i, column=j, sticky="nsew")
                self.btn[i][j] = tk.Button(master=frame, width=IMG_SIZE, height=IMG_SIZE, relief=tk.FLAT)
                self.btn[i][j].bind("<Button-1>", self.click)
                self.btn[i][j].pack(expand=True, fill=tk.BOTH)

        frm_counter = tk.Frame(master=self.window)
        frm_counter.pack(expand=True)
        self.lbl_counter = tk.Label(master=frm_counter)
        self.lbl_counter.pack()

        self.update()
        nextPositions = [move[0] for move in self.game.nextMoves(self.player)]
        self.highlight(nextPositions, highlight_type='default')
        self.window.mainloop()

    def update(self):
        for i in range(self.game.size):
            f = i % 2 == 1
            for j in range(self.game.size):
                if f:
                    self.btn[i][j]['bg'] = 'gray30'
                else:
                    self.btn[i][j]['bg'] = 'white'
                img = self.blank_img
                if self.game.board[i][j] == Checkers.BLACK_MAN:
                    img = self.black_man_img
                elif self.game.board[i][j] == Checkers.BLACK_KING:
                    img = self.black_king_img
                elif self.game.board[i][j] == Checkers.WHITE_MAN:
                    img = self.white_man_img
                elif self.game.board[i][j] == Checkers.WHITE_KING:
                    img = self.white_king_img
                self.btn[i][j]["image"] = img
                f = not f
        self.lbl_counter['text'] = f'Moves without capture: {self.cnt}'
        self.window.update()

    def highlight(self, positions: Positions, highlight_type='default', captures=None):
        for x in range(self.game.size):
            for y in range(self.game.size):
                defaultbg = self.btn[x][y].cget('bg')
                self.btn[x][y].master.config(highlightbackground=defaultbg, highlightthickness=3)
        if highlight_type == 'possible_moves':
            for x, y in positions:
                self.btn[x][y].master.config(highlightbackground="blue", highlightthickness=3)
        elif highlight_type == 'capture_moves':
            for x, y in captures if captures else []:
                self.btn[x][y].master.config(highlightbackground="red", highlightthickness=3)
            for x, y in positions:
                if (x, y) not in captures:
                    self.btn[x][y].master.config(highlightbackground="blue", highlightthickness=3)
        else:
            for x, y in positions:
                self.btn[x][y].master.config(highlightbackground="yellow", highlightthickness=3)
        if self.last_played:
            lx, ly = self.last_played
            self.btn[lx][ly].master.config(highlightbackground="green", highlightthickness=3)

    def click(self, event):
        info = event.widget.master.grid_info()
        x, y = info["row"], info["column"]
        if self.lastX is None or self.lastY is None:
            moves = self.game.nextMoves(self.player)
            found = (x, y) in [move[0] for move in moves]
            if found:
                self.lastX = x
                self.lastY = y
                normal, capture = self.game.nextPositions(x, y)
                positions = normal if len(capture) == 0 else capture
                if len(capture) == 0:
                    self.highlight(positions, highlight_type='possible_moves')
                else:
                    self.highlight(positions, highlight_type='capture_moves', captures=positions)
            else:
                print("Invalid position")
            return
        normalPositions, capturePositions = self.game.nextPositions(self.lastX, self.lastY)
        positions = normalPositions if (len(capturePositions) == 0) else capturePositions
        if (x, y) not in positions:
            print("invalid move")
            if not self.willCapture:
                self.lastX = None
                self.lastY = None
                nextPositions = [move[0] for move in self.game.nextMoves(self.player)]
                self.highlight(nextPositions, highlight_type='default')
            return
        canCapture, removed, promoted = self.game.playMove(self.lastX, self.lastY, x, y)
        self.last_played = (x, y)
        self.highlight([], highlight_type='default')
        self.update()
        self.cnt += 1
        self.lastX = None
        self.lastY = None
        self.willCapture = False

        if removed != 0:
            self.cnt = 0
        if promoted:
            messagebox.showinfo(message="Piece promoted to KING!", title="Promotion")
        if canCapture:
            _, nextCaptures = self.game.nextPositions(x, y)
            if len(nextCaptures) != 0:
                self.willCapture = True
                self.lastX = x
                self.lastY = y
                self.highlight(nextCaptures, highlight_type='capture_moves', captures=nextCaptures)
                return

        if GAME_MODE == Mode.SINGLE_PLAYER:
            cont, reset = True, False
            if USED_ALGORITHM == Algorithm.MINIMAX:
                evaluate = EVALUATION_FUNCTION
                if self.cnt > 20:
                    evaluate = Checkers.endGame
                    if INCREASE_DEPTH:
                        self.maxDepth = max(self.maxDepth, 7)
                else:
                    evaluate = Checkers.evaluate2
                cont, reset = self.game.minimaxPlay(1 - self.player, maxDepth=self.maxDepth, evaluate=evaluate, enablePrint=False)
            elif USED_ALGORITHM == Algorithm.RANDOM:
                cont, reset = self.game.randomPlay(1 - self.player, enablePrint=False)
            self.cnt += 1
            if not cont:
                messagebox.showinfo(message="You Won!", title="Checkers")
                self.window.destroy()
                return
            self.update()
            if reset:
                self.cnt = 0
        else:
            self.player = 1 - self.player

        if self.cnt >= 100:
            messagebox.showinfo(message="Draw!", title="Checkers")
            self.window.destroy()
            return

        nextPositions = [move[0] for move in self.game.nextMoves(self.player)]
        self.highlight(nextPositions, highlight_type='default')
        if len(nextPositions) == 0:
            if GAME_MODE == Mode.SINGLE_PLAYER:
                messagebox.showinfo(message="You lost!", title="Checkers")
            else:
                winner = "BLACK" if self.player == Checkers.WHITE else "WHITE"
                messagebox.showinfo(message=f"{winner} Player won!", title="Checkers")
            self.window.destroy()
        self.history = self.history[:self.historyPtr + 1]
        self.history.append(self.game.getBoard())
        self.historyPtr += 1

# Main function: show difficulty dialog, then launch game
def main():
    root = tk.Tk()
    root.withdraw()
    dialog = DifficultyDialog(root)
    difficulty = dialog.result
    root.destroy()

    if difficulty is None:
        messagebox.showinfo("Exit", "No difficulty selected. Exiting.")
        return

    difficulty_map = {"Easy": 2, "Medium": 4, "Hard": 7}
    maxDepth = difficulty_map.get(difficulty, 4)
    window = tk.Tk()
    window.title("Checkers")
    GUI(window, maxDepth)

if __name__ == "__main__":
    main()
