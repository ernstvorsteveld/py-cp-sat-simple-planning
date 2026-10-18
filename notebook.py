import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell
def _():
    import importlib
    from datetime import date

    import marimo as mo

    import src.models
    import src.resources
    import src.scheduler
    import src.tasks
    import src.visualizations

    importlib.reload(src.models)
    importlib.reload(src.resources)
    importlib.reload(src.tasks)
    importlib.reload(src.scheduler)
    importlib.reload(src.visualizations)

    build_sample_resources = src.resources.build_sample_resources
    solve_schedule = src.scheduler.solve_schedule
    build_sample_tasks = src.tasks.build_sample_tasks
    build_daily_assignments_df = src.visualizations.build_daily_assignments_df
    build_daily_resource_matrix_df = src.visualizations.build_daily_resource_matrix_df
    build_resource_timeline_chart = src.visualizations.build_resource_timeline_chart
    build_resources_df = src.visualizations.build_resources_df
    build_scheduled_tasks_df = src.visualizations.build_scheduled_tasks_df
    build_task_gantt_chart = src.visualizations.build_task_gantt_chart
    return (
        build_daily_assignments_df,
        build_daily_resource_matrix_df,
        build_resource_timeline_chart,
        build_resources_df,
        build_sample_resources,
        build_sample_tasks,
        build_scheduled_tasks_df,
        build_task_gantt_chart,
        date,
        mo,
        solve_schedule,
    )


@app.cell
def _(mo):
    mo.md("""
    # Unified Nested Tasks (`Task` with `subtasks`) & Skill-Based Resource Scheduling

    - **Unified `Task` Model**: Every item is a `Task`. A Main Task can either have no subtasks (`subtasks=[]`) or contain nested `Task` objects (`subtasks=[Task(...), ...]`).
    - **Subtasks**: Subtasks inside a Main Task can run **in parallel** or have dependencies (`predecessors`) among themselves (including passive waiting subtasks with `hours_needed=0, wait_days>0`).
    - **Skills (`skill1`, `skill2`, `skill3`) & Availability**: CP-SAT assigns an eligible resource to each active task/subtask and pauses multi-day tasks over the resource's off-days.
    """)
    return


@app.cell
def _(date, mo):
    project_start_date = mo.ui.date(
        value=date(2026, 10, 19),
        label="Project start date",
    )
    alice_hpd = mo.ui.slider(
        start=1, stop=12, step=1, value=8, label="Alice (skill1, Mon–Thu) hours/day"
    )
    bob_hpd = mo.ui.slider(
        start=1, stop=12, step=1, value=8, label="Bob (skill1 & skill3, Tue–Fri) hours/day"
    )
    charlie_hpd = mo.ui.slider(
        start=1, stop=12, step=1, value=8, label="Charlie (skill2 & skill3, Mon–Thu) hours/day"
    )
    diana_hpd = mo.ui.slider(
        start=1, stop=12, step=1, value=6, label="Diana (skill2, Mon–Fri) hours/day"
    )

    mo.vstack(
        [
            mo.md("### Project & Resource Capacity Controls"),
            project_start_date,
            mo.hstack([alice_hpd, bob_hpd], justify="start", gap=2),
            mo.hstack([charlie_hpd, diana_hpd], justify="start", gap=2),
        ]
    )
    return alice_hpd, bob_hpd, charlie_hpd, diana_hpd, project_start_date


@app.cell
def _(
    alice_hpd,
    bob_hpd,
    build_sample_resources,
    build_sample_tasks,
    charlie_hpd,
    diana_hpd,
    project_start_date,
    solve_schedule,
):
    resources = build_sample_resources(
        alice_hours=alice_hpd.value,
        bob_hours=bob_hpd.value,
        charlie_hours=charlie_hpd.value,
        diana_hours=diana_hpd.value,
    )
    tasks = build_sample_tasks()
    result = solve_schedule(
        tasks=tasks,
        resources=resources,
        project_start_date=project_start_date.value,
    )
    return resources, result


@app.cell
def _(
    build_daily_assignments_df,
    build_daily_resource_matrix_df,
    build_resource_timeline_chart,
    build_resources_df,
    build_scheduled_tasks_df,
    build_task_gantt_chart,
    mo,
    resources,
    result,
):
    task_chart = build_task_gantt_chart(result)
    resource_chart = build_resource_timeline_chart(result, resources)
    daily_resource_matrix_df = build_daily_resource_matrix_df(result, resources)
    daily_df = build_daily_assignments_df(result)
    resources_df = build_resources_df(resources)
    scheduled_tasks_df = build_scheduled_tasks_df(result)

    mo.vstack(
        [
            mo.md(
                f"**Solver Status:** `{result.status}` | "
                f"**Start:** `{result.project_start_date}` | "
                f"**End:** `{result.project_end_date}` | "
                f"**Total Calendar Span:** `{result.makespan_days}` days | "
                f"**Total Effort:** `{result.total_hours}` hours"
            ),
            mo.ui.altair_chart(task_chart),
            mo.ui.altair_chart(resource_chart),
            mo.md("### Assignment Hours per Resource per Day"),
            mo.ui.table(daily_resource_matrix_df),
            mo.md("### Detailed Daily Task-Resource Assignments"),
            mo.ui.table(daily_df),
            mo.md("### Resources & Availability"),
            mo.ui.table(resources_df),
            mo.md("### Scheduled Tasks & Subtasks"),
            mo.ui.table(scheduled_tasks_df),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
