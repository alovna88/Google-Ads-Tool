"""Playbook model. The steering wheel — per-client human-editable context."""

import uuid

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agency_ads.models.base import Base, Timestamps, UUIDPrimaryKey


class Playbook(UUIDPrimaryKey, Timestamps, Base):
    """One Playbook row = one saved version of a client's playbook markdown.

    Each save creates a new row. `version` is monotonic per client.
    The structured `parsed` jsonb holds the extracted fields the audit and
    LLM layers read at runtime.
    """

    __tablename__ = "playbooks"
    __table_args__ = (
        UniqueConstraint("client_id", "version", name="uq_playbook_client_version"),
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    parsed: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    client: Mapped["Client"] = relationship(back_populates="playbooks")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Playbook client={self.client_id} v{self.version}>"
