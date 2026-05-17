"""T3 — Primary conversion is a later-funnel event, not Page View / Session.

A primary conversion of "Page View" or "Session Start" teaches Smart
Bidding to find people who load pages — not buy. Directive and
Dreamdata both call this out as the most common B2B mistake.
"""

from agency_ads.audits.base import BaseCheck
from agency_ads.audits.types import (
    Category,
    CheckContext,
    CheckResult,
    Severity,
)

DISALLOWED_TOP_OF_FUNNEL = {
    "page view",
    "pageview",
    "session start",
    "session_start",
    "session",
    "scroll",
    "scroll_depth",
    "click",
}


class PrimaryConversionIsLaterFunnelCheck(BaseCheck):
    check_id = "tracking.primary_is_later_funnel"
    title = "Primary conversion is not a top-of-funnel event"
    category = Category.TRACKING
    severity = Severity.CRITICAL
    weight = 1.0

    def evaluate(self, ctx: CheckContext) -> CheckResult:
        actions = ctx.snapshot.get("conversion_actions", [])
        primaries = [a for a in actions if a.get("primary")]
        if not primaries:
            return CheckResult(
                passed=False,
                severity=Severity.CRITICAL,
                evidence={"reason": "no primary conversion actions"},
                suggested_fix_md="See `tracking.primary_conversion_window_ge_90d` — same root cause.",
            )

        offenders = []
        for a in primaries:
            name = (a.get("name") or "").strip().lower()
            if any(d in name for d in DISALLOWED_TOP_OF_FUNNEL):
                offenders.append(a)

        if not offenders:
            return CheckResult(
                passed=True,
                severity=self.severity,
                evidence={
                    "primary_actions": [a["name"] for a in primaries],
                },
            )

        return CheckResult(
            passed=False,
            severity=Severity.CRITICAL,
            evidence={
                "offending_actions": [a["name"] for a in offenders],
                "rule": (
                    "Names matching {Page View, Session Start, Scroll, Click} flagged."
                ),
            },
            suggested_fix_md=(
                "Demote these to Secondary and promote a later-funnel action "
                "(SQL, Opportunity, Closed-Won via offline conversion import) "
                "to Primary. Smart Bidding optimizes the Primary signal; "
                "page-view / session conversions teach it to find pageview-ers."
            ),
        )
