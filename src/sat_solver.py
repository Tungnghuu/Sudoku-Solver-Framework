import time
from pysat.solvers import Solver
from src.encoding.cnf_encoding import value, getSudokuFormula
from src.utils.printing_board import returnSolvedBoard_sat

def run_sat(board, n, solver_name='g3', encoding='pairwise'):
    t_enc_start = time.perf_counter()

    # Encoding
    formula = getSudokuFormula(n, amo_encoding=encoding)

    # Given clues
    for r in range(n):
        for c in range(n):
            digit = board[r][c]
            if digit > 0:
                formula.append([value(r + 1, c + 1, digit, n)])

    # Get encoding time ad start solving timer
    enc_time = time.perf_counter() - t_enc_start
    t_solve_start = time.perf_counter()

    solved_board = None
    status_str = "UNKNOWN"

    try:
        # Solve
        with Solver(name=solver_name, bootstrap_with=formula) as solver:
            is_sat = solver.solve()
            solve_time = time.perf_counter() - t_solve_start

            if is_sat:
                status_str = "OPTIMAL"  # SAT
                model = solver.get_model()
                solved_board = returnSolvedBoard_sat(board, model, n)
            else:
                status_str = "UNSAT" # UNSAT
    except Exception as e:
        solve_time = time.perf_counter() - t_solve_start
        status_str = "SOLVER ERROR"
        print(f"\n[SAT Error]: {e}")

    return {
        'status': status_str,
        'encoding_time': enc_time,
        'solve_time': solve_time,
        'total_time': enc_time + solve_time,
        'vars': formula.nv,
        'constraints': len(formula.clauses),
        'solved_board': solved_board
    }

if __name__ == "__main__":
    from utils.printing_board import print_sudoku
    from utils.readSudoku import read_sudoku

    filepath = "data/36/sudoku_36_0.txt"
    board = read_sudoku(filepath)
    size = len(board)

    print(f"=== Testing PYSat Solver on {size}   x{size} Board ===")
    result = run_sat(board, size)

    print(f"Status: {result['status']}")
    print(f"Encoding Time: {result['encoding_time']:.4f}s")
    print(f"Solving Time:  {result['solve_time']:.4f}s")

    if result["solved_board"]:
        print("\nSolved Board:")
        print_sudoku(result["solved_board"])