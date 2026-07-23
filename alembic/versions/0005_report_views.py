"""report_views

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-23 12:00:00.000000

KNOW-2166 — append-only usage log: one row per authenticated open of a run's
HTML report (``GET /report/{run_id}``). Backs the "was a report generated AND
opened, in which release cycle, by whom" adoption metric without depending on
the in-app accept/reject workflow. See ``app/models/report_views.py``.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_views",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_report_views_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_report_views_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_report_views")),
    )
    op.create_index(
        op.f("ix_report_views_run_id"), "report_views", ["run_id"], unique=False
    )
    op.create_index(
        op.f("ix_report_views_user_id"), "report_views", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_report_views_viewed_at"),
        "report_views",
        ["viewed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_report_views_viewed_at"), table_name="report_views")
    op.drop_index(op.f("ix_report_views_user_id"), table_name="report_views")
    op.drop_index(op.f("ix_report_views_run_id"), table_name="report_views")
    op.drop_table("report_views")
