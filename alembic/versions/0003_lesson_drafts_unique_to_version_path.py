"""lesson_drafts unique constraint on (to_version, path)

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-05 22:00:00.000000

KNOW-2273 review fix. The ``lesson_drafts`` table was provisioned in
``0001_baseline`` with only a non-unique ``Index`` on
``(to_version, path)``. Two concurrent POSTs to ``/api/drafts`` could
both pass the route's existence check and both INSERT, leaving a
duplicate row for the same lesson. Replace the plain index with a
unique constraint so the database itself rejects the second INSERT;
the route catches the ``IntegrityError`` and retries as an UPDATE.

Idempotent: drops the old index by name (skips if absent) and creates
the new constraint by name (skips if already present).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_INDEX_NAME = "ix_lesson_drafts_to_version_path"
_CONSTRAINT_NAME = "uq_lesson_drafts_to_version_path"


def upgrade() -> None:
    # Drop the old non-unique index (if it exists). Some dev DBs may
    # have already auto-named it differently; if so, this is a no-op
    # and the constraint creation below adds its own unique index.
    op.execute(f"DROP INDEX IF EXISTS {_INDEX_NAME}")
    op.create_unique_constraint(
        _CONSTRAINT_NAME, "lesson_drafts", ["to_version", "path"]
    )


def downgrade() -> None:
    op.drop_constraint(_CONSTRAINT_NAME, "lesson_drafts", type_="unique")
    op.create_index(
        _INDEX_NAME, "lesson_drafts", ["to_version", "path"], unique=False
    )
