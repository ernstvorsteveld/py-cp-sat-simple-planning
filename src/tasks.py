"""Sample task schedule hierarchies for the 5 projects."""

from src.models import Task


def build_prj1_tasks() -> list[Task]:
    """Task schedule for PRJ-001: Utrecht Cloud Platform Modernization."""
    return [
        Task(id="P1-T1", name="P1-T1: Project Kickoff [skill2]", required_skill="skill2", hours_needed=16),
        Task(
            id="P1-T2",
            name="P1-T2: Architecture Blueprint [skill1]",
            required_skill="skill1",
            hours_needed=24,
            predecessors=["P1-T1"],
        ),
        Task(
            id="P1-M1",
            name="P1-M1: Cloud & Security Setup (Main)",
            predecessors=["P1-T2"],
            subtasks=[
                Task(id="P1-M1.1", name="  ↳ P1-M1.1: Provision Kubernetes [skill1]", required_skill="skill1", hours_needed=24),
                Task(id="P1-M1.2", name="  ↳ P1-M1.2: TLS Certificate Request [skill1]", required_skill="skill1", hours_needed=8),
                Task(id="P1-M1.3", name="  ↳ P1-M1.3: Certificate Authority Wait", required_skill=None, hours_needed=0, wait_days=3, predecessors=["P1-M1.2"]),
                Task(id="P1-M1.4", name="  ↳ P1-M1.4: Install Certificates [skill1]", required_skill="skill1", hours_needed=8, predecessors=["P1-M1.3"]),
                Task(id="P1-M1.5", name="  ↳ P1-M1.5: Security Audit [skill3]", required_skill="skill3", hours_needed=16, predecessors=["P1-M1.1"]),
            ],
        ),
        Task(
            id="P1-T3",
            name="P1-T3: Final Cutover & Handover [skill2]",
            required_skill="skill2",
            hours_needed=16,
            predecessors=["P1-M1"],
        ),
    ]


def build_prj2_tasks() -> list[Task]:
    """Task schedule for PRJ-002: Amsterdam FinTech Payment Gateway."""
    return [
        Task(id="P2-T1", name="P2-T1: Regulatory Scope [skill3]", required_skill="skill3", hours_needed=16),
        Task(
            id="P2-M1",
            name="P2-M1: Payment Engine & PSD2 Compliance (Main)",
            predecessors=["P2-T1"],
            subtasks=[
                Task(id="P2-M1.1", name="  ↳ P2-M1.1: Core Ledger API [skill1]", required_skill="skill1", hours_needed=24),
                Task(id="P2-M1.2", name="  ↳ P2-M1.2: Fraud Rules Engine [skill1]", required_skill="skill1", hours_needed=16),
                Task(id="P2-M1.3", name="  ↳ P2-M1.3: External Bank Sandbox Wait", required_skill=None, hours_needed=0, wait_days=4, predecessors=["P2-M1.1"]),
                Task(id="P2-M1.4", name="  ↳ P2-M1.4: PSD2 Audit Sign-off [skill3]", required_skill="skill3", hours_needed=16, predecessors=["P2-M1.2", "P2-M1.3"]),
            ],
        ),
        Task(
            id="P2-T2",
            name="P2-T2: Merchant Onboarding Portal [skill2]",
            required_skill="skill2",
            hours_needed=24,
            predecessors=["P2-M1"],
        ),
        Task(
            id="P2-T3",
            name="P2-T3: Go-Live Verification [skill3]",
            required_skill="skill3",
            hours_needed=8,
            predecessors=["P2-T2"],
        ),
    ]


