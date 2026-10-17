import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell
def _():
    import importlib
    from datetime import date
    import altair as alt
    import marimo as mo
    import polars as pl
    import src.scheduler

    importlib.reload(src.scheduler)
    from src.scheduler import build_sample_tasks, solve_schedule

    return alt, build_sample_tasks, date, mo, pl, solve_schedule


@app.cell
def _(mo):
    mo.md("""
    # Full Project Schedule: 6 Sequential Tasks & 4 Main Tasks (13 Parallel Subtasks)

    - **Single Resource (`Resource 1`)**: Executes every active phase (`Task`, `Prepare`, `Handle`) without overlap (`add_no_overlap`).
    - **4 Main Tasks (`M1`–`M4`)**: Each contains 3–4 parallel subtasks split into **`Prepare` (Blue) → `Wait` (Gray, 0h) → `Handle` (Green)**.
    - **6 Simple Tasks (`T1`–`T6`)**: Sequential milestones before, between, and after the main tasks.
    """)
    return


@app.cell
def _(date, mo):
    project_start_date = mo.ui.date(
        value=date(2026, 10, 19),
        label="Project start date",
    )
    hours_per_day = mo.ui.slider(
        start=1, stop=12, step=1, value=8, label="Resource capacity (hours / day)"
    )

    mo.hstack([project_start_date, hours_per_day], justify="start", gap=2)
    return hours_per_day, project_start_date


@app.cell
def _(build_sample_tasks, hours_per_day, project_start_date, solve_schedule):
    tasks = build_sample_tasks(resource="Resource 1")
    result = solve_schedule(
        tasks=tasks,
        project_start_date=project_start_date.value,
        hours_per_day=hours_per_day.value,
    )
    return (result,)


@app.cell
def _(alt, mo, pl, result):
    df = pl.DataFrame(
        [
            {
                "id": p.task_id,
                "row": p.row_name,
                "phase": p.phase,
                "hours_needed": p.hours_needed,
                "duration_days": p.duration_days,
                "start_date": p.start_date,
                "end_date": p.end_date,
                "resource": p.resource,
            }
            for p in result.phases
        ]
    )

    _row_order = list(dict.fromkeys(p.row_name for p in result.phases))

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadius=3)
        .encode(
            x=alt.X("start_date:T", title="Date"),
            x2="end_date:T",
            y=alt.Y(
                "row:N",
                title="Task / Subtask",
                sort=_row_order,
                axis=alt.Axis(labelLimit=300),
            ),
            color=alt.Color(
                "phase:N",
                title="Phase",
                scale=alt.Scale(
                    domain=["Main Task", "Task", "Prepare", "Wait", "Handle"],
                    range=["#334155", "#0d9488", "#2563eb", "#cbd5e1", "#16a34a"],
                ),
            ),
            opacity=alt.condition(
                alt.datum.phase == "Wait",
                alt.value(0.55),
                alt.value(0.95),
            ),
            tooltip=[
                alt.Tooltip("row:N", title="Task / Subtask"),
                alt.Tooltip("phase:N", title="Phase"),
                alt.Tooltip("hours_needed:Q", title="Resource Hours"),
                alt.Tooltip("duration_days:Q", title="Duration (days)"),
                alt.Tooltip("start_date:T", title="Start Date", format="%Y-%m-%d"),
                alt.Tooltip("end_date:T", title="End Date", format="%Y-%m-%d"),
                alt.Tooltip("resource:N", title="Resource"),
            ],
        )
        .properties(
            title=(
                f"Schedule for Resource 1 ({result.project_start_date} → {result.project_end_date}, "
                f"{result.makespan_days} days, {result.total_hours} resource hours)"
            ),
            height=620,
        )
    )

    mo.vstack(
        [
            mo.md(
                f"**Solver Status:** `{result.status}` | "
                f"**Start:** `{result.project_start_date}` | "
                f"**End:** `{result.project_end_date}` | "
                f"**Total Duration:** `{result.makespan_days}` days | "
                f"**Total Active Resource Effort:** `{result.total_hours}` hours"
            ),
            mo.ui.altair_chart(chart),
            mo.ui.table(df),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
