"""Action model — the queue spine."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from agency_ads.models.base import Base, UUIDPrimaryKey


class Action(UUIDPrimaryKey, Base):
    """A proposed change to a Google Ads account, awaiting approval and
    execution. State machine:
        proposed → approved → executed
                 → rejected
                 → expired (auto, after expires_at)
    """

    __tablename__ = "actions"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    audit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    diff: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    reasoning_md: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    expected_impact: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(4), default="L2", nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        default="proposed",
        nullable=False,
        index=True,
    )
    approver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Action {self.type} {self.status}>"
