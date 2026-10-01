"""Market data provenance: ingestion_run, per-bar source/run/retrieved_at, document locators

Revision ID: a7c3e1f09b42
Revises: 23093aff0f19
Create Date: 2026-10-02

Adding the NOT NULL provenance columns fails on a table that still holds rows. That is
intended: rows with unknown origin must be purged, not grandfathered in.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7c3e1f09b42"
down_revision: Union[str, Sequence[str], None] = "23093aff0f19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BAR_TABLES = ("price_ohlcv", "index_ohlcv")


def upgrade() -> None:
    op.create_table(
        "ingestion_run",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("params", sa.JSON(), nullable=True),
        sa.Column("rows_inserted", sa.Integer(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.CheckConstraint("status IN ('running','ok','partial','failed')", name="ck_ingestion_run_status"),
    )

    for table in BAR_TABLES:
        op.add_column(table, sa.Column("source", sa.String(40), nullable=False))
        op.add_column(table, sa.Column("ingestion_run_id", sa.Integer(), sa.ForeignKey("ingestion_run.id"), nullable=False))
        op.add_column(
            table,
            sa.Column("retrieved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index(f"ix_{table}_ingestion_run_id", table, ["ingestion_run_id"])
        op.create_check_constraint(f"ck_{table}_source_nonempty", table, "source <> ''")

    op.create_check_constraint(
        "ck_source_document_locator", "source_document", "url IS NOT NULL OR local_path IS NOT NULL"
    )
    op.create_check_constraint("ck_sources_locator", "sources", "url IS NOT NULL OR file_path IS NOT NULL")


def downgrade() -> None:
    op.drop_constraint("ck_sources_locator", "sources", type_="check")
    op.drop_constraint("ck_source_document_locator", "source_document", type_="check")
    for table in BAR_TABLES:
        op.drop_constraint(f"ck_{table}_source_nonempty", table, type_="check")
        op.drop_index(f"ix_{table}_ingestion_run_id", table_name=table)
        op.drop_column(table, "retrieved_at")
        op.drop_column(table, "ingestion_run_id")
        op.drop_column(table, "source")
    op.drop_table("ingestion_run")
