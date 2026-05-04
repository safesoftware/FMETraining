"""Smoke tests for the SQLAlchemy 2.x model definitions.

Verifies that:
- every model in ``app.models`` is registered on ``Base.metadata``
- every table can be created against an empty SQLite engine (catches
  obvious type/relationship/foreign-key mistakes)
- the same teardown round-trips cleanly

Postgres-specific behaviour (JSONB, citext, etc.) is intentionally NOT
exercised here — those columns use ``with_variant`` fallbacks for
SQLite. End-to-end Postgres tests live in the integration suite once
the test container fixture lands.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from app.models import (
    Base,
    ContentCache,
    JiraCache,
    Job,
    LessonDraft,
    ReleaseHistory,
    ReleaseLock,
    Run,
    RunLog,
    RunStep,
    S3ImageCache,
    SkilljarCourse,
    SkilljarLesson,
    SkilljarPublishedPath,
    User,
)

EXPECTED_MODELS = {
    User,
    Run,
    RunStep,
    RunLog,
    Job,
    SkilljarCourse,
    SkilljarLesson,
    SkilljarPublishedPath,
    LessonDraft,
    ReleaseLock,
    ReleaseHistory,
    ContentCache,
    S3ImageCache,
    JiraCache,
}


@pytest.fixture
def sqlite_engine() -> Engine:
    return create_engine("sqlite:///:memory:")


def test_every_model_is_on_base_metadata() -> None:
    registered = {m.class_ for m in Base.registry.mappers}
    missing = EXPECTED_MODELS - registered
    assert not missing, f"models not registered on Base.metadata: {missing}"


def test_metadata_has_all_expected_tables() -> None:
    expected_tables = {model.__tablename__ for model in EXPECTED_MODELS}
    actual_tables = set(Base.metadata.tables.keys())
    missing = expected_tables - actual_tables
    assert not missing, f"tables missing from metadata: {missing}"


def test_create_all_then_drop_all_succeeds(sqlite_engine: Engine) -> None:
    """A clean upgrade/downgrade against SQLite catches type mismatches,
    bad FK references, and undefined relationships."""
    Base.metadata.create_all(sqlite_engine)
    inspector = inspect(sqlite_engine)
    actual = set(inspector.get_table_names())
    expected = {model.__tablename__ for model in EXPECTED_MODELS}
    assert expected.issubset(actual), (
        f"create_all produced tables {actual}; expected superset of {expected}"
    )
    Base.metadata.drop_all(sqlite_engine)
    inspector = inspect(sqlite_engine)
    assert set(inspector.get_table_names()) == set()


def test_every_table_has_a_primary_key(sqlite_engine: Engine) -> None:
    Base.metadata.create_all(sqlite_engine)
    inspector = inspect(sqlite_engine)
    tables_without_pk: list[str] = []
    for tname in {model.__tablename__ for model in EXPECTED_MODELS}:
        pk = inspector.get_pk_constraint(tname)
        if not pk.get("constrained_columns"):
            tables_without_pk.append(tname)
    assert not tables_without_pk, (
        f"tables missing a primary key: {tables_without_pk}"
    )


def test_naming_convention_applied() -> None:
    """Constraint names must come from the project naming convention so
    Alembic autogenerate is stable across environments."""
    convention = Base.metadata.naming_convention
    assert convention.get("pk") == "pk_%(table_name)s"
    assert convention.get("fk") == (
        "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
    )
