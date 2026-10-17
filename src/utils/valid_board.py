import math

def validate_board(board, size, path):
    # Check if the board has the correct number of rows
    if len(board) != size:
        row_lengths = [len(row) for row in board]
        raise ValueError(
            f"{path}: expected a {size}x{size} board, got "
            f"{len(board)} rows with lengths {row_lengths}"
        )
        
    # Check if every row has the correct number of columns
    for row in board:
        if len(row) != size:
            row_lengths = [len(row) for row in board]
            raise ValueError(
                f"{path}: expected a {size}x{size} board, got "
                f"{len(board)} rows with lengths {row_lengths}"
            )

    # Check all cell values within the valid range (0 to size)
    for row in board:
        for value in row:
            if value < 0 or value > size:
                raise ValueError(f"{path}: cell values must be between 0 and {size}")

    # Check if the Sudoku size is a perfect square number (e.g., 9, 16, 25, 36)
    if math.isqrt(size) ** 2 != size:
        raise ValueError(f"{path}: Sudoku size invalid")