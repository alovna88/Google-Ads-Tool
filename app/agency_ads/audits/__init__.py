"""Audit engine.

A `Check` is a small, named, weighted assertion against an
`AccountSnapshot`. Each Check returns a `CheckResult` carrying the
pass/fail, evidence, and an optional draft Action.

The runner executes the registered checks, computes a weighted 0-100
score per category and overall, persists everything, and creates
draft actions in the queue.

To add a new check:
1. Create a module under `agency_ads/audits/checks/`
2. Implement a subclass of `BaseCheck`
3. Add it to `CHECK_REGISTRY` in `checks/__init__.py`
"""

from agency_ads.audits.types import (
    Category,
    CheckContext,
    CheckResult,
    Severity,
)

__all__ = ["Category", "CheckContext", "CheckResult", "Severity"]
