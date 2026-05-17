"""D3 — Search partners off unless data proves otherwise.

Default enabled, rarely worth it in B2B. We flag it as enabled and let
the agency justify with data.
"""

from agency_ads.audits.base import BaseCheck
from agency_ads.audits.types import (
    Category,
    CheckContext,
    CheckResult,
    DraftAction,
    Severity,
)


class SearchPartnersOffCheck(BaseCheck):
    check_id = "defaults.search_partners_off_unless_justified"
    title = "Search partners disabled (unless data justifies)"
    category = Category.DEFAULTS
    severity = Severity.HIGH
    weight = 1.0

    def evaluate(self, ctx: CheckContext) -> CheckResult:
        campaigns = ctx.snapshot.get("campaigns") or []
        offenders = [
            c for c in campaigns
            if c.get("type") == "SEARCH"
            and c.get("status") == "ENABLED"
            and c.get("search_partners_enabled")
        ]
        if not offenders:
            return CheckResult(
                passed=True,
                severity=self.severity,
                evidence={"search_campaigns_with_partners": 0},
            )

        return CheckResult(
            passed=False,
            severity=Severity.HIGH,
            evidence={
                "offenders": [
                    {"id": c.get("id"), "name": c.get("name")} for c in offenders
                ],
            },
            suggested_fix_md=(
                "Open each campaign → Settings → Networks → uncheck **Include "
                "Google search partners**. Reinstate only if you have data "
                "showing search-partner CPA within target."
            ),
            draft_action=DraftAction(
                type="disable_search_partners",
                risk_tier="L2",
                target={
                    "level": "campaign",
                    "ids": [c.get("id") for c in offenders],
                },
                diff={
                    "before": {c["name"]: True for c in offenders},
                    "after": {c["name"]: False for c in offenders},
                },
                reasoning_md=(
                    "Search partners include third-party search sites and "
                    "directories with weaker quality signals. Default-on in "
                    "Google Ads; default-off in healthy B2B accounts."
                ),
                expected_impact={
                    "metric": "wasted_spend",
                    "direction": "decrease",
                    "confidence": "medium",
                },
            ),
        )
