"""B2 — Maximize Conversions has a Target CPA cap.

GrowthSpree's #5 destructive default. Max Conversions without a cap
spends to find conversions at any CPA — fine for ecom, deadly for B2B
where the wrong-CPA conversion is a $0 form submit.
"""

from agency_ads.audits.base import BaseCheck
from agency_ads.audits.types import (
    Category,
    CheckContext,
    CheckResult,
    DraftAction,
    Severity,
)


class MaxConversionsHasTargetCpaCheck(BaseCheck):
    check_id = "bidding.max_conversions_has_target_cpa"
    title = "Maximize Conversions campaigns have a Target CPA cap"
    category = Category.BIDDING
    severity = Severity.HIGH
    weight = 1.0

    def evaluate(self, ctx: CheckContext) -> CheckResult:
        campaigns = ctx.snapshot.get("campaigns") or []
        offenders = [
            c for c in campaigns
            if c.get("status") == "ENABLED"
            and c.get("bidding_strategy") == "MAXIMIZE_CONVERSIONS"
            and not c.get("target_cpa_micros")
        ]
        if not offenders:
            return CheckResult(
                passed=True,
                severity=self.severity,
                evidence={
                    "checked": len([
                        c for c in campaigns
                        if c.get("bidding_strategy") == "MAXIMIZE_CONVERSIONS"
                    ]),
                },
            )

        target_cac = ctx.playbook.get("target_cac_usd")
        suggested = (
            f"Use the playbook's target CAC (${target_cac}) as the cap, "
            "adjusted for the lead→close rate."
            if target_cac
            else "Set a cap based on the client's CAC target — fill in the playbook §2."
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
                "Set a Target CPA on each Max Conversions campaign. " + suggested
            ),
            draft_action=DraftAction(
                type="set_target_cpa_cap",
                risk_tier="L3",
                target={
                    "level": "campaign",
                    "ids": [c.get("id") for c in offenders],
                },
                diff={
                    "before": {c["name"]: None for c in offenders},
                    "after": {c["name"]: "<set per campaign>" for c in offenders},
                },
                reasoning_md=(
                    "Max Conversions without a Target CPA cap optimizes for "
                    "*any* conversion volume — including cheap form spam. A "
                    "cap forces Smart Bidding to stay within commercial bounds."
                ),
                expected_impact={
                    "metric": "cac",
                    "direction": "decrease",
                    "confidence": "medium",
                },
            ),
        )
