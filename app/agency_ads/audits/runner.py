"""Audit runner — orchestrates checks and persists results.

Called from the API route. Takes a Client + snapshot dict + the
authenticated user, returns the persisted Audit (with check_results
loaded). Draft actions are inserted into the queue with status
'proposed' and linked from their AuditCheckResult.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agency_ads.audits.base import BaseCheck
from agency_ads.audits.checks import CHECKS
from agency_ads.audits.scoring import compute_audit_score
from agency_ads.audits.snapshot import coerce_snapshot
from agency_ads.audits.types import CheckContext, CheckResult, DraftAction
from agency_ads.models import Action, Audit, AuditCheckResult, Client, Playbook, User

logger = logging.getLogger(__name__)

DRAFT_EXPIRY_DAYS = 30


async def run_audit(
    session: AsyncSession,
    *,
    client: Client,
    snapshot: dict | None,
    user: User,
) -> Audit:
    """Execute every registered check against the client and persist.

    Returns the new Audit row, with `check_results` populated. The
    caller is responsible for committing the session (the session
    dependency does this in the route).
    """
    coerced = coerce_snapshot(snapshot)
    playbook_parsed = await _latest_playbook_parsed(session, client.id)

    ctx = CheckContext(snapshot=coerced, playbook=playbook_parsed)

    pairs: list[tuple[BaseCheck, CheckResult]] = []
    for cls in CHECKS:
        check = cls()
        try:
            result = check.evaluate(ctx)
        except Exception:  # noqa: BLE001
            logger.exception("check %s raised", check.check_id)
            # Treat raises as failures with low severity so the audit
            # still produces useful output for the rest of the checks.
            result = CheckResult(
                passed=False,
                severity=check.severity,
                evidence={"error": "check raised an exception — see logs"},
            )
        pairs.append((check, result))

    score = compute_audit_score(pairs)

    audit = Audit(
        client_id=client.id,
        overall_score=score.overall,
        grade=score.grade,
        category_scores={cs.category.value: {"score": cs.score, "grade": cs.grade} for cs in score.per_category},
        snapshot=coerced,
        created_by=user.id,
    )
    session.add(audit)
    await session.flush()

    expires_at = datetime.now(timezone.utc) + timedelta(days=DRAFT_EXPIRY_DAYS)

    for check, result in pairs:
        action_row: Action | None = None
        if result.draft_action is not None:
            action_row = _build_action_row(
                client_id=client.id,
                audit_id=audit.id,
                draft=result.draft_action,
                expires_at=expires_at,
            )
            session.add(action_row)
            await session.flush()  # populate action_row.id

        session.add(
            AuditCheckResult(
                audit_id=audit.id,
                check_id=check.check_id,
                category=check.category.value,
                title=check.title,
                passed=result.passed,
                severity=str(result.severity),
                weight=check.weight,
                evidence=result.evidence,
                suggested_fix_md=result.suggested_fix_md,
                draft_action_id=action_row.id if action_row else None,
            )
        )

    await session.flush()
    return audit


async def _latest_playbook_parsed(
    session: AsyncSession, client_id: uuid.UUID
) -> dict:
    result = await session.execute(
        select(Playbook.parsed)
        .where(Playbook.client_id == client_id)
        .order_by(Playbook.version.desc())
        .limit(1)
    )
    parsed = result.scalar_one_or_none()
    return parsed or {}


def _build_action_row(
    *,
    client_id: uuid.UUID,
    audit_id: uuid.UUID,
    draft: DraftAction,
    expires_at: datetime,
) -> Action:
    return Action(
        client_id=client_id,
        audit_id=audit_id,
        type=draft.type,
        target=draft.target,
        diff=draft.diff,
        reasoning_md=draft.reasoning_md,
        evidence={},  # populated from check evidence at display time
        expected_impact=draft.expected_impact,
        risk_tier=draft.risk_tier,
        status="proposed",
        expires_at=expires_at,
    )
