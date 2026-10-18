"""Project creation and configuration for the 5 Dutch projects."""

from datetime import date, timedelta

from src.models import Project
from src.postal_codes import normalize_dutch_postal_code
from src.tasks import (
    build_prj1_tasks,
    build_prj2_tasks,
    build_prj3_tasks,
    build_prj4_tasks,
    build_prj5_tasks,
)


def build_sample_projects(
    base_start_date: date | None = None,
    prj1_postal_code: str = "3512 JE",  # Utrecht
    prj2_postal_code: str = "1015 CJ",  # Amsterdam
    prj3_postal_code: str = "5612 AX",  # Eindhoven
    prj4_postal_code: str = "9713 AV",  # Groningen
    prj5_postal_code: str = "3014 GT",  # Rotterdam
) -> list[Project]:
    """Create 5 `Project` instances across the Netherlands, each with its own task schedule."""
    anchor = base_start_date or date(2026, 10, 19)
    return [
        Project(
            id="PRJ-001",
            name="PRJ-001: Cloud Platform Modernization",
            postal_code=normalize_dutch_postal_code(prj1_postal_code),
            city="Utrecht",
            start_date=anchor,
            tasks=build_prj1_tasks(),
        ),
        Project(
            id="PRJ-002",
            name="PRJ-002: FinTech Payment Gateway",
            postal_code=normalize_dutch_postal_code(prj2_postal_code),
            city="Amsterdam",
            start_date=anchor + timedelta(days=1),
            tasks=build_prj2_tasks(),
        ),
        Project(
            id="PRJ-003",
            name="PRJ-003: High-Tech IoT Telemetry",
            postal_code=normalize_dutch_postal_code(prj3_postal_code),
            city="Eindhoven",
            start_date=anchor + timedelta(days=2),
            tasks=build_prj3_tasks(),
        ),
        Project(
            id="PRJ-004",
            name="PRJ-004: Energy Grid Analytics",
            postal_code=normalize_dutch_postal_code(prj4_postal_code),
            city="Groningen",
            start_date=anchor,
            tasks=build_prj4_tasks(),
        ),
        Project(
            id="PRJ-005",
            name="PRJ-005: Port Logistics Portal",
            postal_code=normalize_dutch_postal_code(prj5_postal_code),
            city="Rotterdam",
            start_date=anchor + timedelta(days=3),
            tasks=build_prj5_tasks(),
        ),
    ]
