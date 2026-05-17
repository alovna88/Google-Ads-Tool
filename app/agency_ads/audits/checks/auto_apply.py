"""D1 — Auto-applied recommendations should be OFF, all categories.

GrowthSpree's #2 destructive default. Google's "auto-apply" silently
applies recommendations (broad match keywords, ad variants, GDN
expansion) without the agency seeing them. Several Digiday-reported
cases of Google reps re-enabling auto-apply behind agencies' backs.
"""

from agency_ads.audits.base import BaseCheck
from agency_ads.audits.types import (
    Category,
    CheckContext,
    CheckResult,
    DraftAction,
    Severity,
)


class AutoApplyOffCheck(BaseCheck):
    check_id = "defaults.auto_apply_recommendations_off"
    title = "Auto-applied recommendations are all turned off"
    category = Category.DEFAULTS
    severity = Severity.CRITICAL
    weight = 1.0

    def evaluate(self, ctx: CheckContext) -> CheckResult:
        auto_apply = ctx.snapshot.get("auto_apply") or {}
        enabled = list(auto_apply.get("enabled_types") or [])
        if not enabled:
            return CheckResult(
                passed=True,
                severity=self.severity,
                evidence={"enabled_types": []},
            )

        return CheckResult(
            passed=False,
            severity=Severity.CRITICAL,
            evidence={"enabled_types": enabled},
            suggested_fix_md=(
                "Tools & Settings → Recommendations → click the gear / Auto-apply "
                "page → turn off **every** category. Google re-enables these "
                "during outreach; check weekly."
            ),
            draft_action=DraftAction(
                type="disable_auto_apply",
                risk_tier="L2",
                target={"level": "account", "categories": enabled},
                diff={"before": {"enabled_types": enabled}, "after": {"enabled_types": []}},
                reasoning_md=(
                    "Auto-applied recommendations silently apply broad-match "
                    "expansion, ad variants, and GDN inclusion — all destructive "
                    "in B2B without OCI. Disable all and revisit manually."
                ),
                expected_impact={
                    "metric": "wasted_spend",
                    "direction": "decrease",
                    "confidence": "high",
                },
            ),
        )
