"""Functions to build Polars tables and Altair charts from schedule results."""

import altair as alt
import polars as pl

from src.models import Project, Resource, ScheduleResult
from src.postal_codes import compute_postal_distance_km


def build_projects_df(result: ScheduleResult) -> pl.DataFrame:
    """Build a summary table with the details of all scheduled projects."""
    return pl.DataFrame(
        [
            {
                "project_id": p.project_id,
                "project_name": p.project_name,
                "city": p.city,
                "postal_code": p.postal_code,
                "status": p.status,
                "start_date": p.start_date,
                "end_date": p.end_date,
                "makespan_days": p.makespan_days,
                "main_tasks": p.main_task_count,
                "leaf_tasks": p.leaf_task_count,
                "total_hours": p.total_hours,
                "total_distance_km": p.total_distance_km,
                "assigned_resources": p.assigned_resources,
            }
            for p in result.projects
        ]
    )


def build_resources_df(
    resources: list[Resource], projects: list[Project] | None = None
) -> pl.DataFrame:
    """Build a table of resources, their skills, Dutch postal code, weekly availability, and distance to each project."""
    rows = []
    for r in resources:
        row: dict[str, object] = {
            "id": r.id,
            "resource": r.name,
            "city": r.city,
            "postal_code": r.postal_code,
            "skills": ", ".join(r.skills),
            "availability": r.availability_label,
            "hours_per_day": r.hours_per_day,
        }
        if projects:
            for p in projects:
                row[f"{p.id} ({p.city}) km"] = compute_postal_distance_km(
                    p.postal_code, r.postal_code
                )
        rows.append(row)
    return pl.DataFrame(rows)


def build_scheduled_tasks_df(
    result: ScheduleResult, project_id_filter: str = "ALL"
) -> pl.DataFrame:
    """Build a table of scheduled tasks and subtasks (for all projects or a single selected project)."""
    tasks = [
        t
        for t in result.tasks
        if project_id_filter == "ALL" or t.project_id == project_id_filter
    ]
    return pl.DataFrame(
        [
            {
                "project_id": t.project_id,
                "project_postal_code": t.project_postal_code,
                "id": t.id,
                "task": t.name,
                "parent_id": t.parent_id or "—",
                "task_type": t.task_type,
                "skill": t.required_skill,
                "resource": t.assigned_resource,
                "resource_postal_code": t.resource_postal_code,
                "distance_km": t.distance_km,
                "hours_needed": t.hours_needed,
                "work_days": t.work_days,
                "calendar_days": t.calendar_days,
                "start_date": t.start_date,
                "end_date": t.end_date,
            }
            for t in tasks
        ]
    )


def build_daily_assignments_df(
    result: ScheduleResult, project_id_filter: str = "ALL"
) -> pl.DataFrame:
    """Build a detailed day-by-day table of task-resource-hour assignments."""
    assignments = [
        a
        for a in result.daily_assignments
        if project_id_filter == "ALL" or a.project_id == project_id_filter
    ]
    return pl.DataFrame(
        [
            {
                "date": a.date,
                "weekday": a.weekday,
                "project_id": a.project_id,
                "project_postal_code": a.project_postal_code,
                "resource": a.resource_name,
                "resource_postal_code": a.resource_postal_code,
                "distance_km": a.distance_km,
                "task_id": a.task_id,
                "task": a.task_name,
                "skill": a.skill,
                "hours": a.hours,
            }
            for a in assignments
        ]
    )


def build_daily_resource_matrix_df(
    result: ScheduleResult,
    resources: list[Resource],
    project_id_filter: str = "ALL",
) -> pl.DataFrame:
    """Build a matrix table of assigned hours per resource per calendar day."""
    hours_by_date_res: dict[tuple, int] = {}
    weekdays_by_date: dict = {}
    for a in result.daily_assignments:
        if project_id_filter != "ALL" and a.project_id != project_id_filter:
            continue
        weekdays_by_date[a.date] = a.weekday
        key = (a.date, a.resource_name)
        hours_by_date_res[key] = hours_by_date_res.get(key, 0) + a.hours

    unique_dates = sorted(weekdays_by_date.keys())
    return pl.DataFrame(
        [
            {
                "date": d,
                "weekday": weekdays_by_date[d],
                **{
                    r.name: hours_by_date_res.get((d, r.name), 0)
                    for r in resources
                },
                "total_hours": sum(
                    hours_by_date_res.get((d, r.name), 0) for r in resources
                ),
            }
            for d in unique_dates
        ]
    )


