"""Domain models for projects, tasks, resources, and solved schedules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@dataclass(frozen=True)
class Resource:
    """A resource with skills, home postal code (Dutch), and weekly availability.

    - `skills`: e.g. `["skill1"]`, `["skill2", "skill3"]`
    - `postal_code`: Dutch postal code (`"NNNN AA"`), e.g. `"3511 JC"`
    - `city`: Dutch city name for display
    - `working_days`: weekdays `0..6` where `0=Mon, 1=Tue, ..., 6=Sun`
        (e.g. `[0, 1, 2, 3]` for Monday to Thursday)
    - `hours_per_day`: active working hours per working day (e.g. 8)
    """

    id: str
    name: str
    skills: list[str]
    postal_code: str = "3511 JC"
    city: str = "Utrecht"
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
class Project:
    """A project executed at a Dutch postal code address with its own task schedule."""

    id: str
    name: str
    postal_code: str
    city: str
    start_date: date
    tasks: list[Task] = field(default_factory=list)


@dataclass(frozen=True)
class ProjectSummary:
    """Solved summary details for a single `Project`."""

    project_id: str
    project_name: str
    city: str
    postal_code: str
    status: str
    start_date: date
    end_date: date | None
    makespan_days: int | None
    main_task_count: int
    leaf_task_count: int
    total_hours: int
    total_distance_km: float
    assigned_resources: str


@dataclass(frozen=True)
class ScheduledTask:
    """Solved schedule bar for a single task, main task, or subtask within a project."""

    project_id: str
    project_name: str
    project_postal_code: str
    id: str
    name: str
    parent_id: str | None
    task_type: str  # "Main Task (with Subtasks)", "Main Task (Simple)", "Subtask", "Wait Subtask"
    required_skill: str
    assigned_resource: str
    resource_postal_code: str
    distance_km: float | None
    hours_needed: int
    work_days: int
    calendar_days: int
    start_day: int
    end_day: int
    start_date: date
    end_date: date


@dataclass(frozen=True)
class DailyAssignment:
    """Hours assigned to a resource on a single calendar date for a project task."""

    date: date
    weekday: str
    project_id: str
    project_name: str
    project_postal_code: str
    resource_id: str
    resource_name: str
    resource_postal_code: str
    distance_km: float
    task_id: str
    task_name: str
    skill: str
    hours: int


@dataclass(frozen=True)
class ScheduleResult:
    """Output returned by the CP-SAT solver for one or more `Project` schedules."""

    status: str
    makespan_days: int | None
    total_hours: int
    total_distance_km: float
    schedule_start_date: date
    schedule_end_date: date | None
    projects: list[ProjectSummary]
    tasks: list[ScheduledTask]
    daily_assignments: list[DailyAssignment] = field(default_factory=list)
