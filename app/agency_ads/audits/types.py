"""Core types for the audit engine."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Category(StrEnum):
    """Audit categories, taken from docs/architecture.md §5.3.

    Order matters for the report — keep it in this order.
    """

    TRACKING = "Tracking & Measurement"
    STRUCTURE = "Account Structure"
    BIDDING = "Bidding & Budget"
    KEYWORDS = "Keywords & Search Terms"
    ADS = "Ads & Assets"
    AUDIENCE = "Audience & Targeting"
    DEFAULTS = "Settings & Defaults"


# Per-category weights (sum = 1.00). Same as docs/architecture.md.
CATEGORY_WEIGHTS: dict[Category, float] = {
    Category.TRACKING: 0.25,
    Category.STRUCTURE: 0.20,
    Category.BIDDING: 0.15,
    Category.KEYWORDS: 0.15,
    Category.ADS: 0.10,
    Category.AUDIENCE: 0.10,
    Category.DEFAULTS: 0.05,
}


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Severity multipliers, from claude-ads taxonomy.
SEVERITY_MULTIPLIERS: dict[Severity, float] = {
    Severity.CRITICAL: 5.0,
    Severity.HIGH: 3.0,
    Severity.MEDIUM: 1.5,
    Severity.LOW: 0.5,
}


@dataclass(frozen=True)
class DraftAction:
    """A draft Action the check wants to propose. The runner persists it
    and links it to the AuditCheckResult.
    """

    type: str
    risk_tier: str  # L1 / L2 / L3
    target: dict[str, Any]
    diff: dict[str, Any]
    reasoning_md: str
    expected_impact: dict[str, Any]


@dataclass
class CheckContext:
    """Everything a check needs at evaluation time.

    `snapshot` is the parsed AccountSnapshot (see audits/snapshot.py).
    `playbook` is the parsed jsonb from the latest playbook.
    """

    snapshot: dict[str, Any]
    playbook: dict[str, Any]


@dataclass
class CheckResult:
    """The output of one check execution."""

    passed: bool
    severity: Severity
    evidence: dict[str, Any] = field(default_factory=dict)
    suggested_fix_md: str | None = None
    draft_action: DraftAction | None = None
