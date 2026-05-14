"""RQ worker entry point. Run with `python -m agency_ads.worker`."""

import logging

from redis import Redis
from rq import Queue, Worker

from agency_ads.config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

QUEUES = ["high", "default", "low"]


def main() -> None:
    redis_conn = Redis.from_url(settings.redis_url)
    queues = [Queue(name, connection=redis_conn) for name in QUEUES]
    logger.info("rq worker starting queues=%s", QUEUES)
    worker = Worker(queues, connection=redis_conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
