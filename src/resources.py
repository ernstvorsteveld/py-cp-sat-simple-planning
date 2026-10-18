"""Resource generation with skills, Dutch postal codes, and weekly availability."""

from src.models import Resource
from src.postal_codes import normalize_dutch_postal_code


def build_sample_resources(
    default_hours: int = 8,
) -> list[Resource]:
    """Create 12 resources across the Netherlands with skills (skill1, skill2, skill3) and postal codes."""
    raw_resources = [
        ("R1", "Alice (Utrecht, skill1)", ["skill1"], "3511 JC", "Utrecht", [0, 1, 2, 3], default_hours),
        ("R2", "Bob (Amsterdam, skill1/3)", ["skill1", "skill3"], "1012 JS", "Amsterdam", [1, 2, 3, 4], default_hours),
        ("R3", "Charlie (Rotterdam, skill2/3)", ["skill2", "skill3"], "3011 AD", "Rotterdam", [0, 1, 2, 3], default_hours),
        ("R4", "Diana (Den Haag, skill2)", ["skill2"], "2511 CV", "Den Haag", [0, 1, 2, 3, 4], max(default_hours - 2, 4)),
        ("R5", "Erik (Eindhoven, skill1/2)", ["skill1", "skill2"], "5611 EM", "Eindhoven", [0, 1, 2, 3, 4], default_hours),
        ("R6", "Femke (Groningen, skill1/3)", ["skill1", "skill3"], "9712 GK", "Groningen", [0, 1, 2, 3], default_hours),
        ("R7", "Gijs (Zwolle, skill2/3)", ["skill2", "skill3"], "8011 PK", "Zwolle", [0, 1, 2, 3, 4], default_hours),
        ("R8", "Hannah (Arnhem, skill1)", ["skill1"], "6811 DG", "Arnhem", [1, 2, 3, 4], default_hours),
        ("R9", "Ivo (Breda, skill2/3)", ["skill2", "skill3"], "4811 KT", "Breda", [0, 1, 2, 3], default_hours),
        ("R10", "Julia (Maastricht, skill1/3)", ["skill1", "skill3"], "6211 CL", "Maastricht", [0, 1, 2, 3, 4], max(default_hours - 1, 4)),
        ("R11", "Koen (Enschede, skill1/2)", ["skill1", "skill2"], "7511 JM", "Enschede", [0, 1, 2, 3, 4], default_hours),
        ("R12", "Lotte (Haarlem, skill2/3)", ["skill2", "skill3"], "2011 RD", "Haarlem", [0, 1, 2, 3], default_hours),
    ]
    return [
        Resource(
            id=r_id,
            name=name,
            skills=skills,
            postal_code=normalize_dutch_postal_code(pc),
            city=city,
            working_days=days,
            hours_per_day=hpd,
        )
        for r_id, name, skills, pc, city, days, hpd in raw_resources
    ]
