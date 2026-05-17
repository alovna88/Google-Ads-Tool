"""T2 — Primary conversion action has click-through window >= 90 days.

B2B sales cycles average 84 days (Involve Digital). Google's default of
30 days truncates 60-80% of attributable conversions in B2B.

Severity: Critical. This is in the spine.
"""

from agency_ads.audits.base import BaseCheck
from agency_ads.audits.types import (
    Category,
    CheckContext,
    CheckResult,
    DraftAction,
    Severity,
)


class PrimaryConversionWindow90Check(BaseCheck):
    check_id = "tracking.primary_conversion_window_ge_90d"
    title = "Primary conversion window is at least 90 days"
    category = Category.TRACKING
    severity = Severity.CRITICAL
    weight = 1.0

    def evaluate(self, ctx: CheckContext) -> CheckResult:
        actions = ctx.snapshot.get("conversion_actions", [])
        primaries = [a for a in actions if a.get("primary")]

        # Sales cycle from playbook overrides the default 90.
        required_days = max(90, int(ctx.playbook.get("sales_cycle_days") or 0) or 90)

        if not primaries:
            return CheckResult(
                passed=False,
                severity=Severity.CRITICAL,
                evidence={"reason": "no primary conversion actions configured"},
                suggested_fix_md=(
                    "Mark at least one conversion action as Primary. For B2B "
                    "SaaS, this should be SQL, Opportunity, or Closed-Won — "
                    "not a top-of-funnel form submit."
                ),
            )

        offenders = [
            a for a in primaries
            if (a.get("click_through_window_days") or 0) < required_days
        ]
        if not offenders:
            return CheckResult(
                passed=True,
                severity=self.severity,
                evidence={
                    "required_days": required_days,
                    "primary_actions": [
                        {"name": a["name"], "window": a.get("click_through_window_days")}
                        for a in primaries
                    ],
                },
            )

        names = ", ".join(f"{a['name']} ({a.get('click_through_window_days')}d)" for a in offenders)
        return CheckResult(
            passed=False,
            severity=Severity.CRITICAL,
            evidence={
                "required_days": required_days,
                "offending_actions": [
                    {
                        "name": a["name"],
                        "click_through_window_days": a.get("click_through_window_days"),
                    }
                    for a in offenders
                ],
            },
            suggested_fix_md=(
                f"Set click-through window to **{required_days} days** on: {names}. "
                "Tools & Settings → Conversions → click the action → Edit settings → "
                "Conversion window."
            ),
            draft_action=DraftAction(
                type="set_conversion_window",
                risk_tier="L2",
                target={
                    "level": "conversion_action",
                    "actions": [a["name"] for a in offenders],
                },
                diff={
                    "before": {
                        a["name"]: a.get("click_through_window_days")
                        for a in offenders
                    },
                    "after": {a["name"]: required_days for a in offenders},
                },
                reasoning_md=(
                    f"Primary conversion windows below the {required_days}-day B2B "
                    "sales cycle truncate attribution. Smart Bidding then trains on "
                    "a lossy signal."
                ),
                expected_impact={
                    "metric": "attributed_conversions",
                    "direction": "increase",
                    "confidence": "high",
                },
            ),
        )
