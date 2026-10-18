import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell
def _():
    import importlib
    from datetime import date

    import marimo as mo

    import src.models
    import src.postal_codes
    import src.projects
    import src.resources
    import src.scheduler
    import src.tasks
    import src.visualizations

    importlib.reload(src.models)
    importlib.reload(src.postal_codes)
    importlib.reload(src.tasks)
    importlib.reload(src.projects)
    importlib.reload(src.resources)
    importlib.reload(src.scheduler)
    importlib.reload(src.visualizations)

    build_sample_projects = src.projects.build_sample_projects
    build_sample_resources = src.resources.build_sample_resources
    solve_schedule = src.scheduler.solve_schedule
    build_daily_assignments_df = src.visualizations.build_daily_assignments_df
    build_daily_resource_matrix_df = src.visualizations.build_daily_resource_matrix_df
    build_projects_df = src.visualizations.build_projects_df
    build_resource_timeline_chart = src.visualizations.build_resource_timeline_chart
    build_resources_df = src.visualizations.build_resources_df
    build_scheduled_tasks_df = src.visualizations.build_scheduled_tasks_df
    build_task_gantt_chart = src.visualizations.build_task_gantt_chart
    return (
        build_daily_assignments_df,
        build_daily_resource_matrix_df,
        build_projects_df,
        build_resource_timeline_chart,
        build_resources_df,
        build_sample_projects,
        build_sample_resources,
        build_scheduled_tasks_df,
        build_task_gantt_chart,
        date,
        mo,
        solve_schedule,
    )


@app.cell
def _(mo):
    mo.md("""
    # Multi-Project Scheduling with Dutch Postal Code Proximity & 12 Skilled Resources

    - **5 Projects (`PRJ-001` – `PRJ-005`)**: Each project is executed at a Dutch postal code (`postal_code`) and has its own task and subtask schedule.
    - **12 Resources across the Netherlands (`R1` – `R12`)**: Every resource lives at a Dutch postal code with specific skills (`skill1`, `skill2`, `skill3`) and weekly working days.
    - **Closest Resource Selection**: CP-SAT schedules all 5 projects across the shared resource pool (preventing double-booking) while preferring the resources that live **closest to each project's postal code**.
    """)


@app.cell
def _(date, mo):
    base_start_date = mo.ui.date(
        value=date(2026, 10, 19),
        label="Portfolio start date",
    )
    default_hpd = mo.ui.slider(
        start=4,
        stop=10,
        step=1,
        value=8,
        label="Base resource hours/day",
    )
    project_filter = mo.ui.dropdown(
        options=["ALL", "PRJ-001", "PRJ-002", "PRJ-003", "PRJ-004", "PRJ-005"],
        value="ALL",
        label="Filter charts & task tables by project",
    )
    prj1_pc = mo.ui.text(value="3512 JE", label="PRJ-001 (Utrecht) postal code")
    prj2_pc = mo.ui.text(value="1015 CJ", label="PRJ-002 (Amsterdam) postal code")
    prj3_pc = mo.ui.text(value="5612 AX", label="PRJ-003 (Eindhoven) postal code")
    prj4_pc = mo.ui.text(value="9713 AV", label="PRJ-004 (Groningen) postal code")
    prj5_pc = mo.ui.text(value="3014 GT", label="PRJ-005 (Rotterdam) postal code")

    mo.vstack(
        [
            mo.md("### Portfolio, Project Postal Codes & Filter Controls"),
            mo.hstack([base_start_date, default_hpd, project_filter], justify="start", gap=2),
            mo.hstack([prj1_pc, prj2_pc, prj3_pc, prj4_pc, prj5_pc], justify="start", gap=2),
        ]
    )
    return (
        base_start_date,
        default_hpd,
        prj1_pc,
        prj2_pc,
        prj3_pc,
        prj4_pc,
        prj5_pc,
        project_filter,
    )


@app.cell
def _(
    base_start_date,
    build_sample_projects,
    build_sample_resources,
    default_hpd,
    prj1_pc,
    prj2_pc,
    prj3_pc,
    prj4_pc,
    prj5_pc,
    solve_schedule,
):
    projects = build_sample_projects(
        base_start_date=base_start_date.value,
        prj1_postal_code=prj1_pc.value,
        prj2_postal_code=prj2_pc.value,
        prj3_postal_code=prj3_pc.value,
        prj4_postal_code=prj4_pc.value,
        prj5_postal_code=prj5_pc.value,
    )
    resources = build_sample_resources(default_hours=default_hpd.value)
    result = solve_schedule(
        projects=projects,
        resources=resources,
    )
    return projects, resources, result


@app.cell
def _(
    build_daily_assignments_df,
    build_daily_resource_matrix_df,
    build_projects_df,
    build_resource_timeline_chart,
    build_resources_df,
    build_scheduled_tasks_df,
    build_task_gantt_chart,
    mo,
    project_filter,
    projects,
    resources,
    result,
):
    selected_proj = project_filter.value
    projects_df = build_projects_df(result)
    task_chart = build_task_gantt_chart(result, project_id_filter=selected_proj)
    resource_chart = build_resource_timeline_chart(
        result, resources, project_id_filter=selected_proj
    )
    daily_resource_matrix_df = build_daily_resource_matrix_df(
        result, resources, project_id_filter=selected_proj
    )
    daily_df = build_daily_assignments_df(result, project_id_filter=selected_proj)
    resources_df = build_resources_df(resources, projects)
    scheduled_tasks_df = build_scheduled_tasks_df(
        result, project_id_filter=selected_proj
    )

    mo.vstack(
        [
            mo.md(
                f"**Solver Status:** `{result.status}` | "
                f"**Portfolio Start:** `{result.schedule_start_date}` | "
                f"**Portfolio End:** `{result.schedule_end_date}` | "
                f"**Total Calendar Span:** `{result.makespan_days}` days | "
                f"**Total Effort (5 Projects):** `{result.total_hours}` hours | "
                f"**Total Task Resource Distance:** `{result.total_distance_km}` km"
            ),
            mo.md("### Project Details Summary (All 5 Projects)"),
            mo.ui.table(projects_df),
            mo.ui.altair_chart(task_chart),
            mo.ui.altair_chart(resource_chart),
            mo.md(f"### Assignment Hours per Resource per Day (Filter: `{selected_proj}`)"),
            mo.ui.table(daily_resource_matrix_df),
            mo.md(f"### Detailed Daily Task-Resource Assignments (Filter: `{selected_proj}`)"),
            mo.ui.table(daily_df),
            mo.md("### 12 Resources, Postal Codes & Distance (km) to Each Project"),
            mo.ui.table(resources_df),
            mo.md(f"### Scheduled Tasks & Subtasks (Filter: `{selected_proj}`)"),
            mo.ui.table(scheduled_tasks_df),
        ]
    )


if __name__ == "__main__":
    app.run()
