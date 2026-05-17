"""Audit endpoints — run audits, list history, fetch detail."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agency_ads.audits.runner import run_audit
from agency_ads.db import session_dependency
from agency_ads.dependencies import current_user
from agency_ads.models import Audit, User
from agency_ads.schemas.audit import (
    AuditCreate,
    AuditList,
    AuditRead,
    AuditSummary,
)
from agency_ads.services import client_service

# Two routers — one mounted under /clients/{id}/audits for create/list,
# another under /audits/{id} for detail. Keeps URLs clean.
client_audits_router = APIRouter(dependencies=[Depends(current_user)])
audits_router = APIRouter(dependencies=[Depends(current_user)])


@client_audits_router.post(
    "/{client_id}/audits",
    response_model=AuditRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_audit(
    client_id: uuid.UUID,
    payload: AuditCreate,
    session: AsyncSession = Depends(session_dependency),
    user: User = Depends(current_user),
) -> AuditRead:
    client = await client_service.get_client(session, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")
    audit = await run_audit(
        session,
        client=client,
        snapshot=payload.snapshot,
        user=user,
    )
    # Eager-load check_results for the response.
    result = await session.execute(
        select(Audit)
        .options(selectinload(Audit.check_results))
        .where(Audit.id == audit.id)
    )
    fresh = result.scalar_one()
    return AuditRead.model_validate(fresh)


@client_audits_router.get("/{client_id}/audits", response_model=AuditList)
async def list_client_audits(
    client_id: uuid.UUID,
    session: AsyncSession = Depends(session_dependency),
) -> AuditList:
    client = await client_service.get_client(session, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")
    result = await session.execute(
        select(Audit)
        .where(Audit.client_id == client_id)
        .order_by(Audit.run_at.desc())
        .limit(50)
    )
    items = list(result.scalars().all())
    return AuditList(
        items=[AuditSummary.model_validate(a) for a in items],
        total=len(items),
    )


@audits_router.get("/{audit_id}", response_model=AuditRead)
async def get_audit(
    audit_id: uuid.UUID,
    session: AsyncSession = Depends(session_dependency),
) -> AuditRead:
    result = await session.execute(
        select(Audit)
        .options(selectinload(Audit.check_results))
        .where(Audit.id == audit_id)
    )
    audit = result.scalar_one_or_none()
    if audit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="audit not found")
    return AuditRead.model_validate(audit)
