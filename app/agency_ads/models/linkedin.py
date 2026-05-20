"""LinkedIn Ads OAuth connection per client.

One row per (Client, LinkedIn account-owner) pair. Tokens are stored
in plain text in v0 — production should layer column-level encryption
(pgcrypto / Fernet) on `access_token` and `refresh_token`. The refresh
worker uses `expires_at` and `refresh_token_expires_at` to decide what
to rotate vs. mark for re-auth.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agency_ads.models.base import Base, Timestamps, UUIDPrimaryKey

CONNECTION_STATUS = ("connected", "expired", "needs_reauth", "revoked", "error")


class LinkedinConnection(UUIDPrimaryKey, Timestamps, Base):
    """Stored LinkedIn Ads OAuth connection for an agency Client.

    `status` is the canonical "is this connection usable right now" flag.
    The refresh job updates it; the API client reads it before making
    calls and short-circuits to a clear error when not `connected`.
    """

    __tablename__ = "linkedin_connections"
    __table_args__ = (
        UniqueConstraint("client_id", "linkedin_member_urn", name="uq_linkedin_client_member"),
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The LinkedIn member (person) who authorized the connection.
    # Format: urn:li:person:xxxx
    linkedin_member_urn: Mapped[str] = mapped_column(String(128), nullable=False)
    linkedin_member_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # OAuth tokens. Access token rotates frequently (~60d); refresh token
    # rotates infrequently and can outlive a year if used.
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scope: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Cached list of LinkedIn ad account URNs this member can manage.
    # Refreshed each time we successfully call /adAccounts. JSONB so we
    # can store {"urn": "...", "name": "...", "role": "..."} per row.
    ad_accounts: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="connected")
    last_refreshed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    connected_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    client: Mapped["Client"] = relationship(back_populates="linkedin_connections")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<LinkedinConnection client={self.client_id} "
            f"member={self.linkedin_member_urn} status={self.status}>"
        )
