"""Pydantic schemas for LinkedIn Ads endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LinkedinAdAccount(BaseModel):
    """Cached entry under LinkedinConnection.ad_accounts."""

    urn: str  # urn:li:sponsoredAccount:123456789
    id: str  # numeric id parsed from the URN
    name: str | None = None
    currency: str | None = None
    status: str | None = None
    role: str | None = None  # ACCOUNT_MANAGER, CAMPAIGN_MANAGER, ...


class LinkedinConnectionRead(BaseModel):
    """Safe outward-facing view of a connection. Excludes tokens."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    linkedin_member_urn: str
    linkedin_member_name: str | None
    scope: str
    status: str
    expires_at: datetime
    refresh_token_expires_at: datetime | None
    ad_accounts: list[LinkedinAdAccount] | None
    last_refreshed_at: datetime | None
    last_error: str | None
    last_error_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LinkedinConnectionList(BaseModel):
    items: list[LinkedinConnectionRead]
    total: int


class LinkedinConnectStartResponse(BaseModel):
    """Returned when an authenticated user kicks off OAuth from the API
    rather than as a redirect (useful when the frontend wants to open
    LinkedIn in a popup).
    """

    authorize_url: str
    state: str


class LinkedinCampaign(BaseModel):
    """A campaign within an ad account, as returned by the LinkedIn
    Marketing API and trimmed to the fields we surface.
    """

    id: str
    name: str
    status: str
    type: str | None = None
    objective_type: str | None = None
    daily_budget: float | None = None
    total_budget: float | None = None
    currency: str | None = None
    run_schedule_start: datetime | None = None
    run_schedule_end: datetime | None = None


class LinkedinCampaignList(BaseModel):
    items: list[LinkedinCampaign]
    total: int


class LinkedinAnalyticsRow(BaseModel):
    """One row of /adAnalytics output. `pivot_value` carries the entity
    URN the row aggregates over (campaign, creative, ...). Extra metrics
    flow through `metrics` so we don't have to model every field.
    """

    pivot_value: str | None = None
    date_range_start: str | None = None
    date_range_end: str | None = None
    impressions: int = 0
    clicks: int = 0
    cost_in_usd: float = 0.0
    cost_in_local_currency: float = 0.0
    external_website_conversions: int = 0
    one_click_leads: int = 0
    metrics: dict = Field(default_factory=dict)


class LinkedinAnalytics(BaseModel):
    items: list[LinkedinAnalyticsRow]


class LinkedinHealth(BaseModel):
    """At-a-glance connection health surfaced to the UI + MCP server."""

    client_id: uuid.UUID
    client_slug: str
    connected: bool
    status: str  # connected / expired / needs_reauth / revoked / error / never
    expires_at: datetime | None
    seconds_until_expiry: int | None
    last_refreshed_at: datetime | None
    last_error: str | None
