"""Audit score computation. Pure functions — no DB."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agency_ads.audits.types import (
    CATEGORY_WEIGHTS,
    SEVERITY_MULTIPLIERS,
    Category,
    Severity,
)

if TYPE_CHECKING:
    from agency_ads.audits.base import BaseCheck
    from agency_ads.audits.types import CheckResult


@dataclass(frozen=True)
class CategoryScore:
    category: Category
    score: float
    grade: str


@dataclass(frozen=True)
class AuditScore:
    overall: float
    grade: str
    per_category: list[CategoryScore]


def grade_from_score(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _category_score(
    category: Category,
    pairs: Iterable[tuple["BaseCheck", "CheckResult"]],
) -> float:
    """0-100 score for one category from its check results.

    For each check, the contribution is weight × severity_multiplier.
    Passed checks earn their full contribution; failed checks earn 0.
    Score = sum(earned) / sum(max possible) × 100.

    If a category has no checks, returns 100 (nothing to fail).
    """
    earned = 0.0
    possible = 0.0
    for check, result in pairs:
        contribution = check.weight * SEVERITY_MULTIPLIERS[Severity(check.severity)]
        possible += contribution
        if result.passed:
            earned += contribution
    if possible == 0:
        return 100.0
    return round((earned / possible) * 100, 2)


def compute_audit_score(
    results: list[tuple["BaseCheck", "CheckResult"]],
) -> AuditScore:
    """Compute the audit's overall + per-category scores."""
    by_category: dict[Category, list[tuple[BaseCheck, CheckResult]]] = {
        c: [] for c in Category
    }
    for check, result in results:
        by_category[check.category].append((check, result))

    per_category: list[CategoryScore] = []
    overall_num = 0.0
    overall_den = 0.0
    for category, pairs in by_category.items():
        score = _category_score(category, pairs)
        per_category.append(
            CategoryScore(category=category, score=score, grade=grade_from_score(score))
        )
        # Only categories with at least one check contribute to overall.
        if pairs:
            weight = CATEGORY_WEIGHTS[category]
            overall_num += score * weight
            overall_den += weight

    overall = round(overall_num / overall_den, 2) if overall_den else 100.0
    return AuditScore(
        overall=overall,
        grade=grade_from_score(overall),
        per_category=per_category,
    )
