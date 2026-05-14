"""Pydantic schemas for Playbook endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlaybookUpsert(BaseModel):
    content_md: str = Field(min_length=1)


class PlaybookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    version: int
    content_md: str
    parsed: dict
    created_at: datetime
    updated_at: datetime
