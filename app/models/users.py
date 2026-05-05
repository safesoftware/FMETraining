"""``users`` table -- Google-SSO identity row.

Plan section 2:

    users(id, email, name, picture_url, role, is_active, session_epoch,
          created_at, last_seen_at)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class User(Base):
    """Authenticated Safe Software staff user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    picture_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    # v1 has flat membership; the column is reserved for later RBAC.
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="member")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Bump to force-sign-out a user without deleting them.
    session_epoch: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User id={self.id!r} email={self.email!r}>"
