import argparse
import csv
import math
import re
import statistics
import time
from collections import defaultdict
from pathlib import Path
from src.utils.readSudoku import read_sudoku

PROJECT_DIR = Path(__file__).resolve().parent
PUZZLE_FILENAME = re.compile(r"sudoku_(\d+)_(\d+)\.txt$")

DETAIL_FIELDS = (
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
    "clues",
    "empty_cells",
    "error",
)

SUMMARY_FIELDS = (
    "size",
    "solver",
    "puzzles",
    "successful_solutions",
    "success_rate_percent",
    "avg_encoding_time_seconds",
    "median_encoding_time_seconds",
    "avg_solve_time_seconds",
    "median_solve_time_seconds",
    "avg_total_time_seconds",
    "median_total_time_seconds",
    "avg_variables",
    "avg_constraints_or_clauses",
)

CLUE_SUMMARY_FIELDS = (
    "size",
    "clues",
    "empty_cells",
    "solver",
    "puzzles",
    "successful_solutions",
    "success_rate_percent",
    "avg_encoding_time_seconds",
    "median_encoding_time_seconds",
    "avg_solve_time_seconds",
    "median_solve_time_seconds",
    "avg_total_time_seconds",
    "median_total_time_seconds",
    "avg_variables",
    "avg_constraints_or_clauses",
)

def get_solvers(selected):
    available = {
        "pair": ("PySAT (Pairwise)", "pysat", "pairwise"),
        "seq": ("PySAT (Sequential Counter)", "pysat", "seqcounter"),
        "gurobi": ("Gurobi (MILP)", "gurobi", None),
        "cplex_mip": ("CPLEX (MILP)", "cplex_mip", None),
        "cplex_cp": ("CPLEX (CP)", "cplex_cp", None),
    }
    if selected == ["all"]:
        selected = ["gurobi", "cplex_mip", "cplex_cp", "pair", "seq"]
    elif "all" in selected:
        raise ValueError("'all' can only be used alone")

    if "pysat" in selected:
        selected = [
            solver for solver in selected if solver != "pysat"
        ]
        selected.extend(("pair", "seq"))

    solvers = []
    loaded = {}
    for name in dict.fromkeys(selected):
        if name not in available:
            raise ValueError(f"Unknown solver {name!r}.")
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
    sizes = (
        {int(size) for size in selected_sizes}
        if selected_sizes
        else {
            int(path.name)
            for path in data_dir.iterdir()
            if path.is_dir() and path.name.isdigit()
        }
    )

    puzzles = []
    for size in sorted(sizes):
        size_dir = data_dir / str(size)
        if not size_dir.is_dir():
            raise FileNotFoundError(f"Dataset directory does not exist: {size_dir}")

        for path in size_dir.iterdir():
            match = PUZZLE_FILENAME.fullmatch(path.name)
            if path.is_file() and match and int(match.group(1)) == size:
                puzzles.append((size, int(match.group(2)), path))

    return sorted(puzzles, key=lambda item: (item[0], item[1]))

def validate_board(board, size, path):
    if len(board) != size or any(len(row) != size for row in board):
        raise ValueError(
            f"{path}: expected a {size}x{size} board, got "
            f"{len(board)} rows with lengths {[len(row) for row in board]}"
        )
    if any(value < 0 or value > size for row in board for value in row):
        raise ValueError(f"{path}: cell values must be between 0 and {size}")
    if math.isqrt(size) ** 2 != size:
        raise ValueError(f"{path}: Sudoku size must be a perfect square")

def is_valid_solution(puzzle, solution, size):
    if not isinstance(solution, (list, tuple)) or len(solution) != size:
        return False
    if any(not isinstance(row, (list, tuple)) or len(row) != size for row in solution):
        return False

    required = set(range(1, size + 1))
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value not in required
        for row in solution
        for value in row
    ):
        return False

    if any(
        puzzle[row][column] not in (0, solution[row][column])
        for row in range(size)
        for column in range(size)
    ):
        return False
    if any(set(row) != required for row in solution):
        return False
    if any(
        {solution[row][column] for row in range(size)} != required
        for column in range(size)
    ):
        return False

    block_size = math.isqrt(size)
    return all(
        {
            solution[row][column]
            for row in range(block_row, block_row + block_size)
            for column in range(block_column, block_column + block_size)
        }
        == required
        for block_row in range(0, size, block_size)
        for block_column in range(0, size, block_size)
    )

def run_solver(solver, board, size, sat_solver_name, encoding=None):
    started = time.perf_counter()
    try:
        if encoding is not None:
            result = solver(
                board, size, sat_solver_name, encoding=encoding
            )
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

def mean_or_blank(values):
    return statistics.mean(values) if values else ""

def median_or_blank(values):
    return statistics.median(values) if values else ""

