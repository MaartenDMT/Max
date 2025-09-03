
def print_board(board):
    for row in board:
        print("|".join(row))
        print("-" * 5)

def check_win(board, player):
    # Check rows
    for row in board:
        if all([cell == player for cell in row]):
            return True
    # Check columns
    for col in range(3):
        if all([board[row][col] == player for row in range(3)]):
            return True
    # Check diagonals
    if all([board[i][i] == player for i in range(3)]) or \
       all([board[i][2 - i] == player for i in range(3)]):
        return True
    return False

def check_draw(board):
    for row in board:
        for cell in row:
            if cell == " ":
                return False
    return True

def get_empty_cells(board):
    cells = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == " ":
                cells.append((r, c))
    return cells

def ai_move(board, ai_player, human_player):
    # Simple AI:
    # 1. Try to win
    # 2. Try to block human
    # 3. Take center
    # 4. Take corners
    # 5. Take any available spot

    # Check if AI can win
    for r, c in get_empty_cells(board):
        board[r][c] = ai_player
        if check_win(board, ai_player):
            return (r, c)
        board[r][c] = " "  # Undo move

    # Check if human can win and block
    for r, c in get_empty_cells(board):
        board[r][c] = human_player
        if check_win(board, human_player):
            board[r][c] = ai_player  # Block
            return (r, c)
        board[r][c] = " "  # Undo move

    # Take center
    if board[1][1] == " ":
        return (1, 1)

    # Take corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for r, c in corners:
        if board[r][c] == " ":
            return (r, c)

    # Take any available spot
    return get_empty_cells(board)[0]

def play_tic_tac_toe():
    board = [[" " for _ in range(3)] for _ in range(3)]
    human_player = "X"
    ai_player = "O"
    current_player = human_player

    print("Welcome to Tic-Tac-Toe!")
    print_board(board)

    while True:
        if current_player == human_player:
            try:
                row = int(input("Enter row (0-2): "))
                col = int(input("Enter column (0-2): "))
                if not (0 <= row <= 2 and 0 <= col <= 2) or board[row][col] != " ":
                    print("Invalid move. Try again.")
                    continue
                board[row][col] = human_player
            except ValueError:
                print("Invalid input. Please enter numbers.")
                continue
        else:
            print("AI is making a move...")
            r, c = ai_move(board, ai_player, human_player)
            board[r][c] = ai_player
            print(f"AI placed {ai_player} at ({r}, {c})")

        print_board(board)

        if check_win(board, current_player):
            print(f"{current_player} wins!")
            break
        elif check_draw(board):
            print("It's a draw!")
            break

        current_player = ai_player if current_player == human_player else human_player

if __name__ == "__main__":
    play_tic_tac_toe()
