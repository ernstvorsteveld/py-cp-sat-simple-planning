# Agent Rules & Project Scope (`py-cp-sat-simple-planning`)

## Operational Rules

1. **No Git Commands Allowed**: Never run, propose, or execute any `git` commands (including read-only commands such as `git status`, `git log`, `git diff`, or write commands such as `git add`, `git commit`, `git checkout`, `git branch`, etc.). All version control operations are strictly managed by the user.
2. **Learning-Focused & Incremental**: The user is learning these tools (`agy`, OR-Tools CP-SAT, and Marimo). Work in small, incremental, runnable steps rather than generating large codebases all at once. Briefly explain key CP-SAT modeling concepts (variables, constraints, objectives) and Marimo reactive patterns as they are introduced.
3. **Separation of Concerns**: Keep domain models and CP-SAT solver logic in pure Python modules (`src/`), and use Marimo notebooks strictly for interactive UI, parameter tuning, and schedule visualization.
4. **Environment & Package Management**: Use `uv` (`pyproject.toml`) with the latest Python version (`>=3.14`) for all Python environment, dependency, and command execution tasks (e.g., `uv add`, `uv run`).

## Project Scope & Stack

- **Domain**: Task / project scheduling (sequencing tasks with durations, deadlines, dependencies, and resource limits)
- **Python Version**: `>=3.14` (latest)
- **Package & Environment Manager**: `uv`
- **Optimization Engine**: OR-Tools CP-SAT (`ortools.sat.python.cp_model`)
- **Interactive UI / Notebook**: Marimo (`marimo`)
- **Data & Visualization**: Polars (`polars`) for dataframes and Altair (`altair`) for interactive Gantt charts

## Modeling & Notebook Conventions

- **CP-SAT Modeling (`src/`)**:
  - Use clear, typed data structures (e.g., `dataclass`) for inputs (tasks, resources, horizon) and outputs (solve status, scheduled intervals, makespan).
  - Always check and report the solver status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `MODEL_INVALID`) rather than assuming a solution exists.
  - Set a sensible solver time limit (`solver.parameters.max_time_in_seconds`).
- **Marimo Notebooks**:
  - Always launch the notebook server with `--watch` (`uv run marimo edit --watch notebook.py`) so external edits to `.py` files on disk are automatically synced to the browser.
  - Keep cells small and reactive—avoid mutating global state across cells.
  - Note that in Marimo, variables shared across cells cannot be redefined in multiple cells; use a leading underscore (e.g., `_task`) for cell-local temporary variables.