def create_summary(detail_rows):
    grouped = defaultdict(list)
    for row in detail_rows:
        grouped[(row["size"], row["solver"])].append(row)

    summary_rows = []
    for (size, solver), rows in sorted(grouped.items()):
        successful = sum(row["success"] for row in rows)
        encoding_times = [
            row["encoding_time_seconds"]
            for row in rows
            if isinstance(row["encoding_time_seconds"], (int, float))
        ]
        solve_times = [
            row["solve_time_seconds"]
            for row in rows
            if isinstance(row["solve_time_seconds"], (int, float))
        ]
        total_times = [
            row["total_time_seconds"]
            for row in rows
            if isinstance(row["total_time_seconds"], (int, float))
        ]
        variables = [
            row["variables"]
            for row in rows
            if isinstance(row["variables"], (int, float))
        ]
        constraints = [
            row["constraints_or_clauses"]
            for row in rows
            if isinstance(row["constraints_or_clauses"], (int, float))
        ]

        summary_rows.append(
            {
                "size": size,
                "solver": solver,
                "puzzles": len(rows),
                "successful_solutions": successful,
                "success_rate_percent": round(successful * 100 / len(rows), 2),
                "avg_encoding_time_seconds": mean_or_blank(encoding_times),
                "median_encoding_time_seconds": median_or_blank(encoding_times),
                "avg_solve_time_seconds": mean_or_blank(solve_times),
                "median_solve_time_seconds": median_or_blank(solve_times),
                "avg_total_time_seconds": mean_or_blank(total_times),
                "median_total_time_seconds": median_or_blank(total_times),
                "avg_variables": mean_or_blank(variables),
                "avg_constraints_or_clauses": mean_or_blank(constraints),
            }
        )
    return summary_rows

def create_clue_summary(detail_rows):
    grouped = defaultdict(list)
    for row in detail_rows:
        grouped[(row["size"], row["clues"], row["solver"])].append(row)

    summary_rows = []
    for (size, clues, solver), rows in sorted(grouped.items()):
        successful = sum(row["success"] for row in rows)

        def numeric_values(field):
            return [
                row[field]
                for row in rows
                if isinstance(row[field], (int, float))
            ]

        encoding_times = numeric_values("encoding_time_seconds")
        solve_times = numeric_values("solve_time_seconds")
        total_times = numeric_values("total_time_seconds")
        variables = numeric_values("variables")
        constraints = numeric_values("constraints_or_clauses")

        summary_rows.append(
            {
                "size": size,
                "clues": clues,
                "empty_cells": size * size - clues,
                "solver": solver,
                "puzzles": len(rows),
                "successful_solutions": successful,
                "success_rate_percent": round(successful * 100 / len(rows), 2),
                "avg_encoding_time_seconds": mean_or_blank(encoding_times),
                "median_encoding_time_seconds": median_or_blank(encoding_times),
                "avg_solve_time_seconds": mean_or_blank(solve_times),
                "median_solve_time_seconds": median_or_blank(solve_times),
                "avg_total_time_seconds": mean_or_blank(total_times),
                "median_total_time_seconds": median_or_blank(total_times),
                "avg_variables": mean_or_blank(variables),
                "avg_constraints_or_clauses": mean_or_blank(constraints),
            }
        )
    return summary_rows

def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

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
        "--data-dir",
        type=Path,
        default=PROJECT_DIR / "data",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_DIR / "result",
    )
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
    )
    parser.add_argument(
        "--sat-solver",
        default="g3",
    )
    return parser.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    try:
        selected_solvers = get_solvers(args.solvers)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    data_dir = args.data_dir.resolve()
    output_dir = args.output_dir.resolve()

    puzzles = discover_puzzles(data_dir, args.sizes)

    detail_rows = []
    total_runs = len(puzzles) * len(selected_solvers)
    print(f"Solving {len(puzzles)} puzzles with {len(selected_solvers)} solvers.")

    for puzzle_number, (size, _, path) in enumerate(puzzles, start=1):
        board = read_sudoku(path)
        validate_board(board, size, path)
        clue_count = sum(value != 0 for row in board for value in row)
        print(
            f"[Puzzle {puzzle_number}/{len(puzzles)}] "
            f"{path.relative_to(data_dir)} ({size}x{size})"
        )

        for solver_name, solver, encoding in selected_solvers:
            result = run_solver(
                solver,
                board,
                size,
                args.sat_solver,
                encoding,
            )
            row = {
                "puzzle": path.relative_to(data_dir).as_posix(),
                "size": size,
                "solver": solver_name,
                **result,
                "clues": clue_count,
                "empty_cells": size * size - clue_count,
            }
            detail_rows.append(row)
            run_number = len(detail_rows)
            outcome = "valid solution" if result["success"] else "no valid solution"
            print(
                f"  [{run_number}/{total_runs}] {solver_name}: "
                f"{result['status']} ({outcome}), "
                f"total={result['total_time_seconds']}s"
            )
            if result["error"]:
                print(f"Error: {result['error']}")

    summary_rows = create_summary(detail_rows)
    clue_summary_rows = create_clue_summary(detail_rows)
    details_path = output_dir / "benchmark_details.csv"
    summary_path = output_dir / "benchmark_summary.csv"
    clue_summary_path = output_dir / "benchmark_by_clues.csv"
    write_csv(details_path, DETAIL_FIELDS, detail_rows)
    write_csv(summary_path, SUMMARY_FIELDS, summary_rows)
    write_csv(clue_summary_path, CLUE_SUMMARY_FIELDS, clue_summary_rows)

    print(f"\nDetailed results: {details_path}")
    print(f"Summary results: {summary_path}")
    print(f"Size/clue summary: {clue_summary_path}")
    print(
        "Summary time averages include all runs that returned a timing value; "
    )

if __name__ == "__main__":
    main()