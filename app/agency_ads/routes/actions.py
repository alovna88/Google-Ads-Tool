"""Action queue endpoints.

GET    /actions          list all actions, filterable by status / client
PATCH  /actions/{id}     approve or reject; approval triggers (stub) execution

Approval flow:
    proposed --approve--> approved --(executor)--> executed | failed
             --reject---> rejected
"""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agency_ads.db import session_dependency
from agency_ads.dependencies import current_user
from agency_ads.models import Action, Client, User
from agency_ads.schemas.action import (
    ActionList,
    ActionRead,
    ActionUpdate,
    ActionWithClient,
)
from agency_ads.services import action_executor

router = APIRouter(dependencies=[Depends(current_user)])

VALID_STATUSES = {"proposed", "approved", "rejected", "executed", "failed", "expired"}


@router.get("", response_model=ActionList)
async def list_actions(
    status_filter: Annotated[str | None, Query(alias="status")] = "proposed",
    client_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    session: AsyncSession = Depends(session_dependency),
) -> ActionList:
    if status_filter and status_filter not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid status; must be one of {sorted(VALID_STATUSES)}",
        )

    # Join client so the cross-client queue can show client name/slug.
    stmt = (
        select(Action, Client)
        .join(Client, Action.client_id == Client.id)
        .order_by(Action.created_at.desc())
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(Action.status == status_filter)
    if client_id:
        stmt = stmt.where(Action.client_id == client_id)

    result = await session.execute(stmt)
    rows = result.all()
    items = [
        ActionWithClient(
            **ActionRead.model_validate(a).model_dump(),
            client_name=c.name,
            client_slug=c.slug,
        )
        for a, c in rows
    ]
    return ActionList(items=items, total=len(items))


@router.patch("/{action_id}", response_model=ActionWithClient)
async def update_action(
    action_id: uuid.UUID,
    payload: ActionUpdate,
    session: AsyncSession = Depends(session_dependency),
    user: User = Depends(current_user),
) -> ActionWithClient:
    result = await session.execute(
        select(Action, Client)
        .join(Client, Action.client_id == Client.id)
        .where(Action.id == action_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="action not found")
    action, client = row

    if action.status != "proposed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"action is in status '{action.status}'; only 'proposed' actions can transition",
        )

    now = datetime.now(timezone.utc)

    if payload.transition == "reject":
        action.status = "rejected"
        action.approver_id = user.id
        action.approved_at = now
    else:  # approve
        action.status = "approved"
        action.approver_id = user.id
        action.approved_at = now
        # Execute synchronously for now. Once real google-ads calls are
        # in, we'll enqueue and let the worker handle it.
        try:
            execution = action_executor.execute_action(action)
            action.status = "executed"
            action.executed_at = now
            action.execution_result = execution
        except Exception as e:  # noqa: BLE001
            action.status = "failed"
            action.execution_result = {
                "status": "error",
                "message": str(e),
                "executed_at": now.isoformat(),
            }

    await session.flush()

    return ActionWithClient(
        **ActionRead.model_validate(action).model_dump(),
        client_name=client.name,
        client_slug=client.slug,
    )
