import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

PROJECT_DIR = Path(__file__).resolve().parent

DETAIL_FIELDS = {
    "puzzle", "size", "solver", "success",
    "encoding_time_seconds", "solve_time_seconds", "total_time_seconds",
    "variables", "constraints_or_clauses",
}

PUZZLE_SUMMARY_FIELDS = (
    "puzzle", "size", "solver", "runs", "successful_runs", "success_rate_percent",
    "mean_encoding_time_seconds", "mean_solve_time_seconds", "mean_total_time_seconds",
    "mean_variables", "mean_constraints_or_clauses",
)

SUMMARY_FIELDS = (
    "size", "solver", "puzzles", "runs", "successful_runs", "success_rate_percent",
    "mean_encoding_time_seconds", "mean_solve_time_seconds", 
    "mean_total_time_seconds", "median_total_time_seconds",
    "mean_variables", "mean_constraints_or_clauses",
)

METRIC_FIELDS = (
    "encoding_time_seconds", "solve_time_seconds", "total_time_seconds",
    "variables", "constraints_or_clauses",
)

def read_detail_rows(path):
    results = []
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Create new dict to copy from row to adjust
            new_row = dict(row)
            
            # parse int to 'size'
            new_row["size"] = int(row["size"])
            
            # 'sucess' to boolean
            success_text = row["success"].strip().lower()
            new_row["success"] = success_text in ("true", "1", "yes")
            
            # Handling params from METRIC_FIELDS
            for metric in METRIC_FIELDS:
                value_str = row[metric].strip()
                
                # Validating data
                if value_str:
                    num_value = float(value_str)
                    if math.isfinite(num_value):
                        new_row[metric] = num_value
                    else:
                        new_row[metric] = None
                else:
                    new_row[metric] = None
            
            # appending processed row inn to result
            results.append(new_row)
            
    return results

def summarize_group(rows, puzzle=None):
    # Only take successful row/run
    success_rows = []
    for row in rows:
        if row["success"]:
            success_rows.append(row)
            
    total_runs = len(rows)
    successful_runs = len(success_rows)
    
    # Calc success rate in percentage
    if total_runs > 0:
        success_rate = round(100 * successful_runs / total_runs, 2)
    else:
        success_rate = 0.0

    summary = {
        "size": rows[0]["size"],
        "solver": rows[0]["solver"],
        "runs": total_runs,
        "successful_runs": successful_runs,
        "success_rate_percent": success_rate,
    }
    
    # Calculate mean for every metric 
    for metric in METRIC_FIELDS:
        values = []
        for row in success_rows:
            val = row[metric]
            if val is not None:
                values.append(val)
        
        if values:
            summary[f"mean_{metric}"] = statistics.mean(values)
        else:
            summary[f"mean_{metric}"] = ""
            
    # processing puzzle/board
    if puzzle is not None:
        summary["puzzle"] = puzzle
    else:
        # count every unique board
        unique_puzzles = set()
        for row in rows:
            unique_puzzles.add(row["puzzle"])
        summary["puzzles"] = len(unique_puzzles)
        
    return summary