def build_task_gantt_chart(
    result: ScheduleResult, project_id_filter: str = "ALL"
) -> alt.Chart:
    """Build an interactive Altair Gantt chart for scheduled tasks and subtasks."""
    df = build_scheduled_tasks_df(result, project_id_filter=project_id_filter)
    row_order = [
        t.name
        for t in result.tasks
        if project_id_filter == "ALL" or t.project_id == project_id_filter
    ]
    chart_height = max(len(row_order) * 20, 260)

    return (
        alt.Chart(df)
        .mark_bar(cornerRadius=3)
        .encode(
            x=alt.X("start_date:T", title="Date"),
            x2="end_date:T",
            y=alt.Y(
                "task:N",
                title="Task / Subtask",
                sort=row_order,
                axis=alt.Axis(labelLimit=360),
            ),
            color=alt.Color(
                "task_type:N",
                title="Task Type",
                scale=alt.Scale(
                    domain=[
                        "Main Task (with Subtasks)",
                        "Main Task (Simple)",
                        "Subtask",
                        "Wait Subtask",
                    ],
                    range=["#334155", "#0d9488", "#2563eb", "#cbd5e1"],
                ),
            ),
            opacity=alt.condition(
                alt.datum.task_type == "Wait Subtask",
                alt.value(0.55),
                alt.value(0.95),
            ),
            tooltip=[
                alt.Tooltip("project_id:N", title="Project"),
                alt.Tooltip("project_postal_code:N", title="Project Postal Code"),
                alt.Tooltip("task:N", title="Task / Subtask"),
                alt.Tooltip("task_type:N", title="Type"),
                alt.Tooltip("skill:N", title="Required Skill"),
                alt.Tooltip("resource:N", title="Assigned Resource"),
                alt.Tooltip("resource_postal_code:N", title="Resource Postal Code"),
                alt.Tooltip("distance_km:Q", title="Distance to Project (km)"),
                alt.Tooltip("hours_needed:Q", title="Resource Hours"),
                alt.Tooltip("work_days:Q", title="Work Days"),
                alt.Tooltip("calendar_days:Q", title="Calendar Span (days)"),
                alt.Tooltip("start_date:T", title="Start Date", format="%a %Y-%m-%d"),
                alt.Tooltip("end_date:T", title="End Date", format="%a %Y-%m-%d"),
            ],
        )
        .properties(
            title=(
                f"Project Schedule by Task — Filter: {project_id_filter} "
                f"({result.schedule_start_date} → {result.schedule_end_date}, "
                f"{result.makespan_days}d span, {result.total_hours}h total, "
                f"{result.total_distance_km} km total resource distance)"
            ),
            height=chart_height,
        )
    )


def build_resource_timeline_chart(
    result: ScheduleResult,
    resources: list[Resource],
    project_id_filter: str = "ALL",
) -> alt.Chart:
    """Build an interactive Altair timeline chart showing utilization per resource across projects."""
    df = build_scheduled_tasks_df(result, project_id_filter=project_id_filter)
    active_df = df.filter(
        pl.col("task_type").is_in(["Main Task (Simple)", "Subtask"])
    )
    res_order = [r.name for r in resources]

    return (
        alt.Chart(active_df)
        .mark_bar(cornerRadius=3, stroke="#ffffff", strokeWidth=1)
        .encode(
            x=alt.X("start_date:T", title="Date"),
            x2="end_date:T",
            y=alt.Y(
                "resource:N",
                title="Resource",
                sort=res_order,
                axis=alt.Axis(labelLimit=240),
            ),
            color=alt.Color(
                "project_id:N",
                title="Project",
                scale=alt.Scale(
                    domain=["PRJ-001", "PRJ-002", "PRJ-003", "PRJ-004", "PRJ-005"],
                    range=["#2563eb", "#0d9488", "#d97706", "#9333ea", "#e11d48"],
                ),
            ),
            tooltip=[
                alt.Tooltip("resource:N", title="Resource"),
                alt.Tooltip("resource_postal_code:N", title="Resource Postal Code"),
                alt.Tooltip("project_id:N", title="Project"),
                alt.Tooltip("project_postal_code:N", title="Project Postal Code"),
                alt.Tooltip("distance_km:Q", title="Distance to Project (km)"),
                alt.Tooltip("task:N", title="Task / Subtask"),
                alt.Tooltip("skill:N", title="Skill Used"),
                alt.Tooltip("hours_needed:Q", title="Hours Needed"),
                alt.Tooltip("work_days:Q", title="Active Work Days"),
                alt.Tooltip("calendar_days:Q", title="Calendar Span (incl. off-days)"),
                alt.Tooltip("start_date:T", title="Start Date", format="%a %Y-%m-%d"),
                alt.Tooltip("end_date:T", title="End Date", format="%a %Y-%m-%d"),
            ],
        )
        .properties(
            title=f"Resource Assignment & Utilization Timeline across Projects (Filter: {project_id_filter})",
            height=340,
        )
    )
