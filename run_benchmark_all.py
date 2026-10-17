import argparse
import csv
import random
import re
import time
from collections import defaultdict
from pathlib import Path
from src.utils.readSudoku import read_sudoku
from src.utils.valid_board import validate_board
from src.utils.valid_solution import is_valid_solution

PROJECT_DIR = Path(__file__).resolve().parent
PUZZLE_FILENAME = re.compile(r"sudoku_(\d+)_(\d+)\.txt$")

DETAIL_FIELDS = (
    "random_seed",
    "iteration",
    "puzzle",
    "size",
    "solver",
    "encoding",
    "status",
    "success",
    "encoding_time_seconds",
    "solve_time_seconds",
    "total_time_seconds",
    "variables",
    "constraints_or_clauses",
    "error",
)

def get_solvers(selected):
    available = {
        "pair": ("PySAT (Pairwise)", "pysat", "pairwise"),
        "seq": ("PySAT (Sequential Counter)", "pysat", "seqcounter"),
        "gurobi": ("Gurobi (MILP)", "gurobi", None),
        "cplex_mip": ("CPLEX (MILP)", "cplex_mip", None),
        "cplex_cp": ("CPLEX (CP)", "cplex_cp", None),
    }
    
    # If user select all -> selected includes all solver
    if selected == ["all"]:
        selected = ["gurobi", "cplex_mip", "cplex_cp", "pair", "seq"]
    elif "all" in selected:
        raise ValueError("'all' can only be used alone")

    if "pysat" in selected:
        selected = [solver for solver in selected if solver != "pysat"]
        selected.extend(("pair", "seq"))

    solvers = []
    loaded = {}

    for name in dict.fromkeys(selected):
        display_name, module_name, encoding = available[name]
        
        if module_name not in loaded:
            if module_name == "pysat":
                from src.sat_solver import run_sat
                loaded[module_name] = run_sat
            elif module_name == "gurobi":
                from src.gurobi_solver import run_gurobi
                loaded[module_name] = run_gurobi
            elif module_name == "cplex_mip":
                from src.cplex_mip_solver import run_cplex_mip
                loaded[module_name] = run_cplex_mip
            else:
                from src.cplex_cp_solver import run_cplex_cp
                loaded[module_name] = run_cplex_cp
        
        solvers.append((display_name, loaded[module_name], encoding))
        
    return tuple(solvers)

def discover_puzzles(data_dir, selected_sizes=None):
    if selected_sizes:
        sizes = {int(size) for size in selected_sizes}
    else:
        sizes = set()
        for path in data_dir.iterdir():
            if path.is_dir() and path.name.isdigit(): # 9 25 36...
                sizes.add(int(path.name))

    puzzles = []
    for size in sorted(sizes):
        size_dir = data_dir / str(size)
        if not size_dir.is_dir():
            raise FileNotFoundError(f"Dataset directory does not exist: {size_dir}")

        # Scan every files in the directory
        for path in size_dir.iterdir():
            match = PUZZLE_FILENAME.fullmatch(path.name)
            # check fpr matching format
            if path.is_file() and match and int(match.group(1)) == size:
                puzzle_index = int(match.group(2))
                puzzles.append((size, puzzle_index, path))

    # Sorting board by size and index
    return sorted(puzzles, key=lambda item: (item[0], item[1]))

