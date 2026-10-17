"""Task scheduler using OR-Tools CP-SAT with Prepare -> Wait -> Handle phases."""

from dataclasses import dataclass, field
from datetime import date, timedelta
import math
from ortools.sat.python import cp_model


@dataclass(frozen=True)
class SubtaskSpec:
    """A subtask inside a Main Task with Prepare -> Wait -> Handle phases.

    - `prepare_hours`: Active resource hours to prepare/initiate the subtask.
    - `wait_days`: Minimum passive waiting days (uses 0 resource hours).
    - `handle_hours`: Active resource hours to handle/complete the subtask after waiting.
    """

    id: str
    name: str
    prepare_hours: int
    wait_days: int
    handle_hours: int


@dataclass(frozen=True)
class Task:
    """Input definition of a task (either a simple task or a Main Task with subtasks)."""

    id: str
    name: str
    hours_needed: int = 0
    predecessors: list[str] = field(default_factory=list)
    subtasks: list[SubtaskSpec] = field(default_factory=list)
    resource: str = "Resource 1"


@dataclass(frozen=True)
class ScheduledPhase:
    """Solved schedule bar for a single phase (Task, Main Task, Prepare, Wait, or Handle)."""

    task_id: str
    row_name: str
    phase: str  # "Main Task", "Task", "Prepare", "Wait", "Handle"
    hours_needed: int
    duration_days: int
    start_day: int
    end_day: int
    start_date: date
    end_date: date
    resource: str


@dataclass(frozen=True)
class ScheduleResult:
    """Output returned by the CP-SAT solver."""

    status: str
    makespan_days: int | None
    total_hours: int
    project_start_date: date
    project_end_date: date | None
    phases: list[ScheduledPhase]


def hours_to_days(hours: int, hours_per_day: int) -> int:
    """Convert resource work hours into whole working days."""
    if hours <= 0:
        return 0
    return math.ceil(hours / hours_per_day)


