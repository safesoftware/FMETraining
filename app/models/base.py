"""Declarative base + shared column mixins."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# A consistent naming convention makes Alembic autogenerate stable across
# environments. Without it, constraint names default to whatever Postgres
# picks, which differs between databases and breaks migrations.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def _utcnow() -> datetime:
    """Return tz-aware UTC ``datetime`` for default timestamp columns."""

    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Project-wide declarative base."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """Common ``created_at`` / ``updated_at`` columns.

    Both columns are application-managed (Python defaults) rather than
    server-side ``func.now()`` so the same model code works against
    Postgres, SQLite (tests), or any other dialect without dialect-
    specific quirks.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )


def utc_now() -> datetime:
    """Public accessor for the same default used by ``TimestampMixin``."""

    return _utcnow()


__all__: list[str] = [
    "Base",
    "TimestampMixin",
    "utc_now",
]


# Help static checkers ignore unused ``Any`` import in some configs.
_: Any = None
