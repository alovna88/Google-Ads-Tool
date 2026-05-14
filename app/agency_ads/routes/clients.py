"""Clients CRUD endpoints. All require an authenticated staff user."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from agency_ads.db import session_dependency
from agency_ads.dependencies import current_user
from agency_ads.models import User
from agency_ads.schemas.client import ClientCreate, ClientList, ClientRead
from agency_ads.services import client_service

router = APIRouter(dependencies=[Depends(current_user)])


@router.get("", response_model=ClientList)
async def list_clients_endpoint(
    session: AsyncSession = Depends(session_dependency),
) -> ClientList:
    items, total = await client_service.list_clients(session)
    return ClientList(items=[ClientRead.model_validate(c) for c in items], total=total)


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client_endpoint(
    payload: ClientCreate,
    session: AsyncSession = Depends(session_dependency),
    user: User = Depends(current_user),
) -> ClientRead:
    existing = await client_service.get_client_by_slug(session, payload.slug)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"client with slug '{payload.slug}' already exists",
        )
    try:
        client = await client_service.create_client(session, payload)
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e.orig)) from e
    return ClientRead.model_validate(client)


@router.get("/{client_id}", response_model=ClientRead)
async def get_client_endpoint(
    client_id: uuid.UUID,
    session: AsyncSession = Depends(session_dependency),
) -> ClientRead:
    client = await client_service.get_client(session, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="client not found")
    return ClientRead.model_validate(client)
