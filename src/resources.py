"""Resource generation and availability configuration."""

from src.models import Resource


def build_sample_resources(
    alice_hours: int = 8,
    bob_hours: int = 8,
    charlie_hours: int = 8,
    diana_hours: int = 6,
) -> list[Resource]:
    """Create sample resources with skills (skill1, skill2, skill3) and weekly availability."""
    return [
        Resource(
            id="R1",
            name="Alice (skill1)",
            skills=["skill1"],
            working_days=[0, 1, 2, 3],  # Mon-Thu
            hours_per_day=alice_hours,
        ),
        Resource(
            id="R2",
            name="Bob (skill1/skill3)",
            skills=["skill1", "skill3"],
            working_days=[1, 2, 3, 4],  # Tue-Fri
            hours_per_day=bob_hours,
        ),
        Resource(
            id="R3",
            name="Charlie (skill2/skill3)",
            skills=["skill2", "skill3"],
            working_days=[0, 1, 2, 3],  # Mon-Thu
            hours_per_day=charlie_hours,
        ),
        Resource(
            id="R4",
            name="Diana (skill2)",
            skills=["skill2"],
            working_days=[0, 1, 2, 3, 4],  # Mon-Fri
            hours_per_day=diana_hours,
        ),
    ]