def solve_schedule(
    tasks: list[Task],
    project_start_date: date | None = None,
    hours_per_day: int = 8,
    time_limit_seconds: float = 5.0,
) -> ScheduleResult:
    """Solve a schedule where a single resource executes tasks and parallel subtasks (Prepare -> Wait -> Handle).

    - Active phases (`Task`, `Prepare`, `Handle`) require the resource and cannot overlap (`add_no_overlap`).
    - Passive `Wait` phases require 0 resource hours and can run in parallel with any active work.
    - Within each subtask: `Prepare` -> `Wait` (at least `wait_days`) -> `Handle` are contiguous.
    - A Main Task starts when its earliest subtask starts and ends when all its subtasks finish.
    """
    start_anchor = project_start_date or date.today()
    model = cp_model.CpModel()

    # Calculate a safe upper bound (horizon) in days
    horizon = 0
    total_hours = 0
    for task in tasks:
        if task.subtasks:
            for sub in task.subtasks:
                horizon += (
                    hours_to_days(sub.prepare_hours, hours_per_day)
                    + sub.wait_days
                    + hours_to_days(sub.handle_hours, hours_per_day)
                )
                total_hours += sub.prepare_hours + sub.handle_hours
        else:
            horizon += hours_to_days(task.hours_needed, hours_per_day)
            total_hours += task.hours_needed

    horizon = max(horizon, 1)

    task_starts: dict[str, cp_model.IntVar] = {}
    task_ends: dict[str, cp_model.IntVar] = {}
    task_durations: dict[str, cp_model.IntVar | int] = {}

    # Active resource intervals (cannot overlap because one resource executes the schedule)
    active_resource_intervals: list[cp_model.IntervalVar] = []

    # Keep references to subtask phase variables so we can extract solved values
    subtask_vars: dict[str, dict[str, cp_model.IntVar | int]] = {}

    for task in tasks:
        t_start = model.new_int_var(0, horizon, f"start_{task.id}")
        t_end = model.new_int_var(0, horizon, f"end_{task.id}")
        task_starts[task.id] = t_start
        task_ends[task.id] = t_end

        if not task.subtasks:
            # Simple sequential task
            dur_days = hours_to_days(task.hours_needed, hours_per_day)
            interval = model.new_interval_var(
                t_start, dur_days, t_end, f"interval_{task.id}"
            )
            task_durations[task.id] = dur_days
            if dur_days > 0:
                active_resource_intervals.append(interval)
        else:
            # Main Task with parallel subtasks (each split into Prepare -> Wait -> Handle)
            t_dur = model.new_int_var(0, horizon, f"dur_{task.id}")
            model.new_interval_var(t_start, t_dur, t_end, f"interval_{task.id}")
            task_durations[task.id] = t_dur

            sub_starts: list[cp_model.IntVar] = []
            sub_ends: list[cp_model.IntVar] = []

            for sub in task.subtasks:
                prep_days = hours_to_days(sub.prepare_hours, hours_per_day)
                handle_days = hours_to_days(sub.handle_hours, hours_per_day)

                # Phase 1: Prepare (active resource work)
                p_start = model.new_int_var(0, horizon, f"prep_start_{sub.id}")
                p_end = model.new_int_var(0, horizon, f"prep_end_{sub.id}")
                p_interval = model.new_interval_var(
                    p_start, prep_days, p_end, f"prep_interval_{sub.id}"
                )
                if prep_days > 0:
                    active_resource_intervals.append(p_interval)

                # Phase 2: Wait (passive lead time, 0 resource needed, at least sub.wait_days)
                # Starts immediately when Prepare finishes; can stretch if resource is busy when wait ends
                w_start = p_end
                w_dur = model.new_int_var(sub.wait_days, horizon, f"wait_dur_{sub.id}")
                w_end = model.new_int_var(0, horizon, f"wait_end_{sub.id}")
                model.new_interval_var(
                    w_start, w_dur, w_end, f"wait_interval_{sub.id}"
                )

                # Phase 3: Handle (active resource work, starts when Wait ends)
                h_start = w_end
                h_end = model.new_int_var(0, horizon, f"handle_end_{sub.id}")
                h_interval = model.new_interval_var(
                    h_start, handle_days, h_end, f"handle_interval_{sub.id}"
                )
                if handle_days > 0:
                    active_resource_intervals.append(h_interval)

                sub_starts.append(p_start)
                sub_ends.append(h_end)

                subtask_vars[sub.id] = {
                    "p_start": p_start,
                    "p_end": p_end,
                    "p_days": prep_days,
                    "w_start": w_start,
                    "w_end": w_end,
                    "w_dur": w_dur,
                    "h_start": h_start,
                    "h_end": h_end,
                    "h_days": handle_days,
                }

            # Main Task starts when the first subtask starts and ends when all subtasks finish
            model.add_min_equality(t_start, sub_starts)
            model.add_max_equality(t_end, sub_ends)

    # Precedence constraints between tasks / main tasks
    for task in tasks:
        for pred_id in task.predecessors:
            model.add(task_starts[task.id] >= task_ends[pred_id])

    # Single Resource Constraint: active work phases (Task, Prepare, Handle) cannot overlap!
    # Passive Wait phases are NOT in this list, so the resource works on other subtasks while waiting.
    if active_resource_intervals:
        model.add_no_overlap(active_resource_intervals)

    # Objective: Minimize total project makespan, finish tasks as early as possible,
    # and start subtask Prepare/Handle phases as early as possible.
    makespan = model.new_int_var(0, horizon, "makespan")
    model.add_max_equality(makespan, list(task_ends.values()))
    sub_phase_vars = [
        sv["p_start"] for sv in subtask_vars.values()
    ] + [
        sv["h_end"] for sv in subtask_vars.values()
    ]
    model.minimize(
        makespan * 1000
        + sum(task_ends.values()) * 10
        + sum(sub_phase_vars)
    )

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    status_code = solver.solve(model)
    status_name = solver.status_name(status_code)

    if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return ScheduleResult(
            status=status_name,
            makespan_days=None,
            total_hours=total_hours,
            project_start_date=start_anchor,
            project_end_date=None,
            phases=[],
        )

    solved_makespan = solver.value(makespan)
    phases: list[ScheduledPhase] = []

    for task in tasks:
        t_s = solver.value(task_starts[task.id])
        t_e = solver.value(task_ends[task.id])
        t_d = solver.value(task_durations[task.id])

        if not task.subtasks:
            phases.append(
                ScheduledPhase(
                    task_id=task.id,
                    row_name=task.name,
                    phase="Task",
                    hours_needed=task.hours_needed,
                    duration_days=t_d,
                    start_day=t_s,
                    end_day=t_e,
                    start_date=start_anchor + timedelta(days=t_s),
                    end_date=start_anchor + timedelta(days=t_e),
                    resource=task.resource,
                )
            )
        else:
            main_hours = sum(
                sub.prepare_hours + sub.handle_hours for sub in task.subtasks
            )
            phases.append(
                ScheduledPhase(
                    task_id=task.id,
                    row_name=task.name,
                    phase="Main Task",
                    hours_needed=main_hours,
                    duration_days=t_d,
                    start_day=t_s,
                    end_day=t_e,
                    start_date=start_anchor + timedelta(days=t_s),
                    end_date=start_anchor + timedelta(days=t_e),
                    resource=task.resource,
                )
            )
            for sub in task.subtasks:
                sv = subtask_vars[sub.id]
                p_s = solver.value(sv["p_start"])
                p_e = solver.value(sv["p_end"])
                w_s = solver.value(sv["w_start"])
                w_e = solver.value(sv["w_end"])
                w_d = solver.value(sv["w_dur"])
                h_s = solver.value(sv["h_start"])
                h_e = solver.value(sv["h_end"])

                phases.append(
                    ScheduledPhase(
                        task_id=sub.id,
                        row_name=sub.name,
                        phase="Prepare",
                        hours_needed=sub.prepare_hours,
                        duration_days=int(sv["p_days"]),
                        start_day=p_s,
                        end_day=p_e,
                        start_date=start_anchor + timedelta(days=p_s),
                        end_date=start_anchor + timedelta(days=p_e),
                        resource=task.resource,
                    )
                )
                phases.append(
                    ScheduledPhase(
                        task_id=sub.id,
                        row_name=sub.name,
                        phase="Wait",
                        hours_needed=0,
                        duration_days=w_d,
                        start_day=w_s,
                        end_day=w_e,
                        start_date=start_anchor + timedelta(days=w_s),
                        end_date=start_anchor + timedelta(days=w_e),
                        resource=task.resource,
                    )
                )
                phases.append(
                    ScheduledPhase(
                        task_id=sub.id,
                        row_name=sub.name,
                        phase="Handle",
                        hours_needed=sub.handle_hours,
                        duration_days=int(sv["h_days"]),
                        start_day=h_s,
                        end_day=h_e,
                        start_date=start_anchor + timedelta(days=h_s),
                        end_date=start_anchor + timedelta(days=h_e),
                        resource=task.resource,
                    )
                )

    return ScheduleResult(
        status=status_name,
        makespan_days=solved_makespan,
        total_hours=total_hours,
        project_start_date=start_anchor,
        project_end_date=start_anchor + timedelta(days=solved_makespan),
        phases=phases,
    )


