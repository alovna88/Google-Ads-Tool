"""Client model. One per managed Google Ads account."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agency_ads.models.base import Base, Timestamps, UUIDPrimaryKey


class Client(UUIDPrimaryKey, Timestamps, Base):
    """An agency-managed client. Maps 1:1 to a Google Ads customer ID.

    The MCC login_customer_id is optional — set when the agency has a Manager
    Account fronting this client's CID.
    """

    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    google_ads_customer_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    login_customer_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    playbooks: Mapped[list["Playbook"]] = relationship(  # noqa: F821
        back_populates="client",
        cascade="all, delete-orphan",
        order_by="Playbook.version.desc()",
    )

    def __repr__(self) -> str:
        return f"<Client {self.slug} cid={self.google_ads_customer_id}>"
