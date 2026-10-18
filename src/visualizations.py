"""Functions to build Polars tables and Altair charts from schedule results."""

import altair as alt
import polars as pl

from src.models import Resource, ScheduleResult


def build_resources_df(resources: list[Resource]) -> pl.DataFrame:
    """Build a table of resources, their skills, and weekly availability."""
    return pl.DataFrame(
        [
            {
                "id": r.id,
                "resource": r.name,
                "skills": ", ".join(r.skills),
                "availability": r.availability_label,
                "hours_per_day": r.hours_per_day,
            }
            for r in resources
        ]
    )


def build_scheduled_tasks_df(result: ScheduleResult) -> pl.DataFrame:
    """Build a table of all scheduled tasks and subtasks."""
    return pl.DataFrame(
        [
            {
                "id": t.id,
                "task": t.name,
                "parent_id": t.parent_id or "—",
                "task_type": t.task_type,
                "skill": t.required_skill,
                "resource": t.assigned_resource,
                "hours_needed": t.hours_needed,
                "work_days": t.work_days,
                "calendar_days": t.calendar_days,
                "start_date": t.start_date,
                "end_date": t.end_date,
            }
            for t in result.tasks
        ]
    )


def build_daily_assignments_df(result: ScheduleResult) -> pl.DataFrame:
    """Build a detailed day-by-day table of task-resource-hour assignments."""
    return pl.DataFrame(
        [
            {
                "date": a.date,
                "weekday": a.weekday,
                "resource": a.resource_name,
                "task_id": a.task_id,
                "task": a.task_name,
                "skill": a.skill,
                "hours": a.hours,
            }
            for a in result.daily_assignments
        ]
    )


def build_daily_resource_matrix_df(
    result: ScheduleResult, resources: list[Resource]
) -> pl.DataFrame:
    """Build a matrix table of assigned hours per resource per calendar day."""
    hours_by_date_res: dict[tuple, int] = {}
    weekdays_by_date: dict = {}
    for a in result.daily_assignments:
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


def build_task_gantt_chart(result: ScheduleResult) -> alt.Chart:
    """Build an interactive Altair Gantt chart for all tasks and subtasks."""
    df = build_scheduled_tasks_df(result)
    row_order = [t.name for t in result.tasks]

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
                axis=alt.Axis(labelLimit=340),
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
                alt.Tooltip("task:N", title="Task / Subtask"),
                alt.Tooltip("task_type:N", title="Type"),
                alt.Tooltip("skill:N", title="Required Skill"),
                alt.Tooltip("resource:N", title="Assigned Resource"),
                alt.Tooltip("hours_needed:Q", title="Resource Hours"),
                alt.Tooltip("work_days:Q", title="Work Days"),
                alt.Tooltip("calendar_days:Q", title="Calendar Span (days)"),
                alt.Tooltip("start_date:T", title="Start Date", format="%a %Y-%m-%d"),
                alt.Tooltip("end_date:T", title="End Date", format="%a %Y-%m-%d"),
            ],
        )
        .properties(
            title=(
                f"Project Schedule by Task ({result.project_start_date} → {result.project_end_date}, "
                f"{result.makespan_days} calendar days, {result.total_hours} total work hours)"
            ),
            height=680,
        )
    )


def build_resource_timeline_chart(
    result: ScheduleResult, resources: list[Resource]
) -> alt.Chart:
    """Build an interactive Altair timeline chart showing utilization per resource."""
    df = build_scheduled_tasks_df(result)
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
                axis=alt.Axis(labelLimit=200),
            ),
            color=alt.Color(
                "skill:N",
                title="Skill Used",
                scale=alt.Scale(
                    domain=["skill1", "skill2", "skill3"],
                    range=["#2563eb", "#d97706", "#9333ea"],
                ),
            ),
            tooltip=[
                alt.Tooltip("resource:N", title="Resource"),
                alt.Tooltip("task:N", title="Task / Subtask"),
                alt.Tooltip("task_type:N", title="Type"),
                alt.Tooltip("skill:N", title="Skill Used"),
                alt.Tooltip("hours_needed:Q", title="Hours Needed"),
                alt.Tooltip("work_days:Q", title="Active Work Days"),
                alt.Tooltip("calendar_days:Q", title="Calendar Span (incl. off-days)"),
                alt.Tooltip("start_date:T", title="Start Date", format="%a %Y-%m-%d"),
                alt.Tooltip("end_date:T", title="End Date", format="%a %Y-%m-%d"),
            ],
        )
        .properties(
            title="Resource Assignment & Utilization Timeline",
            height=180,
        )
    )
