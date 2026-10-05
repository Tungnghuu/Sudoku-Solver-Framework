import time
import math
from docplex.mp.model import Model
from docplex.mp.utils import DOcplexException

def run_cplex_mip(board, n):
    b = int(math.isqrt(n))
    if b * b != n:
        raise ValueError(f"Sudoku size {n} is invalid. Size must be a perfect square.")

    t_enc_start = time.perf_counter()

    model = Model(name="Sudoku_MILP")
    model.context.solver.log_output = False

    x = model.binary_var_dict(
        [(r, c, d) for r in range(n) for c in range(n) for d in range(n)],
        name="x"
    )

    # Cell
    for r in range(n):
        for c in range(n):
            model.add_constraint(model.sum(x[r, c, d] for d in range(n)) == 1)

    # Row
    for r in range(n):
        for d in range(n):
            model.add_constraint(model.sum(x[r, c, d] for c in range(n)) == 1)

    # Column
    for c in range(n):
        for d in range(n):
            model.add_constraint(model.sum(x[r, c, d] for r in range(n)) == 1)

    # Block
    for br in range(b):
        for bc in range(b):
            for d in range(n):
                model.add_constraint(
                    model.sum(
                        x[r, c, d]
                        for r in range(br * b, (br + 1) * b)
                        for c in range(bc * b, (bc + 1) * b)
                    ) == 1
                )
    
    # Clues
    for r in range(n):
        for c in range(n):
            digit = board[r][c]
            if digit > 0:
                model.add_constraint(x[r, c, digit - 1] == 1)

    enc_time = time.perf_counter() - t_enc_start
    t_solve_start = time.perf_counter()

    try:
        sol = model.solve()
        solve_time = time.perf_counter() - t_solve_start

        status = model.get_solve_status()
        status_str = status.name if status is not None else "UNKNOWN"

        if sol:
            solved_board = [[0] * n for _ in range(n)]
            for r in range(n):
                for c in range(n):
                    for d in range(n):
                        if sol.get_value(x[r, c, d]) > 0.5:
                            solved_board[r][c] = d + 1
                            break

    except (DOcplexException, Exception) as e:
        solve_time = time.perf_counter() - t_solve_start
        status_str = "ERROR"
        print(f"\n[CPLEX Error]: {e}")

    return {
        'status': status_str,
        'encoding_time': enc_time,
        'solve_time': solve_time,
        'total_time': enc_time + solve_time,
        'vars': model.number_of_variables,
        'constraints': model.number_of_constraints,
        'solved_board': solved_board,
    }

if __name__ == "__main__":
    from utils.printing_board import print_sudoku
    from utils.readSudoku import read_sudoku

    filepath = "data/9/sudoku_9_0.txt"
    board = read_sudoku(filepath)
    size = len(board)

    print(f"=== Testing CPLEX CP Solver on {size}x{size} Board ===")
    result = run_cplex_mip(board, size)

    print(f"Status: {result['status']}")
    print(f"Encoding Time: {result['encoding_time']:.4f}s")
    print(f"Solving Time:  {result['solve_time']:.4f}s")

    if result["solved_board"]:
        print("\nSolved Board:")
        print_sudoku(result["solved_board"])