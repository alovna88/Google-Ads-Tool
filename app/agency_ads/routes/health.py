"""Health + version endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agency_ads import __version__
from agency_ads.config import settings
from agency_ads.db import session_dependency

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__, "env": settings.environment}


@router.get("/health/db")
async def health_db(session: AsyncSession = Depends(session_dependency)) -> dict[str, str]:
    result = await session.execute(text("SELECT 1"))
    value = result.scalar_one()
    return {"status": "ok", "db": "reachable", "result": str(value)}
