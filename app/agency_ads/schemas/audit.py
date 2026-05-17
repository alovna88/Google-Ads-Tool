"""Pydantic schemas for audit endpoints."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditCreate(BaseModel):
    """Body for `POST /clients/{id}/audits`.

    `snapshot` is the AccountSnapshot dict (see audits/snapshot.py).
    Empty / omitted means use the demo fixture — fine for kicking the
    tires before Google Ads sync exists.
    """

    snapshot: dict[str, Any] | None = Field(default=None)


class CategoryScore(BaseModel):
    category: str
    score: float
    grade: str


class AuditCheckResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    check_id: str
    category: str
    title: str
    passed: bool
    severity: str
    weight: float
    evidence: dict[str, Any]
    suggested_fix_md: str | None
    draft_action_id: uuid.UUID | None


class AuditSummary(BaseModel):
    """Lightweight row for the audit-history list on a client page."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_at: datetime
    overall_score: float
    grade: str


class AuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    run_at: datetime
    overall_score: float
    grade: str
    category_scores: dict[str, Any]
    check_results: list[AuditCheckResultRead]


class AuditList(BaseModel):
    items: list[AuditSummary]
    total: int
