import math
import time

from docplex.cp.model import CpoModel as CplexCPModel


def run_cplex_cp(board, n):
    b = int(math.isqrt(n))
    if b * b != n:
        raise ValueError(
            f"Sudoku size {n} is invalid."
        )

    t_enc_start = time.perf_counter()

    model = CplexCPModel(name="Sudoku_CP")

    grid = [
        [model.integer_var(1, n, name=f"x_{r}_{c}") for c in range(n)]
        for r in range(n)
    ]

    # Row
    for r in range(n):
        model.add(model.all_diff(grid[r]))

    # Column
    for c in range(n):
        model.add(model.all_diff([grid[r][c] for r in range(n)]))

    # Block
    for br in range(b):
        for bc in range(b):
            block_vars = [
                grid[r][c]
                for r in range(br * b, (br + 1) * b)
                for c in range(bc * b, (bc + 1) * b)
            ]
            model.add(model.all_diff(block_vars))

    # Given Clues
    for r in range(n):
        for c in range(n):
            digit = board[r][c]
            if digit > 0:
                model.add(grid[r][c] == digit)

    enc_time = time.perf_counter() - t_enc_start
    t_solve_start = time.perf_counter()

    solved_board = None
    status_str = "UNKNOWN"

    try:
        res = model.solve(LogVerbosity='Quiet')
        solve_time = time.perf_counter() - t_solve_start

        if res:
            status_str = res.get_solve_status() # Feasible
            if res.is_solution():
                solved_board = [[0] * n for _ in range(n)]
                for r in range(n):
                    for c in range(n):
                        solved_board[r][c] = res.get_value(grid[r][c])
        else:
            status_str = "INFEASIBLE"

    except Exception as e:
        solve_time = time.perf_counter() - t_solve_start
        status_str = "ERROR"
        print(f"\n[CPLEX CP Error]: {e}")

    return {
        "status": status_str,
        "encoding_time": enc_time,
        "solve_time": solve_time,
        "total_time": enc_time + solve_time,
        "vars": n * n,
        "constraints": 3 * n + (n * n - sum(row.count(0) for row in board)),
        "solved_board": solved_board,
    }

if __name__ == "__main__":
    from utils.printing_board import print_sudoku
    from utils.readSudoku import read_sudoku

    filepath = "data/9/sudoku_9_0.txt"
    board = read_sudoku(filepath)
    size = len(board)

    print(f"=== Testing CPLEX CP Solver on {size}x{size} Board ===")
    res = run_cplex_cp(board, size)

    print(f"Status: {res['status']}")
    print(f"Encoding Time: {res['encoding_time']:.4f}s")
    print(f"Solving Time:  {res['solve_time']:.4f}s")

    if res["solved_board"]:
        print("\nSolved Board:")
        print_sudoku(res["solved_board"])