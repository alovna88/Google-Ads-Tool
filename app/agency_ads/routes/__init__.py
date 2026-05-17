"""FastAPI route modules."""

from fastapi import APIRouter

from agency_ads.routes import actions, audits, auth, clients, health, playbooks

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(playbooks.router, prefix="/clients", tags=["playbooks"])
api_router.include_router(audits.client_audits_router, prefix="/clients", tags=["audits"])
api_router.include_router(audits.audits_router, prefix="/audits", tags=["audits"])
api_router.include_router(actions.router, prefix="/actions", tags=["actions"])
