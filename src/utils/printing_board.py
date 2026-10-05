import math
import copy

def returnSolvedBoard_sat(unsolvedBoard, model, n):
    solved_board = copy.deepcopy(unsolvedBoard)
    max_var = n ** 3

    for v in model:
        if 0 < v <= max_var:
            v_index = v - 1
            row = v_index // (n ** 2)
            column = (v_index % (n ** 2)) // n
            digit = (v_index % n) + 1
            solved_board[row][column] = digit
    return solved_board

def print_sudoku(board):
    if not board or not board[0]:
        return

    n = len(board)
    block_size = math.isqrt(n)
    
    max_width = max(len(str(val)) for row in board for val in row if val != 0) if any(any(row) for row in board) else 1
    empty_symbol = "." * max_width

    line_length = n * (max_width + 1) + (block_size - 1) * 2 - 1

    for r in range(n):
        if r > 0 and r % block_size == 0:
            print("-" * line_length)

        row_string = ""
        for c in range(n):
            if c > 0 and c % block_size == 0:
                row_string += "| "

            val = board[r][c]
            symbol = empty_symbol if val == 0 else str(val).rjust(max_width)
            row_string += symbol + " "

        print(row_string.rstrip())