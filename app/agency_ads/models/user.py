"""User model. Agency staff who log in to the tool."""

from typing import Literal

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from agency_ads.models.base import Base, Timestamps, UUIDPrimaryKey

UserRole = Literal["admin", "strategist", "analyst"]


class User(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(String(32), default="analyst", nullable=False)

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"
