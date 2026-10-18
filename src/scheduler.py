"""CP-SAT solver logic for multi-Project, unified nested Task, and Resource scheduling."""

import math
from datetime import date, timedelta

from ortools.sat.python import cp_model

from src.models import (
    WEEKDAY_NAMES,
    DailyAssignment,
    Project,
    ProjectSummary,
    Resource,
    ScheduledTask,
    ScheduleResult,
    Task,
)
from src.postal_codes import compute_postal_distance_cost, compute_postal_distance_km


def hours_to_work_days(hours: int, hours_per_day: int) -> int:
    """Convert resource work hours into whole working days for a specific resource."""
    if hours <= 0:
        return 0
    return math.ceil(hours / hours_per_day)


def compute_allowed_spans(
    start_anchor: date,
    horizon: int,
    work_days_needed: int,
    working_weekdays: set[int],
    min_start_day: int = 0,
) -> list[tuple[int, int, int]]:
    """Precompute valid `(start_day, calendar_span, end_day)` tuples for a resource.

    A task requiring `work_days_needed` working days must start on a working day of
    the resource (at or after `min_start_day`) and pauses over off-days (e.g., Fri-Sun
    for a Mon-Thu resource) until `work_days_needed` working days have been completed.
    """
    if work_days_needed <= 0:
        return [(d, 0, d) for d in range(min_start_day, horizon + 1)]

    allowed: list[tuple[int, int, int]] = []
    for s in range(min_start_day, horizon):
        s_date = start_anchor + timedelta(days=s)
        if s_date.weekday() not in working_weekdays:
            continue

        remaining = work_days_needed
        cur = s
        while remaining > 0 and cur < horizon * 2:
            cur_date = start_anchor + timedelta(days=cur)
            if cur_date.weekday() in working_weekdays:
                remaining -= 1
            cur += 1

        if remaining == 0 and cur <= horizon:
            end_day = cur
            span = end_day - s
            allowed.append((s, span, end_day))

    return allowed


