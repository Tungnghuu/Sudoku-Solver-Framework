import math

def is_valid_solution(puzzle, solution, size):
    if not isinstance(solution, (list, tuple)) or len(solution) != size:
        return False
        
    # Check if every row in the solution is a list/tuple of the correct length
    for row in solution:
        if not isinstance(row, (list, tuple)) or len(row) != size:
            return False

    # Check all cell values within the valid range (1 to size)
    required = set(range(1, size + 1))
    for row in solution:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or value not in required:
                return False

    # Check if solution matches the original board clues
    for row in range(size):
        for column in range(size):
            puzzle_val = puzzle[row][column]
            solution_val = solution[row][column]
            if puzzle_val != 0 and puzzle_val != solution_val:
                return False

    # Row
    for row in solution:
        if set(row) != required:
            return False

    # Column
    for column in range(size):
        column_values = set()
        for row in range(size):
            column_values.add(solution[row][column])
        if column_values != required:
            return False

    # Block
    block_size = math.isqrt(size)
    
    for block_row in range(0, size, block_size):
        for block_column in range(0, size, block_size):
            block_values = set()
            
            for row in range(block_row, block_row + block_size):
                for column in range(block_column, block_column + block_size):
                    block_values.add(solution[row][column])
            
            if block_values != required:
                return False

    return True