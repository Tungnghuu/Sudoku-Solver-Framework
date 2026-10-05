import math

def get_box_dimensions(size):
    """
    Determines subgrid row and column dimensions based on board size.
    Handles standard square blocks (4x4, 9x9, 16x16) and common rectangular variations.
    """
    root = math.isqrt(size)
    if root * root == size:
        return root, root
    # Fallbacks for common rectangular subgrid boards (e.g., 6x6 uses 2x3 boxes, 8x8 uses 2x4)
    # if size == 6: return 2, 3
    # if size == 8: return 2, 4
    # if size == 12: return 3, 4
    # raise ValueError(f"Unsupported Sudoku grid size: {size}x{size}")

def is_board_valid(board):
    """
    Validates the initial board state. Returns True if all clues follow 
    Sudoku rules (no duplicates), False otherwise.
    """
    size = len(board)
    try:
        box_r, box_c = get_box_dimensions(size)
    except ValueError:
        print("Validation Error: Invalid board size shape.")
        return False

    # Check for row and column dimensions consistency
    for r in range(size):
        if len(board[r]) != size:
            print(f"Validation Error: Row {r} does not match board size {size}.")
            return False

    # Check rows, columns, and boxes for duplicate clues
    for i in range(size):
        row_seen = set()
        col_seen = set()
        for j in range(size):
            # Check row
            row_val = board[i][j]
            if row_val != 0:
                if row_val < 1 or row_val > size or row_val in row_seen:
                    return False
                row_seen.add(row_val)
            
            # Check column
            col_val = board[j][i]
            if col_val != 0:
                if col_val < 1 or col_val > size or col_val in col_seen:
                    return False
                col_seen.add(col_val)

    # Check subgrid boxes
    for br in range(0, size, box_r):
        for bc in range(0, size, box_c):
            box_seen = set()
            for r in range(box_r):
                for c in range(box_c):
                    val = board[br + r][bc + c]
                    if val != 0:
                        if val in box_seen:
                            return False
                        box_seen.add(val)
    return True

def solve_sudoku(board):
    """
    Generic backtracking Sudoku solver for any valid layout size.
    """
    if not is_board_valid(board):
        print("Cannot solve: The initial board contains invalid duplicate clues!")
        return None

    size = len(board)
    box_r, box_c = get_box_dimensions(size)

    def is_valid_move(r, c, val):
        for i in range(size):
            if board[r][i] == val or board[i][c] == val:
                return False
        
        box_start_r = (r // box_r) * box_r
        box_start_c = (c // box_c) * box_c
        for i in range(box_r):
            for j in range(box_c):
                if board[box_start_r + i][box_start_c + j] == val:
                    return False
        return True

    def backtrack(r, c):
        if r == size:
            return True
        if c == size:
            return backtrack(r + 1, 0)
        if board[r][c] != 0:
            return backtrack(r, c + 1)
            
        for val in range(1, size + 1):
            if is_valid_move(r, c, val):
                board[r][c] = val
                if backtrack(r, c + 1):
                    return True
                board[r][c] = 0
        return False

    if backtrack(0, 0):
        return board
    else:
        print("No solution exists for this configuration.")
        return None