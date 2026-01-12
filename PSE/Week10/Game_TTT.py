"""For the timer feature"""
from inputimeout import inputimeout, TimeoutOccurred


class Board:
    """Represents the Tic Tac Toe board."""

    def __init__(self):
        self.grid = [[" " for _ in range(3)] for _ in range(3)]

    def display(self):
        """Display the board."""
        print("\n")
        for i, row in enumerate(self.grid):
            print(" | ".join(row))
            if i < 2:
                print("-" * 5)

    def empty_squares(self):
        """Return list of empty squares."""
        return [(r, c) for r in range(3) for c in range(3) if self.grid[r][c] == " "]

    def make_move(self, row, col, symbol):
        """Place a symbol if valid."""
        if self.grid[row][col] == " ":
            self.grid[row][col] = symbol
            return True
        return False

    def won_game(self, symbol):
        """Check if symbol has won."""
        lines = self.grid + [list(col) for col in zip(*self.grid)]
        lines.append([self.grid[i][i] for i in range(3)])
        lines.append([self.grid[i][2 - i] for i in range(3)])
        return any(all(cell == symbol for cell in line) for line in lines)

    def game_over(self):
        """Return True if someone wins or draw."""
        return self.won_game("X") or self.won_game("O") or len(self.empty_squares()) == 0


class Player:
    """Represents a player."""

    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
class Game:
    """Main Tic Tac Toe game."""

    def __init__(self):
        self.board = Board()
        """start this is for W10A4"""
        #enable user to enter name"""
        p1name = input("Please enter Player 1 name:")
        p1name = p1name if p1name != "" else "Player 1"
        p2name = input("Please enter Player 2 name:")
        p2name = p2name if p2name != "" else "Player 2"
        """give player1 a choice between the symbols"""
        while True:
            p1symbol = input("Choose your symbole between X or O:")
            if p1symbol in ("X","O"):
                break
            print("Invalid choice!")
        p2symbol = "O" if p1symbol == "X" else "X"
        self.player1 = Player(p1name,p1symbol)
        self.player2 = Player(p2name,p2symbol)
        #self.player1 = Player("Player 1","X")
        #self.player2 = Player("Player 2","O")
        """end this is for W10A4"""
        self.current_player = self.player1

    def other_player(self):
        """Switch turns."""
        self.current_player = (
            self.player2 if self.current_player == self.player1 else self.player1
        )

    def make_human_move(self):
        """Handle a player's move."""
        #start this is for W10A4
        print(f"{self.current_player.name} ({self.current_player.symbol})")
        print("you have 10 seconds to move")
        try:
            rc =inputimeout(
                prompt=f"{self.current_player.name},enter 0-2 for row & col with format r,c (0,0):"
                ,timeout=10
                )

        except TimeoutOccurred:
            print(" Time is Up!!! No Move Made.")
            return

        if not rc.strip():
            print("No input entered. Turn Skipped.")
            return

        rc = rc.replace(",").split()

        if len(rc) != 2 or not all(part.isdigit() for part in rc):
            print("Invalid input. Use two numbers like: 1,2")
            return

        row, col = map(int, rc)

        if not (0 <= row < 3 and 0 <= col < 3):
            print("Coordinates out of range (0–2).")
            return

        try:
            if (row, col) in self.board.empty_squares():
                self.board.make_move(row, col, self.current_player.symbol)
            print(" Invalid move — square already taken or out of range.")
        except ValueError:
            print(" Please enter valid numbers between 0 and 2.")
            return

        #while True:
        #    try:
        #        row = int(input(f"{self.current_player.name}, enter row (0–2): "))
        #        col = int(input(f"{self.current_player.name}, enter col (0–2): "))
        #        if (row, col) in self.board.empty_squares():
        #            self.board.make_move(row, col, self.current_player.symbol)
        #            break
        #        print(" Invalid move — square already taken or out of range.")
        #    except ValueError:
        #        print(" Please enter valid numbers between 0 and 2.")
        #end this is for W10A4"""

    def play_one_turn(self):
        """Play a single turn."""
        self.make_human_move()

    def play_game(self):
        """Main game loop."""
        print("=== Tic Tac Toe (Human1 vs Human2) ===")
        self.board.display()
        while not self.board.game_over():
            print(f"\n{self.current_player.name}'s turn ({self.current_player.symbol})")
            self.play_one_turn()
            self.board.display()
            if self.board.won_game(self.current_player.symbol):
                print(f" {self.current_player.name} wins!")
                return
            self.other_player()
        print(" It's a draw!")

    def print_result(self):
        """Print final result."""
        print("Game finished. Thanks for playing!")


if __name__ == "__main__":
    game = Game()
    game.play_game()
    game.print_result()
