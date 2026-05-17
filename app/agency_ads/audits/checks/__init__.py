"""Check registry. Every check the engine should run lives in CHECKS."""

from agency_ads.audits.base import BaseCheck
from agency_ads.audits.checks.auto_apply import AutoApplyOffCheck
from agency_ads.audits.checks.conversion_window import (
    PrimaryConversionWindow90Check,
)
from agency_ads.audits.checks.display_expansion import (
    SearchDisplayExpansionOffCheck,
)
from agency_ads.audits.checks.primary_event_quality import (
    PrimaryConversionIsLaterFunnelCheck,
)
from agency_ads.audits.checks.search_partners import SearchPartnersOffCheck
from agency_ads.audits.checks.target_cpa_cap import (
    MaxConversionsHasTargetCpaCheck,
)

CHECKS: list[type[BaseCheck]] = [
    PrimaryConversionWindow90Check,
    PrimaryConversionIsLaterFunnelCheck,
    AutoApplyOffCheck,
    SearchDisplayExpansionOffCheck,
    SearchPartnersOffCheck,
    MaxConversionsHasTargetCpaCheck,
]

__all__ = ["CHECKS"]
