"""Domain models and sample task data for scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@dataclass(frozen=True)
class Resource:
    """A resource with skills and weekly availability.

    - `skills`: e.g. `["skill1"]`, `["skill2", "skill3"]`
    - `working_days`: weekdays `0..6` where `0=Mon, 1=Tue, ..., 6=Sun`
        (e.g. `[0, 1, 2, 3]` for Monday to Thursday)
    - `hours_per_day`: active working hours per working day (e.g. 8)
    """

    id: str
    name: str
    skills: list[str]
    working_days: list[int] = field(default_factory=lambda: [0, 1, 2, 3])
    hours_per_day: int = 8

    @property
    def availability_label(self) -> str:
        days_str = ", ".join(WEEKDAY_NAMES[d] for d in sorted(self.working_days))
        return f"{days_str} ({self.hours_per_day}h/day)"


@dataclass(frozen=True)
class Task:
    """Unified task model: can be a task without subtasks, a Main Task with `subtasks`, or a nested subtask.

    - For a Main Task with subtasks: populate `subtasks: list[Task]`. Its start and end
      are automatically derived from its subtasks (`min(start)` to `max(end)`).
    - For an active leaf task/subtask: set `hours_needed > 0` and `required_skill`.
    - For a passive wait leaf task/subtask (0 resource hours): set `hours_needed = 0` and `wait_days > 0`.
    """

    id: str
    name: str
    required_skill: str | None = "skill1"
    hours_needed: int = 0
    wait_days: int = 0
    predecessors: list[str] = field(default_factory=list)
    subtasks: list[Task] = field(default_factory=list)


@dataclass(frozen=True)
class ScheduledTask:
    """Solved schedule bar for a single task, main task, or subtask."""

    id: str
    name: str
    parent_id: str | None
    task_type: str  # "Main Task (with Subtasks)", "Main Task (Simple)", "Subtask", "Wait Subtask"
    required_skill: str
    assigned_resource: str
    hours_needed: int
    work_days: int
    calendar_days: int
    start_day: int
    end_day: int
    start_date: date
    end_date: date


@dataclass(frozen=True)
class DailyAssignment:
    """Hours assigned to a resource on a single calendar date."""

    date: date
    weekday: str
    resource_id: str
    resource_name: str
    task_id: str
    task_name: str
    skill: str
    hours: int


@dataclass(frozen=True)
class ScheduleResult:
    """Output returned by the CP-SAT solver."""

    status: str
    makespan_days: int | None
    total_hours: int
    project_start_date: date
    project_end_date: date | None
    tasks: list[ScheduledTask]
    daily_assignments: list[DailyAssignment] = field(default_factory=list)