def create_summaries(rows):
    # grouping data
    by_puzzle = defaultdict(list)
    by_size = defaultdict(list)
    
    for row in rows:
        # Groupby (puzzle, size and solver)
        puzzle_key = (row["puzzle"], row["size"], row["solver"])
        by_puzzle[puzzle_key].append(row)
        
        # groupby (size, solver)
        size_key = (row["size"], row["solver"])
        by_size[size_key].append(row)

    # create summary for every puzzle/board
    puzzle_summaries = []
    for (puzzle, size, solver), group_rows in sorted(by_puzzle.items()):
        summary = summarize_group(group_rows, puzzle=puzzle)
        puzzle_summaries.append(summary)

    # Grouping puzzle sum by size and solver
    ps_by_size = defaultdict(list)
    for summary_item in puzzle_summaries:
        key = (summary_item["size"], summary_item["solver"])
        ps_by_size[key].append(summary_item)

    # summary for every size
    summaries = []
    for key, runs in sorted(by_size.items()):
        puzzle_summaries_for_size = ps_by_size[key]
        summary = summarize_group(runs)
        
        # Calculate mean of mean_{metric}
        for metric in METRIC_FIELDS:
            puzzle_means = []
            for item in puzzle_summaries_for_size:
                mean_key = f"mean_{metric}"
                # only take from sucessful run or non-zero
                if item["successful_runs"] > 0 and item[mean_key] != "":
                    puzzle_means.append(item[mean_key])
            
            if puzzle_means:
                summary[f"mean_{metric}"] = statistics.mean(puzzle_means)
            else:
                summary[f"mean_{metric}"] = ""
        
        # Calculating Median of total time
        puzzle_times = []
        for item in puzzle_summaries_for_size:
            time_val = item["mean_total_time_seconds"]

            if item["successful_runs"] > 0 and isinstance(time_val, (int, float)):
                puzzle_times.append(time_val)
        
        if puzzle_times:
            summary["median_total_time_seconds"] = statistics.median(puzzle_times)
        else:
            summary["median_total_time_seconds"] = ""
        
        summaries.append(summary)

    return puzzle_summaries, summaries

