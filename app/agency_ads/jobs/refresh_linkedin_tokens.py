"""Background job: rotate LinkedIn access tokens before they expire.

Scheduled by the worker every hour. For each connection nearing expiry:

- If a refresh token is on file, exchange it (mutating the row in place).
- Otherwise mark the row `needs_reauth` so the UI prompts the user.

Connections in a non-`connected` status are skipped — they need a human
to re-authorize. This is what makes the connection "always-on" from
the agent's point of view: as long as someone re-authorizes once, the
worker keeps the access token alive indefinitely (until LinkedIn's
365-day refresh-token cap, after which the worker flips status to
`needs_reauth` and the UI handles the rest).
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from redis import Redis
from rq import Queue
from sqlalchemy import select

from agency_ads.config import settings
from agency_ads.db import get_session
from agency_ads.models import LinkedinConnection
from agency_ads.services import linkedin_client, linkedin_connections

logger = logging.getLogger(__name__)

RECURRING_JOB_ID = "linkedin-refresh-tokens"
RECURRING_INTERVAL = timedelta(hours=1)


async def _refresh_due() -> dict:
    refreshed = 0
    needs_reauth = 0
    errored = 0

    cutoff = datetime.now(UTC) + timedelta(seconds=settings.linkedin_refresh_skew_seconds)

    async with get_session() as session:
        result = await session.execute(
            select(LinkedinConnection).where(
                LinkedinConnection.status.in_(("connected", "expired")),
                LinkedinConnection.expires_at <= cutoff,
            )
        )
        connections = list(result.scalars().all())

        for connection in connections:
            if not connection.refresh_token:
                await linkedin_connections.mark_error(
                    session,
                    connection,
                    status="needs_reauth",
                    message="Access token near expiry and no refresh token on file.",
                )
                needs_reauth += 1
                continue

            connection = await linkedin_client.ensure_fresh_token(session, connection)
            if connection.status == "connected":
                refreshed += 1
            elif connection.status == "needs_reauth":
                needs_reauth += 1
            else:
                errored += 1

    return {
        "scanned": len(connections),
        "refreshed": refreshed,
        "needs_reauth": needs_reauth,
        "errored": errored,
    }


def refresh_linkedin_tokens() -> dict:
    """RQ entry point. Runs the async refresh loop in a fresh event loop,
    then re-enqueues itself so the loop keeps running indefinitely.

    Returns a summary dict so RQ's result storage and ops dashboards
    have something to grab onto.
    """
    logger.info("linkedin token refresh tick")
    summary = asyncio.run(_refresh_due())
    logger.info("linkedin token refresh done summary=%s", summary)
    _enqueue_next()
    return summary


def _enqueue_next() -> None:
    """Schedule the next refresh tick. Best-effort — if Redis is down we
    log and continue; the worker's startup hook will reseed on next boot.
    """
    try:
        redis_conn = Redis.from_url(settings.redis_url)
        queue = Queue("default", connection=redis_conn)
        queue.enqueue_in(
            RECURRING_INTERVAL,
            refresh_linkedin_tokens,
            job_id=RECURRING_JOB_ID,
        )
    except Exception:  # noqa: BLE001
        logger.exception("could not enqueue next linkedin refresh — worker startup will reseed")


def ensure_scheduled() -> None:
    """Idempotent seeder called from `worker.main()` on startup. Enqueues
    the job to run immediately if no copy is queued or scheduled.
    """
    redis_conn = Redis.from_url(settings.redis_url)
    queue = Queue("default", connection=redis_conn)
    # If a job with this id is already pending or scheduled, leave it.
    from rq.job import Job

    try:
        existing = Job.fetch(RECURRING_JOB_ID, connection=redis_conn)
        if existing.get_status() in ("queued", "scheduled", "started", "deferred"):
            logger.info("linkedin refresh already scheduled status=%s", existing.get_status())
            return
    except Exception:  # noqa: BLE001 — Job.fetch raises NoSuchJobError when missing
        pass
    queue.enqueue_in(
        timedelta(seconds=30),  # short delay so the worker has time to register itself
        refresh_linkedin_tokens,
        job_id=RECURRING_JOB_ID,
    )
    logger.info("seeded linkedin refresh — next tick in 30s, then every %s", RECURRING_INTERVAL)