def build_prj3_tasks() -> list[Task]:
    """Task schedule for PRJ-003: Eindhoven High-Tech IoT Telemetry."""
    return [
        Task(id="P3-T1", name="P3-T1: Sensor Protocol Spec [skill1]", required_skill="skill1", hours_needed=16),
        Task(
            id="P3-M1",
            name="P3-M1: Edge Firmware & Ingestion Pipeline (Main)",
            predecessors=["P3-T1"],
            subtasks=[
                Task(id="P3-M1.1", name="  ↳ P3-M1.1: MQTT Broker Cluster [skill1]", required_skill="skill1", hours_needed=24),
                Task(id="P3-M1.2", name="  ↳ P3-M1.2: Factory Floor Hardware Wait", required_skill=None, hours_needed=0, wait_days=3),
                Task(id="P3-M1.3", name="  ↳ P3-M1.3: Operator Dashboard [skill2]", required_skill="skill2", hours_needed=24, predecessors=["P3-M1.2"]),
                Task(id="P3-M1.4", name="  ↳ P3-M1.4: Safety Certification [skill3]", required_skill="skill3", hours_needed=16, predecessors=["P3-M1.1"]),
            ],
        ),
        Task(
            id="P3-T2",
            name="P3-T2: Factory Acceptance Test [skill1]",
            required_skill="skill1",
            hours_needed=16,
            predecessors=["P3-M1"],
        ),
    ]


def build_prj4_tasks() -> list[Task]:
    """Task schedule for PRJ-004: Groningen Energy Grid Analytics."""
    return [
        Task(id="P4-T1", name="P4-T1: Grid Data Alignment [skill2]", required_skill="skill2", hours_needed=16),
        Task(
            id="P4-T2",
            name="P4-T2: Time-Series Ingestion [skill1]",
            required_skill="skill1",
            hours_needed=24,
            predecessors=["P4-T1"],
        ),
        Task(
            id="P4-M1",
            name="P4-M1: Forecasting & Grid Compliance (Main)",
            predecessors=["P4-T2"],
            subtasks=[
                Task(id="P4-M1.1", name="  ↳ P4-M1.1: Load Balancing Model [skill1]", required_skill="skill1", hours_needed=24),
                Task(id="P4-M1.2", name="  ↳ P4-M1.2: Regulator Dataset Review Wait", required_skill=None, hours_needed=0, wait_days=4),
                Task(id="P4-M1.3", name="  ↳ P4-M1.3: Grid Governance Report [skill3]", required_skill="skill3", hours_needed=16, predecessors=["P4-M1.2"]),
                Task(id="P4-M1.4", name="  ↳ P4-M1.4: Control Room UX [skill2]", required_skill="skill2", hours_needed=16, predecessors=["P4-M1.1"]),
            ],
        ),
        Task(
            id="P4-T3",
            name="P4-T3: Grid Operator Training [skill2]",
            required_skill="skill2",
            hours_needed=8,
            predecessors=["P4-M1"],
        ),
    ]


def build_prj5_tasks() -> list[Task]:
    """Task schedule for PRJ-005: Rotterdam Port Logistics Portal."""
    return [
        Task(id="P5-T1", name="P5-T1: Customs API Discovery [skill2]", required_skill="skill2", hours_needed=16),
        Task(
            id="P5-M1",
            name="P5-M1: Container Tracking & Customs Clearance (Main)",
            predecessors=["P5-T1"],
            subtasks=[
                Task(id="P5-M1.1", name="  ↳ P5-M1.1: Manifest Sync Service [skill1]", required_skill="skill1", hours_needed=24),
                Task(id="P5-M1.2", name="  ↳ P5-M1.2: Carrier Webhook Integration [skill2]", required_skill="skill2", hours_needed=16),
                Task(id="P5-M1.3", name="  ↳ P5-M1.3: Port Authority Approval Wait", required_skill=None, hours_needed=0, wait_days=3, predecessors=["P5-M1.2"]),
                Task(id="P5-M1.4", name="  ↳ P5-M1.4: Maritime Security Review [skill3]", required_skill="skill3", hours_needed=24, predecessors=["P5-M1.1", "P5-M1.3"]),
            ],
        ),
        Task(
            id="P5-T2",
            name="P5-T2: Terminal Rollout [skill2]",
            required_skill="skill2",
            hours_needed=16,
            predecessors=["P5-M1"],
        ),
    ]
