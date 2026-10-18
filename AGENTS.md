# Agent Rules & Project Scope (`py-cp-sat-simple-planning`)

## Operational Rules

1. **No Git Commands Allowed**: Never run, propose, or execute any `git` commands (including read-only commands such as `git status`, `git log`, `git diff`, or write commands such as `git add`, `git commit`, `git checkout`, `git branch`, etc.). All version control operations are strictly managed by the user.
2. **Learning-Focused & Incremental**: The user is learning these tools (`agy`, OR-Tools CP-SAT, and Marimo). Work in small, incremental, runnable steps rather than generating large codebases all at once. Briefly explain key CP-SAT modeling concepts (variables, constraints, objectives) and Marimo reactive patterns as they are introduced.
3. **Separation of Concerns & Dedicated Files per Subject**:
   - Always split code into separate files in `src/` by subject/responsibility (e.g., domain models, data generation, solver logic, visualizations) rather than combining multiple subjects into one file.
   - Whenever a new subject or concern is introduced, create a dedicated module for it.
   - Create a separate, dedicated function for every individual diagram (Altair chart) and every table (Polars DataFrame) in a dedicated module outside the notebook.
   - Keep the Marimo notebook thin—use it strictly for interactive UI controls, calling module functions, and rendering outputs.
4. **Environment & Package Management**: Use `uv` (`pyproject.toml`) with the latest Python version (`>=3.14`) for all Python environment, dependency, and command execution tasks (e.g., `uv add`, `uv run`).
5. **Import Organization**: Always organize imports cleanly according to standard Python conventions (PEP 8 / `isort` / `ruff`):
   - Group imports into three sections separated by a blank line: (1) standard library, (2) third-party packages, and (3) local `src` modules.
   - Within each section, place plain `import ...` statements before `from ... import ...` statements, sorted alphabetically.
   - Within `from ... import (...)` blocks, group `CONSTANT_CASE` names first, followed by `PascalCase` classes, then `snake_case` functions/variables, sorted case-insensitively in alphabetical order.
   - Remove any unused imports and verify/auto-format import order after creating or editing Python files by running `uvx ruff check --select I,F401 --fix src/ notebook.py`.
6. **Zero Warnings Allowed**: Linter, type-checker, and Marimo warnings are strictly not allowed and must always be fixed before finishing any step:
   - After creating or editing any Python file, always run `uvx ruff check --fix src/ notebook.py` and `uv run marimo check notebook.py` (and resolve any remaining diagnostics) so that zero warnings or errors remain across the codebase.
   - In Marimo cells that do not export variables, omit trailing bare `return` statements (`PLR1711`).
7. **Keep Solver Documentation Updated**: Whenever any changes are made to the schedule solver functionality (such as variables, constraints, objective function, horizon calculation, or post-processing in `src/scheduler.py`), always update `SOLVE_SCHEDULE.md` so the documentation accurately reflects how the solver works.

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
  - Keep `SOLVE_SCHEDULE.md` synchronized with any changes to `solve_schedule` or its helper functions.
- **Visualizations & Tables (`src/`)**:
  - Create a separate, dedicated function for every chart and every table in a dedicated module rather than building DataFrames or Altair charts inline in the notebook.
- **Marimo Notebooks**:
  - Always launch the notebook server with `--watch` (`uv run marimo edit --watch notebook.py`) so external edits to `.py` files on disk are automatically synced to the browser.
  - Reload `src.*` modules in the first cell so external edits to `src/` are picked up immediately when cells re-run.
  - Keep cells small and reactive—avoid mutating global state across cells.
  - Note that in Marimo, variables shared across cells cannot be redefined in multiple cells; use a leading underscore (e.g., `_task`) for cell-local temporary variables.
