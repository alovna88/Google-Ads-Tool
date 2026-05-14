"""FastAPI app entry point. Run with `uvicorn agency_ads.main:app`."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agency_ads import __version__
from agency_ads.config import settings
from agency_ads.routes import api_router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting agency-ads api version=%s env=%s", __version__, settings.environment)
    yield
    logger.info("stopping agency-ads api")


app = FastAPI(
    title="Agency Google Ads Tool API",
    version=__version__,
    lifespan=lifespan,
)

# With cookie-based sessions we must pin the origin — wildcard is invalid
# alongside allow_credentials=True. In dev the browser always hits the web
# origin (Next.js rewrites proxy /api/*), so CORS is rarely exercised; we
# allow web_base_url anyway in case of direct cross-origin calls.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
