"""Corporate-action ex-dates and evidence, coverage windows, quarantine, point-in-time facts

Revision ID: c4d9f2a17e60
Revises: a7c3e1f09b42
Create Date: 2026-10-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4d9f2a17e60"
down_revision: Union[str, Sequence[str], None] = "a7c3e1f09b42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for name, col in [
        ("ex_date", sa.Date()),
        ("book_closure_start", sa.Date()),
        ("book_closure_end", sa.Date()),
        ("cash_per_share", sa.Numeric(12, 4)),
        ("evidence", sa.Text()),
        ("source_page", sa.Integer()),
    ]:
        op.add_column("corporate_action", sa.Column(name, col, nullable=True))
    op.add_column("corporate_action", sa.Column("ingestion_run_id", sa.Integer(), sa.ForeignKey("ingestion_run.id"), nullable=True))
    op.create_index("ix_corporate_action_ex_date", "corporate_action", ["ex_date"])

    op.create_table(
        "corporate_action_coverage",
        sa.Column("security_id", sa.Integer(), sa.ForeignKey("security.id"), primary_key=True),
        sa.Column("covered_from", sa.Date(), nullable=False),
        sa.Column("covered_to", sa.Date(), nullable=False),
        sa.Column("source", sa.String(60), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "quarantined_row",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ingestion_run_id", sa.Integer(), sa.ForeignKey("ingestion_run.id"), nullable=False),
        sa.Column("target_table", sa.String(40), nullable=False),
        sa.Column("natural_key", sa.String(200), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_quarantined_row_ingestion_run_id", "quarantined_row", ["ingestion_run_id"])

    for name in ("rows_seen", "rows_updated", "rows_rejected"):
        op.add_column("ingestion_run", sa.Column(name, sa.Integer(), server_default="0", nullable=False))

    op.add_column("financial_fact", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("financial_fact", sa.Column("publication_document_id", sa.Integer(), sa.ForeignKey("source_document.id"), nullable=True))
    op.add_column("financial_fact", sa.Column("ingestion_run_id", sa.Integer(), sa.ForeignKey("ingestion_run.id"), nullable=True))


def downgrade() -> None:
    for name in ("ingestion_run_id", "publication_document_id", "published_at"):
        op.drop_column("financial_fact", name)
    for name in ("rows_rejected", "rows_updated", "rows_seen"):
        op.drop_column("ingestion_run", name)
    op.drop_index("ix_quarantined_row_ingestion_run_id", table_name="quarantined_row")
    op.drop_table("quarantined_row")
    op.drop_table("corporate_action_coverage")
    op.drop_index("ix_corporate_action_ex_date", table_name="corporate_action")
    for name in ("ingestion_run_id", "source_page", "evidence", "cash_per_share",
                 "book_closure_end", "book_closure_start", "ex_date"):
        op.drop_column("corporate_action", name)
