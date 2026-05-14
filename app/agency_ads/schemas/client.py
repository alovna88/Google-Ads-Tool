"""Pydantic schemas for Client endpoints."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
CID_RE = re.compile(r"^\d{10}$")


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=64)
    google_ads_customer_id: str | None = Field(default=None)
    login_customer_id: str | None = Field(default=None)
    timezone: str = Field(default="UTC", max_length=64)
    currency: str = Field(default="USD", min_length=3, max_length=3)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not SLUG_RE.match(v):
            raise ValueError("slug must be lowercase a-z, 0-9, hyphen; 1-64 chars; no leading/trailing hyphen")
        return v

    @field_validator("google_ads_customer_id", "login_customer_id")
    @classmethod
    def validate_cid(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        stripped = v.replace("-", "")
        if not CID_RE.match(stripped):
            raise ValueError("customer id must be 10 digits (dashes allowed but stripped)")
        return stripped


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    google_ads_customer_id: str | None
    login_customer_id: str | None
    timezone: str
    currency: str
    active: bool
    created_at: datetime
    updated_at: datetime


class ClientList(BaseModel):
    items: list[ClientRead]
    total: int
