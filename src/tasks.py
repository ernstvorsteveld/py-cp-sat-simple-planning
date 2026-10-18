"""Sample task hierarchy generation for scheduling."""

from src.models import Task


def build_sample_tasks() -> list[Task]:
    """Create sample tasks: 6 main tasks without subtasks and 4 main tasks with nested `Task` subtasks."""
    return [
        Task(
            id="T1",
            name="T1: Project Kickoff [skill2]",
            required_skill="skill2",
            hours_needed=16,
        ),
        Task(
            id="T2",
            name="T2: Requirements & Architecture [skill1]",
            required_skill="skill1",
            hours_needed=24,
            predecessors=["T1"],
        ),
        Task(
            id="M1",
            name="M1: Procurement & Vendor Setup (Main)",
            predecessors=["T2"],
            subtasks=[
                Task(id="M1.1", name="  ↳ M1.1: Cloud Infrastructure [skill1]", required_skill="skill1", hours_needed=24),
                Task(id="M1.2", name="  ↳ M1.2: Security Certificates (Prep) [skill1]", required_skill="skill1", hours_needed=8),
                Task(id="M1.3", name="  ↳ M1.3: Certificate Authority Wait", required_skill=None, hours_needed=0, wait_days=4, predecessors=["M1.2"]),
                Task(id="M1.4", name="  ↳ M1.4: Install Certificates [skill1]", required_skill="skill1", hours_needed=8, predecessors=["M1.3"]),
                Task(id="M1.5", name="  ↳ M1.5: Vendor Contracts [skill2]", required_skill="skill2", hours_needed=16),
            ],
        ),
        Task(
            id="T3",
            name="T3: Core Data Model [skill1]",
            required_skill="skill1",
            hours_needed=16,
            predecessors=["M1"],
        ),
        Task(
            id="M2",
            name="M2: Core Module Development (Main)",
            predecessors=["T3"],
            subtasks=[
                Task(id="M2.1", name="  ↳ M2.1: Auth & Permissions [skill1]", required_skill="skill1", hours_needed=32),
                Task(id="M2.2", name="  ↳ M2.2: Billing Integration [skill1]", required_skill="skill1", hours_needed=24),
                Task(id="M2.3", name="  ↳ M2.3: Stakeholder Alignment [skill2]", required_skill="skill2", hours_needed=16),
                Task(id="M2.4", name="  ↳ M2.4: Risk Review [skill3]", required_skill="skill3", hours_needed=16),
            ],
        ),
        Task(
            id="T4",
            name="T4: System Integration [skill1]",
            required_skill="skill1",
            hours_needed=16,
            predecessors=["M2"],
        ),
        Task(
            id="M3",
            name="M3: External Testing & Audits (Main)",
            predecessors=["T4"],
            subtasks=[
                Task(id="M3.1", name="  ↳ M3.1: Penetration Test Setup [skill1]", required_skill="skill1", hours_needed=8),
                Task(id="M3.2", name="  ↳ M3.2: External Pen-Test Execution (Wait)", required_skill=None, hours_needed=0, wait_days=5, predecessors=["M3.1"]),
                Task(id="M3.3", name="  ↳ M3.3: Fix Pen-Test Findings [skill1]", required_skill="skill1", hours_needed=16, predecessors=["M3.2"]),
                Task(id="M3.4", name="  ↳ M3.4: Compliance Audit [skill3]", required_skill="skill3", hours_needed=24),
                Task(id="M3.5", name="  ↳ M3.5: Accessibility Review [skill2]", required_skill="skill2", hours_needed=16),
            ],
        ),
        Task(
            id="T5",
            name="T5: Release Candidate Sign-off [skill3]",
            required_skill="skill3",
            hours_needed=8,
            predecessors=["M3"],
        ),
        Task(
            id="M4",
            name="M4: Rollout & Store Approvals (Main)",
            predecessors=["T5"],
            subtasks=[
                Task(id="M4.1", name="  ↳ M4.1: Submit to App Store [skill2]", required_skill="skill2", hours_needed=8),
                Task(id="M4.2", name="  ↳ M4.2: App Store Review Wait", required_skill=None, hours_needed=0, wait_days=4, predecessors=["M4.1"]),
                Task(id="M4.3", name="  ↳ M4.3: Publish Release [skill2]", required_skill="skill2", hours_needed=8, predecessors=["M4.2"]),
                Task(id="M4.4", name="  ↳ M4.4: Customer Migration [skill1]", required_skill="skill1", hours_needed=24),
                Task(id="M4.5", name="  ↳ M4.5: Release Governance [skill3]", required_skill="skill3", hours_needed=16),
            ],
        ),
        Task(
            id="T6",
            name="T6: Handover & Project Closure [skill2]",
            required_skill="skill2",
            hours_needed=16,
            predecessors=["M4"],
        ),
    ]
