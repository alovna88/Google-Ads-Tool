"""Playbook endpoints — get current, save new version."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agency_ads.db import session_dependency
from agency_ads.schemas.playbook import PlaybookRead, PlaybookUpsert
from agency_ads.services import client_service

router = APIRouter()


@router.get("/{client_id}/playbook", response_model=PlaybookRead)
async def get_playbook(
    client_id: uuid.UUID,
    session: AsyncSession = Depends(session_dependency),
) -> PlaybookRead:
    client = await client_service.get_client(session, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")
    playbook = await client_service.get_latest_playbook(session, client_id)
    if playbook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no playbook saved yet for this client",
        )
    return PlaybookRead.model_validate(playbook)


@router.put("/{client_id}/playbook", response_model=PlaybookRead)
async def save_playbook(
    client_id: uuid.UUID,
    payload: PlaybookUpsert,
    session: AsyncSession = Depends(session_dependency),
) -> PlaybookRead:
    client = await client_service.get_client(session, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")
    playbook = await client_service.save_playbook(session, client_id, payload.content_md)
    return PlaybookRead.model_validate(playbook)
