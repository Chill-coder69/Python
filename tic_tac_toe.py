def print_board(board):
    print()
    print(f" {board[0]} | {board[1]} | {board[2]} ")
    print("---|---|---")
    print(f" {board[3]} | {board[4]} | {board[5]} ")
    print("---|---|---")
    print(f" {board[6]} | {board[7]} | {board[8]} ")
    print()
def check_winner(board, player):
    win_conditions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]]
    for condition in win_conditions:
        if all(board[i] == player for i in condition):
            return True
    return False
def is_draw(board):
    return all(space in ['X', 'O'] for space in board)
def tic_tac_toe():
    board = [str(i+1) for i in range(9)]
    current_player = 'X'
    while True:
        print_board(board)
        move = input(f"Player {current_player}, choose a position (1-9): ")
        if not move.isdigit() or int(move) < 1 or int(move) > 9:
            print("Invalid input. Try again.")
            continue
        index = int(move) - 1
        if board[index] in ['X', 'O']:
            print("That spot is already taken. Try again.")
            continue
        board[index] = current_player
        if check_winner(board, current_player):
            print_board(board)
            print(f"🎉 Player {current_player} wins!")
            break
        elif is_draw(board):
            print_board(board)
            print("It's a draw!")
            break
        current_player = 'O' if current_player == 'X' else 'X'
tic_tac_toe()
