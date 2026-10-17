import time
import math
import gurobipy as gp
from gurobipy import GRB

def run_gurobi(board, n):
    b = int(math.isqrt(n))
    t_enc_start = time.perf_counter()

    # Initialize Gurobi, set quiet output
    env = gp.Env(empty=True)
    env.setParam('OutputFlag', 0)
    env.start()

    model = gp.Model("Sudoku_MILP", env=env)

    # Create binary decision variabls for every cell and digit combination
    x = model.addVars(n, n, n, vtype=GRB.BINARY, name="x")

    # Cell
    for r in range(n):
        for c in range(n):
            model.addConstr(gp.quicksum(x[r, c, d] for d in range(n)) == 1)

    # Row
    for r in range(n):
        for d in range(n):
            model.addConstr(gp.quicksum(x[r, c, d] for c in range(n)) == 1)

    # Column
    for c in range(n):
        for d in range(n):
            model.addConstr(gp.quicksum(x[r, c, d] for r in range(n)) == 1)

    # Block
    for br in range(b):
        for bc in range(b):
            for d in range(n):
                model.addConstr(
                    gp.quicksum(
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
                model.addConstr(x[r, c, digit - 1] == 1)

    # get encoding time and start solving timer
    model.update()
    enc_time = time.perf_counter() - t_enc_start
    t_solve_start = time.perf_counter()
    solved_board = None

    # Solve
    try:
        model.optimize()
        solve_time = time.perf_counter() - t_solve_start

        status_names = {
            GRB.OPTIMAL: "OPTIMAL",
            GRB.INFEASIBLE: "INFEASIBLE",
            GRB.TIME_LIMIT: "TIME_LIMIT",
            GRB.INTERRUPTED: "INTERRUPTED",
        }
        status_str = status_names.get(model.Status, f"STATUS_{model.Status}")

        if model.SolCount > 0:
            solved_board = [[0] * n for _ in range(n)]
            for r in range(n):
                for c in range(n):
                    for d in range(n):
                        if x[r, c, d].X > 0.5:
                            solved_board[r][c] = d + 1
                            break

    except gp.GurobiError as e:
        solve_time = time.perf_counter() - t_solve_start
        status_str = "ERROR"
        print(f"\n[Gurobi Error]: {e}")

    return {
        'status': status_str,
        'encoding_time': enc_time,
        'solve_time': solve_time,
        'total_time': enc_time + solve_time,
        'vars': model.NumVars,
        'constraints': model.NumConstrs,
        'solved_board': solved_board
    }

if __name__ == "__main__":
    from utils.printing_board import print_sudoku
    from utils.readSudoku import read_sudoku

    filepath = "data/36/sudoku_36_0.txt"
    board = read_sudoku(filepath)
    size = len(board)

    print(f"=== Testing Gurobi Solver on {size}x{size} Board ===")
    result = run_gurobi(board, size)

    print(f"Status: {result['status']}")
    print(f"Encoding Time: {result['encoding_time']:.4f}s")
    print(f"Solving Time:  {result['solve_time']:.4f}s")

    if result["solved_board"]:
        print("\nSolved Board:")
        print_sudoku(result["solved_board"])