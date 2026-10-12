import os
from src.utils.readSudoku import read_sudoku
from src.gurobi_solver import run_gurobi
from src.cplex_mip_solver import run_cplex_mip
from src.cplex_cp_solver import run_cplex_cp
from src.sat_solver import run_sat

if __name__ == "__main__":
    size = 36
    total_boards = 20

    solvers = ['Gurobi (MILP)', 'CPLEX (MILP)', 'CPLEX (CP)', 'PySAT (CNF)']
    metrics = {s: {'success_count': 0, 'encoding_time': 0.0, 'solve_time': 0.0, 'total_time': 0.0, 'vars': 0, 'constraints': 0} for s in solvers}

    print(f"STARTING BENCHMARK: {total_boards} Boards of Dimensions {size}x{size}")

    for i in range(total_boards):
        filepath = f"data/{size}/sudoku_{size}_{i}.txt"
        if not os.path.exists(filepath):
            print(f"Warning: File {filepath} missing. Skipping board {i}.")
            continue
        
        board = read_sudoku(filepath)
        print(f"Processing Board {i+1}/{total_boards}...")

        # Gurobi
        gurobi_res = run_gurobi(board, size)
        if gurobi_res['status'] in ['OPTIMAL', 'SATISFIABLE', True]:
            metrics['Gurobi (MILP)']['success_count'] += 1
            metrics['Gurobi (MILP)']['encoding_time'] += gurobi_res['encoding_time']
            metrics['Gurobi (MILP)']['solve_time'] += gurobi_res['solve_time']
            metrics['Gurobi (MILP)']['total_time'] += gurobi_res['total_time']
            metrics['Gurobi (MILP)']['vars'] = gurobi_res['vars']
            metrics['Gurobi (MILP)']['constraints'] = gurobi_res['constraints']

        # CPLEX MIP
        cplex_res = run_cplex_mip(board, size)
        if cplex_res['status'] in ['OPTIMAL', 'SATISFIABLE', True, 'OPTIMAL_SOLUTION']:
            metrics['CPLEX (MILP)']['success_count'] += 1
            metrics['CPLEX (MILP)']['encoding_time'] += cplex_res['encoding_time']
            metrics['CPLEX (MILP)']['solve_time'] += cplex_res['solve_time']
            metrics['CPLEX (MILP)']['total_time'] += cplex_res['total_time']
            metrics['CPLEX (MILP)']['vars'] = cplex_res['vars']
            metrics['CPLEX (MILP)']['constraints'] = cplex_res['constraints']

        # CPLEX CP
        cplex_cp_res = run_cplex_cp(board, size)
        if cplex_cp_res['status'] in ['OPTIMAL', 'SATISFIABLE', True, 'OPTIMAL_SOLUTION', 'Feasible']:
            metrics['CPLEX (CP)']['success_count'] += 1
            metrics['CPLEX (CP)']['encoding_time'] += cplex_cp_res['encoding_time']
            metrics['CPLEX (CP)']['solve_time'] += cplex_cp_res['solve_time']
            metrics['CPLEX (CP)']['total_time'] += cplex_cp_res['total_time']
            metrics['CPLEX (CP)']['vars'] = cplex_cp_res['vars']
            metrics['CPLEX (CP)']['constraints'] = cplex_cp_res['constraints']

        # PySAT Glucose 3
        sat_res = run_sat(board, size, solver_name='g3')
        if sat_res['status'] in ['OPTIMAL', 'SATISFIABLE', True]:
            metrics['PySAT (CNF)']['success_count'] += 1
            metrics['PySAT (CNF)']['encoding_time'] += sat_res['encoding_time']
            metrics['PySAT (CNF)']['solve_time'] += sat_res['solve_time']
            metrics['PySAT (CNF)']['total_time'] += sat_res['total_time']
            metrics['PySAT (CNF)']['vars'] = sat_res['vars']
            metrics['PySAT (CNF)']['constraints'] = sat_res['constraints']

    avg_results = {}
    for solver in solvers:
        count = metrics[solver]['success_count']
        divisor = count if count > 0 else total_boards
        
        avg_results[solver] = {
            'status': f"Solved {count}/{total_boards}",
            'encoding_time': metrics[solver]['encoding_time'] / divisor,
            'solve_time': metrics[solver]['solve_time'] / divisor,
            'total_time': metrics[solver]['total_time'] / divisor,
            'vars': metrics[solver]['vars'],
            'constraints': metrics[solver]['constraints']
        }

    print("\n" + ">" * 110)
    print(f"{f'BENCHMARK COMPARISON AVERAGE RESULTS FOR {size}x{size}':^110}")
    print(">" * 110)

    header = f"{'Metric (Average)':<25} | {'Gurobi (MILP)':<18} | {'CPLEX (MILP)':<18} | {'CPLEX (CP)':<18} | {'PySAT (CNF)':<18}"
    print(header)
    print("-" * 110)

    print(f"{'Status / Success':<25} | {avg_results['Gurobi (MILP)']['status']:<18} | {avg_results['CPLEX (MILP)']['status']:<18} | {avg_results['CPLEX (CP)']['status']:<18} | {avg_results['PySAT (CNF)']['status']:<18}")
    print(f"{'Encoding Time (s)':<25} | {avg_results['Gurobi (MILP)']['encoding_time']:<18.4f} | {avg_results['CPLEX (MILP)']['encoding_time']:<18.4f} | {avg_results['CPLEX (CP)']['encoding_time']:<18.4f} | {avg_results['PySAT (CNF)']['encoding_time']:<18.4f}")
    print(f"{'Solving Time (s)':<25} | {avg_results['Gurobi (MILP)']['solve_time']:<18.4f} | {avg_results['CPLEX (MILP)']['solve_time']:<18.4f} | {avg_results['CPLEX (CP)']['solve_time']:<18.4f} | {avg_results['PySAT (CNF)']['solve_time']:<18.4f}")
    print(f"{'Total Time (s)':<25} | {avg_results['Gurobi (MILP)']['total_time']:<18.4f} | {avg_results['CPLEX (MILP)']['total_time']:<18.4f} | {avg_results['CPLEX (CP)']['total_time']:<18.4f} | {avg_results['PySAT (CNF)']['total_time']:<18.4f}")
    print(f"{'Variables':<25} | {avg_results['Gurobi (MILP)']['vars']:<18} | {avg_results['CPLEX (MILP)']['vars']:<18} | {avg_results['CPLEX (CP)']['vars']:<18} | {avg_results['PySAT (CNF)']['vars']:<18}")
    print(f"{'Constraints/Clauses':<25} | {avg_results['Gurobi (MILP)']['constraints']:<18} | {avg_results['CPLEX (MILP)']['constraints']:<18} | {avg_results['CPLEX (CP)']['constraints']:<18} | {avg_results['PySAT (CNF)']['constraints']:<18}")

    print("=" * 110)
