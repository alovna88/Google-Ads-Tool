"""Audit + AuditCheckResult models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agency_ads.models.base import Base, UUIDPrimaryKey


class Audit(UUIDPrimaryKey, Base):
    """One run of the audit engine against one client snapshot."""

    __tablename__ = "audits"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    overall_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    grade: Mapped[str] = mapped_column(String(2), nullable=False)
    category_scores: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    check_results: Mapped[list["AuditCheckResult"]] = relationship(
        back_populates="audit",
        cascade="all, delete-orphan",
        # No order_by — alphabetical on severity would be misleading
        # (critical, high, low, medium). The route / UI sorts by rank.
    )

    def __repr__(self) -> str:
        return f"<Audit client={self.client_id} grade={self.grade}>"


class AuditCheckResult(UUIDPrimaryKey, Base):
    """One check execution within an audit."""

    __tablename__ = "audit_check_results"

    audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    check_id: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    suggested_fix_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_action_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actions.id", ondelete="SET NULL"),
        nullable=True,
    )

    audit: Mapped["Audit"] = relationship(back_populates="check_results")
    draft_action: Mapped["Action | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        flag = "✓" if self.passed else "✗"
        return f"<AuditCheckResult {self.check_id} {flag}>"
