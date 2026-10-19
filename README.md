# Comparative Benchmark: SAT, CP, and MILP Solvers for Sudoku

Evaluation framework and performance benchmarks comparing **SAT**, **Constraint Programming (CP)**, and **Mixed-Integer Linear Programming (MILP)** solvers on Sudoku boards $9 \times 9$ up to $36 \times 36$.

## 📌 Solver Configurations

* **SAT (`PySAT`)**: CNF encodings via Pairwise ($\mathcal{O}(N^2)$) and Sequential Counter ($\mathcal{O}(N)$) At-Most-One (AMO) constraints.
* **CP (`IBM CPLEX CP`)**: Direct integer modeling ($X_{i,j} \in \{1, \dots, N\}$) using built-in `all_different` global constraints.
* **MILP (`Gurobi` / `CPLEX MILP`)**: Binary formulation ($N^3$ variables) solved via linear relaxation and branch-and-cut.

---

## 🛠️ Quick Start

### Installation
```bash
pip install python-sat gurobipy docplex numpy matplotlib