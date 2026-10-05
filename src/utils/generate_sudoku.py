import math
import random

def generate_test_sudoku(n, empty_ratio=0.6):
    b = int(math.isqrt(n))
    board = [[0] * n for _ in range(n)]

    for r in range(n):
        for c in range(n):
            board[r][c] = (r * b + r // b + c) % n + 1

    random.seed()
    for r in range(n):
        for c in range(n):
            if random.random() < empty_ratio:
                board[r][c] = 0
    return board

def save_sudoku(board, filename):
    with open(filename, 'w') as f:
        for row in board:
            f.write(" ".join(f"{val:2d}" for val in row) + "\n")

save_sudoku(generate_test_sudoku(9), "data/sudoku_9.txt")
save_sudoku(generate_test_sudoku(16), "data/sudoku_16.txt")
save_sudoku(generate_test_sudoku(25), "data/sudoku_25.txt")
save_sudoku(generate_test_sudoku(36), "data/sudoku_36.txt")