"""Client + Playbook business logic."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agency_ads.models import Client, Playbook
from agency_ads.schemas.client import ClientCreate
from agency_ads.services.playbook_parser import parse_playbook


async def list_clients(session: AsyncSession) -> tuple[list[Client], int]:
    result = await session.execute(select(Client).order_by(Client.name))
    items = list(result.scalars().all())
    total = (await session.execute(select(func.count(Client.id)))).scalar_one()
    return items, total


async def get_client(session: AsyncSession, client_id: uuid.UUID) -> Client | None:
    result = await session.execute(select(Client).where(Client.id == client_id))
    return result.scalar_one_or_none()


async def get_client_by_slug(session: AsyncSession, slug: str) -> Client | None:
    result = await session.execute(select(Client).where(Client.slug == slug))
    return result.scalar_one_or_none()


async def create_client(session: AsyncSession, payload: ClientCreate) -> Client:
    client = Client(
        name=payload.name,
        slug=payload.slug,
        google_ads_customer_id=payload.google_ads_customer_id,
        login_customer_id=payload.login_customer_id,
        timezone=payload.timezone,
        currency=payload.currency,
    )
    session.add(client)
    await session.flush()
    return client


async def get_latest_playbook(
    session: AsyncSession, client_id: uuid.UUID
) -> Playbook | None:
    result = await session.execute(
        select(Playbook)
        .where(Playbook.client_id == client_id)
        .order_by(Playbook.version.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def save_playbook(
    session: AsyncSession, client_id: uuid.UUID, content_md: str
) -> Playbook:
    """Save a new playbook version. Each save is a new row; previous
    versions are immutable history.
    """
    latest = await get_latest_playbook(session, client_id)
    next_version = (latest.version + 1) if latest else 1

    playbook = Playbook(
        client_id=client_id,
        version=next_version,
        content_md=content_md,
        parsed=parse_playbook(content_md),
    )
    session.add(playbook)
    await session.flush()
    return playbook
