# chessboard size
N = 5
knight_moves = [
    (2, 1), (1, 2), (-1, 2), (-2, 1),
    (-2, -1), (-1, -2), (1, -2), (2, -1)
]
def create_board():
    return [[-1 for _ in range(N)] for _ in range(N)]

def is_valid(x, y, board):
    return 0 <= x < N and 0 <= y < N and board[x][y] == -1

def knight_tour(x, y, move_count, board):
    if move_count == N * N: # all squares visited
        return True
    for move in knight_moves:
        next_x = x + move[0]
        next_y = y + move[1]
        if is_valid(next_x, next_y, board):
            # mark move with current move count and attempt next tour
            board[next_x][next_y] = move_count
            if knight_tour(next_x, next_y, move_count + 1, board):
                return True
            # if no next tour then unmark the square and backtrack
            board[next_x][next_y] = -1

    return False

def solve_knight_tour(start_x, start_y):
    board = create_board()
    board[start_x][start_y] = 0
    if knight_tour(start_x, start_y, 1, board):
        return board
    else:
        return None
    
start_x, start_y = 0, 0  # start from top left
solution = solve_knight_tour(start_x, start_y)

if solution:
    for row in solution:
        print(row)
else:
    print("No solution found.")
