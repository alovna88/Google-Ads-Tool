"""Daily Google Ads read sync per client.

Stub for the scaffold. Wires up the function signature so the scheduler
can register jobs; the real GAQL fetch + persist comes in the next commit
alongside the Google Ads OAuth flow.
"""

import logging
import uuid

logger = logging.getLogger(__name__)


def sync_client_account(client_id: str) -> dict:
    """Pull last-24h metrics for one client. Wired-up stub.

    Args:
        client_id: UUID string of the agency_ads.models.Client.

    Returns:
        Summary dict for the job result.
    """
    cid = uuid.UUID(client_id)
    logger.info("sync_client_account stub for client_id=%s", cid)
    # TODO(next-commit): open async session, load client, build GAQL,
    # call google-ads client, normalize, persist to metrics_daily.
    return {
        "client_id": str(cid),
        "status": "stub",
        "note": "real sync lands with OAuth + GAQL builder",
    }
