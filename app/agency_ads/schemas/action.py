"""Pydantic schemas for action queue endpoints."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

ActionStatus = Literal["proposed", "approved", "rejected", "executed", "failed", "expired"]
ActionTransition = Literal["approve", "reject"]


class ActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    audit_id: uuid.UUID | None
    type: str
    target: dict[str, Any]
    diff: dict[str, Any]
    reasoning_md: str
    evidence: dict[str, Any]
    expected_impact: dict[str, Any]
    risk_tier: str
    status: ActionStatus
    approver_id: uuid.UUID | None
    approved_at: datetime | None
    executed_at: datetime | None
    execution_result: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None


class ActionWithClient(ActionRead):
    """ActionRead + the client's slug + name, for the cross-client queue."""

    client_name: str
    client_slug: str


class ActionList(BaseModel):
    items: list[ActionWithClient]
    total: int


class ActionUpdate(BaseModel):
    """Body for `PATCH /actions/{id}`.

    `transition` drives the state machine:
        approve → status: approved → executor runs → executed or failed
        reject  → status: rejected
    """

    transition: ActionTransition
