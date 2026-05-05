"""report_lesson_drafts

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-05 18:00:00.000000

KNOW-2276 — per-lesson editor state for the report. Auto-saved by the
report JS, reset by "Reset to original," marked with the version-folder
path on Save to Version Folder.

Distinct from the ``lesson_drafts`` table created in baseline (the
Skilljar release-pipeline draft).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_lesson_drafts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("lesson_dir", sa.String(length=512), nullable=False),
        sa.Column(
            "decisions_json",
            sa.JSON().with_variant(
                postgresql.JSONB(astext_type=sa.Text()), "postgresql"
            ),
            nullable=False,
        ),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column(
            "saved_to_version_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "saved_to_version_path", sa.String(length=1024), nullable=True
        ),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_report_lesson_drafts_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["users.id"],
            name=op.f("fk_report_lesson_drafts_updated_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_report_lesson_drafts")),
        sa.UniqueConstraint(
            "run_id",
            "lesson_dir",
            name="uq_report_lesson_drafts_run_id_lesson_dir",
        ),
    )
    op.create_index(
        "ix_report_lesson_drafts_run_id_updated_at",
        "report_lesson_drafts",
        ["run_id", "updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_report_lesson_drafts_run_id_updated_at",
        table_name="report_lesson_drafts",
    )
    op.drop_table("report_lesson_drafts")
