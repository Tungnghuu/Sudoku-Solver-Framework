from src.utils.readSudoku import read_sudoku
from src.gurobi_solver import run_gurobi
from src.cplex_mip_solver import run_cplex_mip
from src.sat_solver import run_sat

if __name__ == "__main__":
    filepath = "data/36/sudoku_36_0.txt"
    board = read_sudoku(filepath)
    size = len(board)

    print(f"Running Sudoku Solvers Benchmark on {size}x{size} Board\n")

    print("Solving with Gurobi...")
    gurobi_res = run_gurobi(board, size)

    print("Solving with CPLEX...")
    cplex_res = run_cplex_mip(board, size)

    print("Solving with PySAT (Glucose3)...")
    sat_res = run_sat(board, size, solver_name='g3')

    # Print Unified Comparison Table
    print("\n" + ">" * 90)
    print(f"{'BENCHMARK COMPARISON':^90}")
    print(">" * 90)

    header = f"{'Metric':<25} | {'Gurobi (MILP)':<18} | {'CPLEX (MILP)':<18} | {'PySAT (CNF)':<18}"
    print(header)
    print("-" * 90)

    print(f"{'Status':<25} | {gurobi_res['status']:<18} | {cplex_res['status']:<18} | {sat_res['status']:<18}")
    print(f"{'Encoding Time (s)':<25} | {gurobi_res['encoding_time']:<18.4f} | {cplex_res['encoding_time']:<18.4f} | {sat_res['encoding_time']:<18.4f}")
    print(f"{'Solving Time (s)':<25} | {gurobi_res['solve_time']:<18.4f} | {cplex_res['solve_time']:<18.4f} | {sat_res['solve_time']:<18.4f}")
    print(f"{'Total Time (s)':<25} | {gurobi_res['total_time']:<18.4f} | {cplex_res['total_time']:<18.4f} | {sat_res['total_time']:<18.4f}")
    print(f"{'Variables':<25} | {gurobi_res['vars']:<18} | {cplex_res['vars']:<18} | {sat_res['vars']:<18}")
    print(f"{'Constraints/Clauses':<25} | {gurobi_res['constraints']:<18} | {cplex_res['constraints']:<18} | {sat_res['constraints']:<18}")

    print("=" * 90)