"""Action executor — turns an approved Action into a real Google Ads
mutation. Stub for now; real google-ads-python calls land with slice B.

Contract: `execute(action)` is called only on already-approved actions.
On success, returns a dict written to `action.execution_result`. On
failure, raises — the route catches and persists the failure.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from agency_ads.models import Action

logger = logging.getLogger(__name__)


class ActionExecutorNotImplemented(Exception):
    """Raised by stub executors. Caller writes a friendly message into
    execution_result instead of crashing the request.
    """


# Registry pattern so adding a new action type later means dropping a
# function into HANDLERS without touching the route.
HANDLERS: dict[str, "ActionHandler"] = {}


class ActionHandler:
    """Callable that executes one action type. Override for real types
    once we have a live google-ads client.
    """

    def __init__(self, action_type: str) -> None:
        self.action_type = action_type

    def execute(self, action: Action) -> dict[str, Any]:
        raise ActionExecutorNotImplemented(
            f"action type '{self.action_type}' has no live executor yet"
        )


def register(action_type: str) -> ActionHandler:
    handler = ActionHandler(action_type)
    HANDLERS[action_type] = handler
    return handler


# Pre-register every type we currently produce. They all stub for now.
for _t in (
    "set_conversion_window",
    "disable_auto_apply",
    "disable_display_expansion",
    "disable_search_partners",
    "set_target_cpa_cap",
    "add_negative",
    "pause_campaign",
    "edit_rsa_asset",
    "change_budget",
    "upload_oci",
):
    register(_t)


def execute_action(action: Action) -> dict[str, Any]:
    """Dispatch to the registered handler. Falls back to a marker result
    when no handler exists yet (slice B will replace these).
    """
    handler = HANDLERS.get(action.type)
    if handler is None:
        logger.warning("no handler for action type %s", action.type)
        return _stub_result(action, reason="no_handler")

    try:
        return handler.execute(action)
    except ActionExecutorNotImplemented:
        return _stub_result(action, reason="stub_executor")


def _stub_result(action: Action, *, reason: str) -> dict[str, Any]:
    return {
        "status": "stub",
        "reason": reason,
        "message": (
            "Action approved and marked executed, but no live Google Ads "
            "mutation ran. Real writes land when the Google Ads OAuth + "
            "API integration ships (slice B)."
        ),
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "type": action.type,
    }
