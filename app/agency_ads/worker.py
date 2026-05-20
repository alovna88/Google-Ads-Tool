"""RQ worker entry point. Run with `python -m agency_ads.worker`.

Also seeds recurring background work on startup. Recurring jobs
re-enqueue themselves at the end of each run; the seeder here exists
to bootstrap that loop on first boot and to recover from a long
outage where the chain was lost.
"""

import logging

from redis import Redis
from rq import Queue, Worker

from agency_ads.config import settings
from agency_ads.jobs.refresh_linkedin_tokens import ensure_scheduled as ensure_linkedin_refresh

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

QUEUES = ["high", "default", "low"]


def main() -> None:
    redis_conn = Redis.from_url(settings.redis_url)
    queues = [Queue(name, connection=redis_conn) for name in QUEUES]
    try:
        ensure_linkedin_refresh()
    except Exception:  # noqa: BLE001
        logger.exception("failed to seed linkedin refresh — worker will still process queue")
    logger.info("rq worker starting queues=%s", QUEUES)
    worker = Worker(queues, connection=redis_conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
