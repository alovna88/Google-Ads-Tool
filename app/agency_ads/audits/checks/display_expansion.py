"""D2 — "Include Google Display Network" off on every Search campaign.

GrowthSpree's #3 destructive default: routes 5-15% of Search budget to
near-zero-converting Display impressions. Always off on B2B Search.
"""

from agency_ads.audits.base import BaseCheck
from agency_ads.audits.types import (
    Category,
    CheckContext,
    CheckResult,
    DraftAction,
    Severity,
)


class SearchDisplayExpansionOffCheck(BaseCheck):
    check_id = "defaults.search_display_expansion_off"
    title = "Search campaigns do not include Google Display Network"
    category = Category.DEFAULTS
    severity = Severity.HIGH
    weight = 1.0

    def evaluate(self, ctx: CheckContext) -> CheckResult:
        campaigns = ctx.snapshot.get("campaigns") or []
        offenders = [
            c for c in campaigns
            if c.get("type") == "SEARCH"
            and c.get("status") == "ENABLED"
            and c.get("include_display_network")
        ]
        if not offenders:
            search = [c for c in campaigns if c.get("type") == "SEARCH"]
            return CheckResult(
                passed=True,
                severity=self.severity,
                evidence={"search_campaigns_checked": len(search)},
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
                "Open each campaign → Settings → Networks → uncheck **Display "
                "Network**. 5-15% of budget is otherwise siphoned to Display "
                "impressions with near-zero conversion rate in B2B."
            ),
            draft_action=DraftAction(
                type="disable_display_expansion",
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
                    "Search Network campaigns with Display expansion route "
                    "low-intent display impressions through a Search budget. "
                    "Confirmed waste pattern per GrowthSpree (43 B2B SaaS "
                    "accounts) and Vehnta."
                ),
                expected_impact={
                    "metric": "wasted_spend",
                    "direction": "decrease",
                    "magnitude_pct": "5-15",
                    "confidence": "high",
                },
            ),
        )