def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents= True, exist_ok= True)
    with path.open("w", newline="", encoding = "utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames = fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def plot_boxplots(puzzle_summaries, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # grouping summaries by size
    summaries_size = defaultdict(list)
    for row in puzzle_summaries:
        size = row["size"]
        summaries_size[size].append(row)

    box_colors = ("#007bff8f", "#ff800086", "#ff000473", "#00ffff7f", "#1eff0086")

    # running through each size
    for size, summaries in sorted(summaries_size.items()):
        solvers = []
        for row in summaries:
            solver_name = row["solver"]
            if solver_name not in solvers:
                solvers.append(solver_name)
        
        # Filtering runtime for each solver
        times_by_solver = []
        for solver in solvers:
            times = []
            for row in summaries:
                if row["solver"] == solver and row["successful_runs"] > 0:
                    runtime = row["mean_total_time_seconds"]
                    if isinstance(runtime, (int, float)) and runtime > 0:
                        times.append(runtime)
            times_by_solver.append(times)

        # INIT Matplot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Base Conditions
        if any(times_by_solver):
            boxplot = ax.boxplot(
                times_by_solver,
                tick_labels=solvers,
                patch_artist=True,  # Draw box
                showmeans=True,     # Show mean inside the box
            )
            
            for idx, box in enumerate(boxplot["boxes"]):
                color_index = idx % len(box_colors)
                box.set_facecolor(box_colors[color_index])
            
            # Y axis is log scale
            ax.set_yscale("log")
            ax.set_ylabel("Mean total runtime (s)")
            ax.grid(axis="y", which="both", alpha=0.25)

        # X axis setup
        ax.set_xticks(range(1, len(solvers) + 1))
        
        xtick_labels = [f" {solver} \n (20 boards)" for solver in solvers]
        ax.set_xticklabels(xtick_labels)
        
        ax.set_title(f"{size}x{size} Sudoku: Solver Runtime")
        ax.set_xlabel("Solver")

        fig.tight_layout()

        # Saving
        file_name = f"boxplot_{size}x{size}.png"
        fig.savefig(output_dir / file_name, bbox_inches="tight")
        plt.close(fig)

def plot_median_runtime(puzzle_summaries, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # group run time by size and solver
    runtimes_by_size_solver = defaultdict(list)
    for row in puzzle_summaries:
        runtime = row["mean_total_time_seconds"]
        if row["successful_runs"] > 0 and isinstance(runtime, (int, float)) and runtime > 0:
            key = (row["size"], row["solver"])
            runtimes_by_size_solver[key].append(runtime)

    sizes = sorted({row["size"] for row in puzzle_summaries})
    
    solvers = []
    for row in puzzle_summaries:
        solver_name = row["solver"]
        if solver_name not in solvers:
            solvers.append(solver_name)

    line_colors = ("#007bff", "#ff8000", "#ff0004", "#00ffff", "#1eff00")

    # Matplot init
    fig, ax = plt.subplots(figsize=(10, 6))
    plotted = False

    # Run through every solver to draw graph
    for idx, solver in enumerate(solvers):
        solver_sizes = []
        medians = []
        
        # calculate median of mean runinig time for each size of this solver
        for size in sizes:
            times = runtimes_by_size_solver.get((size, solver), [])
            if times:
                solver_sizes.append(size)
                medians.append(statistics.median(times))
        
        if solver_sizes:
            color_index = idx % len(line_colors)
            ax.plot(
                solver_sizes,
                medians,
                marker="o",
                linewidth=2,
                label=solver,
                color=line_colors[color_index],
            )
            plotted = True

    if plotted:
        ax.set_yscale("log")
        ax.set_xticks(sizes)
        ax.set_xticklabels([f"{size}x{size}" for size in sizes])
        ax.set_ylabel("Median total runtime (s)")
        ax.legend(title="Solver")
        ax.grid(axis="y", which="both", alpha=0.25)

    ax.set_title("Median Solver Runtime by Sudoku Size")
    ax.set_xlabel("Sudoku size")

    fig.tight_layout()

    # Save
    fig.savefig(output_dir / "median_runtime.png", bbox_inches="tight")
    plt.close(fig)

def plot_encoding_complexity(puzzle_summaries, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group data by grid size and solver
    data_by_size_solver = defaultdict(list)
    for row in puzzle_summaries:
        count = row["mean_constraints_or_clauses"]
        # Only successful runs
        if (
            row["successful_runs"] > 0
            and isinstance(count, (int, float))
            and count > 0
        ):
            data_by_size_solver[(row["size"], row["solver"])].append(count)

    # Prepare unique grid sizes, solvers
    sizes = sorted({row["size"] for row in puzzle_summaries})
    solvers = list(dict.fromkeys(row["solver"] for row in puzzle_summaries))
    
    line_colors = ("#007bff", "#ff8000", "#ff0004", "#00a6a6", "#7b2cbf")
    line_styles = ("-", "--", ":", "-.", (0, (5, 1)))
    
    fig, ax = plt.subplots(figsize=(10, 6))

    plotted = False
    
    # Loop through each solver to calculate median
    for index, solver in enumerate(solvers):
        solver_sizes = []
        median_counts = []
        
        # Solve median value for each grid size
        for size in sizes:
            counts = data_by_size_solver.get((size, solver), [])
            if counts:
                solver_sizes.append(size)
                median_counts.append(statistics.median(counts))

        if solver_sizes:
            color = line_colors[index % len(line_colors)]
            style = line_styles[index % len(line_styles)]
            
            ax.plot(
                solver_sizes,
                median_counts,
                marker="o",
                linewidth=2,
                label=solver,
                color=color,
                linestyle=style,
            )
            plotted = True
            
            # annotate label for each data point
            for s, val in zip(solver_sizes, median_counts):
                if val >= 1e6:
                    val_str = f"{val*1e-6:.1f}M"
                elif val >= 1e3:
                    val_str = f"{val*1e-3:.1f}K"
                else:
                    val_str = f"{int(val)}"
                    
                ax.annotate(
                    val_str,
                    (s, val),
                    textcoords="offset points",
                    xytext=(0, 8),
                    ha="center",
                    fontsize=8,
                    color=color,
                    weight="bold"
                )

    # x axis config
    if plotted:
        ax.set_xticks(sizes)
        ax.set_xticklabels([f"{size}x{size}" for size in sizes])
        ax.legend(title="Solver", loc="upper left")
        ax.grid(axis="y", which="both", alpha=0.25)
    else:
        ax.text(0.5, 0.5, "No successful complexity measurements to plot", ha="center", va="center", transform=ax.transAxes)
        ax.set_xticks([])

    # y axis cònfig
    ax.set_yscale("log")
    ax.set_ylim(top=1e7)

    # Format y axis to K and M
    def format_y_ticks(x, pos):
        if x >= 1e6:
            return f'{x*1e-6:.1f}M'
        elif x >= 1e3:
            return f'{int(x*1e-3)}K'
        else:
            return f'{int(x)}'

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_y_ticks))

    # set titles and labels
    ax.set_ylabel("Clauses / Constraints")
    ax.set_title("Encoding Complexity Growth by Grid Size")
    ax.set_xlabel("Sudoku Grid Size")
    
    # Save
    fig.tight_layout()
    fig.savefig(output_dir / "encoding_complexity.png", bbox_inches="tight")
    plt.close(fig)

def plot_time_breakdown(summaries, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract unique solvers, board sizes
    solvers = sorted({row["solver"] for row in summaries})
    sizes = sorted({row["size"] for row in summaries})
    
    # Dictionaries to store encoding and solving times
    enc_times = defaultdict(dict)
    sol_times = defaultdict(dict)
    
    for row in summaries:
        size = row["size"]
        solver = row["solver"]
        # Only successful runs
        if row["successful_runs"] > 0:
            enc = row.get("mean_encoding_time_seconds", 0) or 0
            sol = row.get("mean_solve_time_seconds", 0) or 0
            enc_times[solver][size] = enc
            sol_times[solver][size] = sol

    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(sizes))
    width = 0.15
    colors = ("#007bff", "#ff8000", "#ff0004", "#00a6a6", "#7b2cbf")
    
    # Loop through each solver
    for idx, solver in enumerate(solvers):
        # Get time values for each grid size
        enc_vals = [enc_times[solver].get(size, 0) for size in sizes]
        sol_vals = [sol_times[solver].get(size, 0) for size in sizes]
        
        # Calculate horizontal position for this solver
        pos = [p + idx * width for p in x]
        
        # Draw the bottom bar for enc time
        ax.bar(
            pos, enc_vals, width, 
            label=f"{solver} (Enc)", 
            color=colors[idx % len(colors)], 
            alpha=0.5
        )

        # Draw the top bar for solving time -> stacked on top of enc time
        ax.bar(
            pos, sol_vals, width, 
            bottom=enc_vals, 
            label=f"{solver} (Sol)", 
            color=colors[idx % len(colors)], 
            hatch="//"
        )

    # scales, labels, legend
    ax.set_yscale("log")
    ax.set_title("Encoding Time vs. Solving Time Breakdown")
    ax.set_ylabel("Mean Time (s)")
    ax.set_xlabel("Sudoku Grid Size")
    
    # Center x axis labels
    ax.set_xticks([p + width * (len(solvers) - 1) / 2 for p in x])
    ax.set_xticklabels([f"{size}x{size}" for size in sizes])
    
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="small")
    ax.grid(axis="y", which="both", alpha=0.25)
    
    # Save
    fig.tight_layout()
    fig.savefig(output_dir / "time_breakdown.png", bbox_inches="tight")
    plt.close(fig)

def main():
    details_path = PROJECT_DIR / "result" / "benchmark_details.csv"
    output_dir = PROJECT_DIR / "result"

    rows = read_detail_rows(details_path)
    p_sum, summaries = create_summaries(rows)

    write_csv(output_dir / "benchmark_by_puzzle.csv", PUZZLE_SUMMARY_FIELDS, p_sum)
    write_csv(output_dir / "benchmark_summary.csv", SUMMARY_FIELDS, summaries)

    plot_boxplots(p_sum, output_dir)
    plot_median_runtime(p_sum, output_dir)
    plot_encoding_complexity(p_sum, output_dir)
    plot_time_breakdown(p_sum, output_dir)
    print(f"Processed {len(rows)} run(s) successfully.")

if __name__ == "__main__":
    main()