def solve_schedule(
    projects: list[Project],
    resources: list[Resource],
    time_limit_seconds: float = 5.0,
) -> ScheduleResult:
    """Solve a schedule for multiple `Project` instances sharing a pool of skilled resources."""
    if not projects:
        today = date.today()
        return ScheduleResult(
            status="OPTIMAL",
            makespan_days=0,
            total_hours=0,
            total_distance_km=0.0,
            schedule_start_date=today,
            schedule_end_date=today,
            projects=[],
            tasks=[],
            daily_assignments=[],
        )

    start_anchor = min(p.start_date for p in projects)
    model = cp_model.CpModel()

    # Flatten all leaf tasks across all projects to compute safe calendar horizon
    all_leaf_tasks: list[Task] = []
    for proj in projects:
        for task in proj.tasks:
            if task.subtasks:
                all_leaf_tasks.extend(task.subtasks)
            else:
                all_leaf_tasks.append(task)

    min_hpd = min((r.hours_per_day for r in resources), default=8)
    total_hours = sum(t.hours_needed for t in all_leaf_tasks)
    raw_work_days = sum(
        hours_to_work_days(t.hours_needed, min_hpd) + t.wait_days
        for t in all_leaf_tasks
    )
    max_proj_offset = max((p.start_date - start_anchor).days for p in projects)

    # Parallel resource pool: scale raw work days by available resources per skill
    parallel_factor = max(len(resources) // 3, 1)
    horizon = max(
        int((raw_work_days / parallel_factor) * 2.5) + max_proj_offset + 18,
        35,
    )

    # Precompute distance (in km and integer 0.1km cost units) for every (project.id, resource.id)
    distance_km_by_proj_res: dict[tuple[str, str], float] = {}
    distance_cost_by_proj_res: dict[tuple[str, str], int] = {}
    for proj in projects:
        for res in resources:
            distance_km_by_proj_res[(proj.id, res.id)] = compute_postal_distance_km(
                proj.postal_code, res.postal_code
            )
            distance_cost_by_proj_res[(proj.id, res.id)] = compute_postal_distance_cost(
                proj.postal_code, res.postal_code
            )

    # Index resources by skill
    resources_by_skill: dict[str, list[Resource]] = {}
    for res in resources:
        for skill in res.skills:
            resources_by_skill.setdefault(skill, []).append(res)

    # Cache allowed `(start, span, end)` tables per `(resource_id, work_days_needed, min_start_day)`
    span_table_cache: dict[tuple[str, int, int], list[tuple[int, int, int]]] = {}

    def get_span_table(
        res: Resource, work_days_needed: int, min_start_day: int
    ) -> list[tuple[int, int, int]]:
        key = (res.id, work_days_needed, min_start_day)
        if key not in span_table_cache:
            span_table_cache[key] = compute_allowed_spans(
                start_anchor=start_anchor,
                horizon=horizon,
                work_days_needed=work_days_needed,
                working_weekdays=set(res.working_days),
                min_start_day=min_start_day,
            )
        return span_table_cache[key]

    # Active optional intervals per resource for NoOverlap across all projects
    resource_intervals: dict[str, list[cp_model.IntervalVar]] = {
        res.id: [] for res in resources
    }

    starts: dict[str, cp_model.IntVar] = {}
    ends: dict[str, cp_model.IntVar] = {}
    spans: dict[str, cp_model.IntVar | int] = {}
    assign_vars_by_task: dict[str, dict[str, cp_model.IntVar]] = {}
    distance_cost_terms: list[cp_model.LinearExpr] = []
    project_end_vars: dict[str, cp_model.IntVar] = {}

    def add_leaf_task(proj: Project, leaf: Task, min_start_day: int) -> None:
        """Create variables and resource assignment constraints for any leaf task or subtask."""
        t_start = model.new_int_var(min_start_day, horizon, f"start_{leaf.id}")
        t_end = model.new_int_var(min_start_day, horizon, f"end_{leaf.id}")
        starts[leaf.id] = t_start
        ends[leaf.id] = t_end

        if leaf.hours_needed <= 0 or leaf.required_skill is None:
            # Passive waiting task (0 resource hours needed)
            w_days = leaf.wait_days
            model.new_interval_var(t_start, w_days, t_end, f"wait_iv_{leaf.id}")
            spans[leaf.id] = w_days
            assign_vars_by_task[leaf.id] = {}
            return

        eligible = resources_by_skill.get(leaf.required_skill, [])
        if not eligible:
            raise ValueError(
                f"No resource found with required skill '{leaf.required_skill}' for task '{leaf.id}'"
            )

        t_span = model.new_int_var(0, horizon, f"span_{leaf.id}")
        spans[leaf.id] = t_span

        assign_vars = {
            res.id: model.new_bool_var(f"assign_{leaf.id}_{res.id}")
            for res in eligible
        }
        model.add_exactly_one(list(assign_vars.values()))
        assign_vars_by_task[leaf.id] = assign_vars

        for res in eligible:
            is_assigned = assign_vars[res.id]
            w_days = hours_to_work_days(leaf.hours_needed, res.hours_per_day)
            allowed_tuples = get_span_table(res, w_days, min_start_day)

            r_start = model.new_int_var(min_start_day, horizon, f"r_start_{leaf.id}_{res.id}")
            r_span = model.new_int_var(0, horizon, f"r_span_{leaf.id}_{res.id}")
            r_end = model.new_int_var(min_start_day, horizon, f"r_end_{leaf.id}_{res.id}")
            model.add_allowed_assignments([r_start, r_span, r_end], allowed_tuples)

            model.add(t_start == r_start).only_enforce_if(is_assigned)
            model.add(t_span == r_span).only_enforce_if(is_assigned)
            model.add(t_end == r_end).only_enforce_if(is_assigned)
            if allowed_tuples:
                model.add(r_start == allowed_tuples[0][0]).only_enforce_if(~is_assigned)

            opt_interval = model.new_optional_interval_var(
                r_start, r_span, r_end, is_assigned, f"opt_iv_{leaf.id}_{res.id}"
            )
            resource_intervals[res.id].append(opt_interval)

            # Prefer the resource that lives closest to this project's postal code
            dist_cost = distance_cost_by_proj_res[(proj.id, res.id)]
            distance_cost_terms.append(is_assigned * dist_cost)

    # 1. Create variables for all projects, their main tasks, and their nested subtasks
    all_main_tasks: list[Task] = []
    for proj in projects:
        proj_offset = (proj.start_date - start_anchor).days
        for task in proj.tasks:
            all_main_tasks.append(task)
            if not task.subtasks:
                add_leaf_task(proj, task, proj_offset)
            else:
                t_start = model.new_int_var(proj_offset, horizon, f"start_{task.id}")
                t_end = model.new_int_var(proj_offset, horizon, f"end_{task.id}")
                t_span = model.new_int_var(0, horizon, f"span_{task.id}")
                model.new_interval_var(t_start, t_span, t_end, f"interval_{task.id}")
                starts[task.id] = t_start
                ends[task.id] = t_end
                spans[task.id] = t_span

                for sub in task.subtasks:
                    add_leaf_task(proj, sub, proj_offset)

                # Main Task starts when its earliest subtask starts and ends when all subtasks finish
                model.add_min_equality(t_start, [starts[sub.id] for sub in task.subtasks])
                model.add_max_equality(t_end, [ends[sub.id] for sub in task.subtasks])

        # Project end variable
        p_end = model.new_int_var(proj_offset, horizon, f"proj_end_{proj.id}")
        model.add_max_equality(p_end, [ends[t.id] for t in proj.tasks])
        project_end_vars[proj.id] = p_end

    # 2. Precedence constraints (both top-level tasks and nested subtasks within each project)
    for proj in projects:
        for task in proj.tasks:
            for pred_id in task.predecessors:
                model.add(starts[task.id] >= ends[pred_id])
            for sub in task.subtasks:
                for pred_id in sub.predecessors:
                    model.add(starts[sub.id] >= ends[pred_id])

    # 3. Per-Resource NoOverlap constraint across all projects
    for intervals in resource_intervals.values():
        if intervals:
            model.add_no_overlap(intervals)

    # 4. Objective:
    #    - Strongly prefer resources living closest to each project's postal code (weight 1,000 per 0.1km)
    #    - Minimize overall portfolio makespan (weight 5,000) and each project's completion day (weight 1,000)
    #    - Finish main tasks and subtasks as early as possible (weights 10 and 1)
    makespan = model.new_int_var(0, horizon, "makespan")
    model.add_max_equality(makespan, list(project_end_vars.values()))
    model.minimize(
        sum(distance_cost_terms) * 1_000
        + makespan * 5_000
        + sum(project_end_vars.values()) * 1_000
        + sum(ends[t.id] for t in all_main_tasks) * 10
        + sum(ends[leaf.id] for leaf in all_leaf_tasks)
    )

    # 5. Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    status_code = solver.solve(model)
    status_name = solver.status_name(status_code)

    if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return ScheduleResult(
            status=status_name,
            makespan_days=None,
            total_hours=total_hours,
            total_distance_km=0.0,
            schedule_start_date=start_anchor,
            schedule_end_date=None,
            projects=[],
            tasks=[],
            daily_assignments=[],
        )

    resource_by_id = {res.id: res for res in resources}

    def get_assigned_resource(task_id: str) -> Resource | None:
        for res_id, var in assign_vars_by_task.get(task_id, {}).items():
            if solver.boolean_value(var):
                return resource_by_id[res_id]
        return None

    def build_scheduled_leaf(
        proj: Project, leaf: Task, parent_id: str | None
    ) -> ScheduledTask:
        s_day = solver.value(starts[leaf.id])
        e_day = solver.value(ends[leaf.id])
        c_days = solver.value(spans[leaf.id])
        res = get_assigned_resource(leaf.id)

        if res is None:
            return ScheduledTask(
                project_id=proj.id,
                project_name=proj.name,
                project_postal_code=proj.postal_code,
                id=leaf.id,
                name=leaf.name,
                parent_id=parent_id,
                task_type="Wait Subtask" if parent_id else "Main Task (Simple)",
                required_skill="—",
                assigned_resource="— (Wait)",
                resource_postal_code="—",
                distance_km=None,
                hours_needed=0,
                work_days=0,
                calendar_days=c_days,
                start_day=s_day,
                end_day=e_day,
                start_date=start_anchor + timedelta(days=s_day),
                end_date=start_anchor + timedelta(days=e_day),
            )

        return ScheduledTask(
            project_id=proj.id,
            project_name=proj.name,
            project_postal_code=proj.postal_code,
            id=leaf.id,
            name=leaf.name,
            parent_id=parent_id,
            task_type="Subtask" if parent_id else "Main Task (Simple)",
            required_skill=leaf.required_skill or "—",
            assigned_resource=res.name,
            resource_postal_code=res.postal_code,
            distance_km=distance_km_by_proj_res[(proj.id, res.id)],
            hours_needed=leaf.hours_needed,
            work_days=hours_to_work_days(leaf.hours_needed, res.hours_per_day),
            calendar_days=c_days,
            start_day=s_day,
            end_day=e_day,
            start_date=start_anchor + timedelta(days=s_day),
            end_date=start_anchor + timedelta(days=e_day),
        )

    solved_makespan = solver.value(makespan)
    project_summaries: list[ProjectSummary] = []
    scheduled_tasks: list[ScheduledTask] = []
    daily_assignments: list[DailyAssignment] = []
    total_distance_km = 0.0

    def record_daily_hours(
        proj: Project, leaf: Task, s_day: int, e_day: int, res: Resource | None
    ) -> None:
        if res is None or leaf.hours_needed <= 0:
            return
        remaining = leaf.hours_needed
        working_set = set(res.working_days)
        dist_km = distance_km_by_proj_res[(proj.id, res.id)]
        for day_offset in range(s_day, e_day):
            if remaining <= 0:
                break
            cal_date = start_anchor + timedelta(days=day_offset)
            if cal_date.weekday() in working_set:
                hours_today = min(remaining, res.hours_per_day)
                remaining -= hours_today
                daily_assignments.append(
                    DailyAssignment(
                        date=cal_date,
                        weekday=WEEKDAY_NAMES[cal_date.weekday()],
                        project_id=proj.id,
                        project_name=proj.name,
                        project_postal_code=proj.postal_code,
                        resource_id=res.id,
                        resource_name=res.name,
                        resource_postal_code=res.postal_code,
                        distance_km=dist_km,
                        task_id=leaf.id,
                        task_name=leaf.name.strip(),
                        skill=leaf.required_skill or "—",
                        hours=hours_today,
                    )
                )

    for proj in projects:
        proj_offset = (proj.start_date - start_anchor).days
        proj_end_day = solver.value(project_end_vars[proj.id])
        proj_distance_km = 0.0
        proj_hours = 0
        proj_leaf_count = 0
        proj_resources_used: set[str] = set()

        for task in proj.tasks:
            if not task.subtasks:
                proj_leaf_count += 1
                st = build_scheduled_leaf(proj, task, parent_id=None)
                scheduled_tasks.append(st)
                proj_hours += st.hours_needed
                if st.distance_km is not None:
                    proj_distance_km += st.distance_km
                if not st.assigned_resource.startswith("—"):
                    proj_resources_used.add(st.assigned_resource)
                record_daily_hours(
                    proj, task, st.start_day, st.end_day, get_assigned_resource(task.id)
                )
            else:
                t_s = solver.value(starts[task.id])
                t_e = solver.value(ends[task.id])
                t_d = solver.value(spans[task.id])
                sub_results = [
                    build_scheduled_leaf(proj, sub, parent_id=task.id)
                    for sub in task.subtasks
                ]
                proj_leaf_count += len(sub_results)
                for sub, st in zip(task.subtasks, sub_results):
                    proj_hours += st.hours_needed
                    if st.distance_km is not None:
                        proj_distance_km += st.distance_km
                    if not st.assigned_resource.startswith("—"):
                        proj_resources_used.add(st.assigned_resource)
                    record_daily_hours(
                        proj, sub, st.start_day, st.end_day, get_assigned_resource(sub.id)
                    )
                sub_skills = sorted(
                    {s.required_skill for s in sub_results if s.required_skill != "—"}
                )
                sub_resources = sorted(
                    {
                        s.assigned_resource
                        for s in sub_results
                        if not s.assigned_resource.startswith("—")
                    }
                )
                sub_postals = sorted(
                    {
                        s.resource_postal_code
                        for s in sub_results
                        if s.resource_postal_code != "—"
                    }
                )
                sub_distances = [
                    s.distance_km for s in sub_results if s.distance_km is not None
                ]
                scheduled_tasks.append(
                    ScheduledTask(
                        project_id=proj.id,
                        project_name=proj.name,
                        project_postal_code=proj.postal_code,
                        id=task.id,
                        name=task.name,
                        parent_id=None,
                        task_type="Main Task (with Subtasks)",
                        required_skill=", ".join(sub_skills),
                        assigned_resource=", ".join(sub_resources),
                        resource_postal_code=", ".join(sub_postals),
                        distance_km=round(sum(sub_distances), 1) if sub_distances else None,
                        hours_needed=sum(s.hours_needed for s in sub_results),
                        work_days=sum(s.work_days for s in sub_results),
                        calendar_days=t_d,
                        start_day=t_s,
                        end_day=t_e,
                        start_date=start_anchor + timedelta(days=t_s),
                        end_date=start_anchor + timedelta(days=t_e),
                    )
                )
                scheduled_tasks.extend(sub_results)

        total_distance_km += proj_distance_km
        project_summaries.append(
            ProjectSummary(
                project_id=proj.id,
                project_name=proj.name,
                city=proj.city,
                postal_code=proj.postal_code,
                status=status_name,
                start_date=proj.start_date,
                end_date=start_anchor + timedelta(days=proj_end_day),
                makespan_days=proj_end_day - proj_offset,
                main_task_count=len(proj.tasks),
                leaf_task_count=proj_leaf_count,
                total_hours=proj_hours,
                total_distance_km=round(proj_distance_km, 1),
                assigned_resources=", ".join(sorted(proj_resources_used)),
            )
        )

    daily_assignments.sort(key=lambda a: (a.date, a.project_id, a.resource_id, a.task_id))

    return ScheduleResult(
        status=status_name,
        makespan_days=solved_makespan,
        total_hours=total_hours,
        total_distance_km=round(total_distance_km, 1),
        schedule_start_date=start_anchor,
        schedule_end_date=start_anchor + timedelta(days=solved_makespan),
        projects=project_summaries,
        tasks=scheduled_tasks,
        daily_assignments=daily_assignments,
    )