def build_sample_tasks(resource: str = "Resource 1") -> list[Task]:
    """Create a realistic schedule with 6 simple tasks and 4 Main Tasks (13 parallel subtasks)."""
    return [
        Task(
            id="T1",
            name="T1: Project Kickoff",
            hours_needed=16,
            resource=resource,
        ),
        Task(
            id="T2",
            name="T2: Requirements & Architecture",
            hours_needed=24,
            predecessors=["T1"],
            resource=resource,
        ),
        Task(
            id="M1",
            name="M1: Procurement & Vendor Setup (Main)",
            predecessors=["T2"],
            resource=resource,
            subtasks=[
                SubtaskSpec(id="M1.1", name="  ↳ M1.1: Cloud Infrastructure", prepare_hours=8, wait_days=4, handle_hours=16),
                SubtaskSpec(id="M1.2", name="  ↳ M1.2: Security Certificates", prepare_hours=8, wait_days=6, handle_hours=8),
                SubtaskSpec(id="M1.3", name="  ↳ M1.3: Third-Party API Keys", prepare_hours=8, wait_days=3, handle_hours=8),
            ],
        ),
        Task(
            id="T3",
            name="T3: Core Data Model",
            hours_needed=16,
            predecessors=["M1"],
            resource=resource,
        ),
        Task(
            id="M2",
            name="M2: Core Module Development (Main)",
            predecessors=["T3"],
            resource=resource,
            subtasks=[
                SubtaskSpec(id="M2.1", name="  ↳ M2.1: Auth & Permissions", prepare_hours=16, wait_days=3, handle_hours=16),
                SubtaskSpec(id="M2.2", name="  ↳ M2.2: Billing Integration", prepare_hours=8, wait_days=5, handle_hours=16),
                SubtaskSpec(id="M2.3", name="  ↳ M2.3: Notification Service", prepare_hours=8, wait_days=2, handle_hours=8),
                SubtaskSpec(id="M2.4", name="  ↳ M2.4: Audit Logging", prepare_hours=8, wait_days=3, handle_hours=8),
            ],
        ),
        Task(
            id="T4",
            name="T4: System Integration",
            hours_needed=16,
            predecessors=["M2"],
            resource=resource,
        ),
        Task(
            id="M3",
            name="M3: External Testing & Audits (Main)",
            predecessors=["T4"],
            resource=resource,
            subtasks=[
                SubtaskSpec(id="M3.1", name="  ↳ M3.1: Penetration Test", prepare_hours=8, wait_days=5, handle_hours=16),
                SubtaskSpec(id="M3.2", name="  ↳ M3.2: Performance Load Test", prepare_hours=16, wait_days=3, handle_hours=8),
                SubtaskSpec(id="M3.3", name="  ↳ M3.3: Accessibility Review", prepare_hours=8, wait_days=4, handle_hours=8),
            ],
        ),
        Task(
            id="T5",
            name="T5: Release Candidate Sign-off",
            hours_needed=8,
            predecessors=["M3"],
            resource=resource,
        ),
        Task(
            id="M4",
            name="M4: Rollout & Store Approvals (Main)",
            predecessors=["T5"],
            resource=resource,
            subtasks=[
                SubtaskSpec(id="M4.1", name="  ↳ M4.1: App Store Review", prepare_hours=8, wait_days=4, handle_hours=8),
                SubtaskSpec(id="M4.2", name="  ↳ M4.2: Customer Migration", prepare_hours=16, wait_days=3, handle_hours=16),
                SubtaskSpec(id="M4.3", name="  ↳ M4.3: Partner Onboarding", prepare_hours=8, wait_days=5, handle_hours=8),
            ],
        ),
        Task(
            id="T6",
            name="T6: Handover & Project Closure",
            hours_needed=16,
            predecessors=["M4"],
            resource=resource,
        ),
    ]

