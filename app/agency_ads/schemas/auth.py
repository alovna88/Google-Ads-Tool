"""Schemas for auth endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    role: str
    created_at: datetime