def run_solver(solver, board, size, sat_solver_name, encoding=None):
    started = time.perf_counter()
    try:
        if encoding is not None:
            result = solver(board, size, sat_solver_name, encoding=encoding)
        else:
            result = solver(board, size)

        encoding_time = result.get("encoding_time")
        solve_time = result.get("solve_time")
        total_time = result.get("total_time")
        
        if total_time is None and encoding_time is not None and solve_time is not None:
            total_time = encoding_time + solve_time

        return {
            "status": str(result.get("status", "UNKNOWN")),
            "encoding": encoding or "",
            "success": is_valid_solution(board, result.get("solved_board"), size),
            "encoding_time_seconds": encoding_time,
            "solve_time_seconds": solve_time,
            "total_time_seconds": total_time,
            "variables": result.get("vars"),
            "constraints_or_clauses": result.get("constraints"),
            "error": "",
        }

    except Exception as error:
        # If during solving encounter bug/crash, status = ERROR
        elapsed = time.perf_counter() - started
        return {
            "status": "ERROR",
            "encoding": encoding or "",
            "success": False,
            "encoding_time_seconds": "",
            "solve_time_seconds": "",
            "total_time_seconds": elapsed,
            "variables": "",
            "constraints_or_clauses": "",
            "error": f"{type(error).__name__}: {error}",
        }

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark selected Sudoku solvers against numbered puzzle files."
        )
    )
    parser.add_argument(
        "solvers",
        nargs="+",
        choices=("all", "pysat", "pair", "seq", "gurobi", "cplex_mip", "cplex_cp"),
    )
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
    )
    parser.add_argument(
        "--iterations",
        type = int,
        default = 1,
    )
    parser.add_argument(
        "--seed",
        type=int,
    )
    parser.add_argument(
        "--sat-solver",
        default="g3",
    )
    return parser.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    selected_solvers = get_solvers(args.solvers)

    data_dir = PROJECT_DIR / "data"
    output_dir = PROJECT_DIR / "result"
    
    if args.iterations < 1:
        raise SystemExit("--iterations must be >= 1.")

    # Discover puzzle files
    puzzles = discover_puzzles(data_dir, args.sizes)

    # Group puzzle by size
    puzzles_by_size = defaultdict(list)
    for puzzle in puzzles:
        size = puzzle[0]
        puzzles_by_size[size].append(puzzle)

    if args.seed is not None:
        random_seed = args.seed
    else:
        random_seed = random.randint(0, 1_000_000_000)
        
    rng = random.Random(random_seed)

    # Randomly select 20 puzzles/boards
    sampled_puzzles_by_size = {}
    for size, size_puzzles in puzzles_by_size.items():
        sampled_puzzles_by_size[size] = rng.sample(size_puzzles, min(20, len(size_puzzles)))

    # Calculate total runs
    total_sampled_boards = sum(len(puzzles) for puzzles in sampled_puzzles_by_size.values())
    total_runs = total_sampled_boards * args.iterations * len(selected_solvers)

    print(f"Starting benchmark with a total of {total_runs} runs...")

    # Create output directory and CSV file
    output_dir.mkdir(parents=True, exist_ok=True)
    details_path = output_dir / "benchmark_details.csv"

    # Open file for writing
    with details_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=DETAIL_FIELDS)
        writer.writeheader()

        run_number = 0

        # Main loop to execute the solvers on each board
        for iteration in range(1, args.iterations + 1):
            print(f"\nRunning Iteration {iteration}/{args.iterations}")

            for size in sorted(sampled_puzzles_by_size):
                sampled_puzzles = sampled_puzzles_by_size[size]
                
                # Iterate through each Sudoku puzzle file
                for puzzle_number, (p_size, p_index, path) in enumerate(sampled_puzzles, start=1):
                    board = read_sudoku(path)
                    validate_board(board, size, path)
                    
                    puzzle_name = path.relative_to(data_dir).as_posix()

                    # Run the selected solvers
                    for solver_name, solver, encoding in selected_solvers:
                        run_number += 1

                        result = run_solver(solver, board, size, args.sat_solver, encoding,)
                        
                        # Package the result into a clean row dict
                        row = {
                            "random_seed": random_seed,
                            "iteration": iteration,
                            "puzzle": puzzle_name,
                            "size": size,
                            "solver": solver_name,
                            **result,  # Unpack the result dict
                        }
                        
                        # Write the row to the CSV file
                        writer.writerow(row)
                        csv_file.flush()
                        
                        outcome = "Success" if result["success"] else "Failure"
                            
                        # Print console progress
                        print(
                            f"[{run_number}/{total_runs}] Size {size}x{size} | "
                            f"{solver_name} | Board: {puzzle_name} | "
                            f"Status: {result['status']} ({outcome}) | "
                            f"Time: {result['total_time_seconds']}s"
                        )
                        
                        if result["error"]:
                            print(f"Detailed Error: {result['error']}")

    print(f"\nBenchmark completed! Results have been saved to: {details_path}")

if __name__ == "__main__":
    main()