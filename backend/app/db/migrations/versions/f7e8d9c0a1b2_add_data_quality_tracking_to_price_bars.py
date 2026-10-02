"""Add data quality tracking: is_synthetic, quality_status for price bars

Revision ID: f7e8d9c0a1b2
Revises: c4d9f2a17e60
Create Date: 2026-10-02

These columns make it possible to distinguish:
- Real PSX data (quality_status='verified', is_synthetic=False)
- Provisional data (quality_status='provisional', is_synthetic=False)
- Synthetic/demo data (is_synthetic=True)
- Rejected/quarantined data (quality_status='rejected')

This is a prerequisite for audit trails, data lineage, and preventing synthetic data
from contaminating research outputs.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f7e8d9c0a1b2"
down_revision: Union[str, Sequence[str], None] = "c4d9f2a17e60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_synthetic flag to both OHLCV tables
    # Default to False (assume real data unless marked otherwise)
    for table in ("price_ohlcv", "index_ohlcv"):
        op.add_column(
            table,
            sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    # Add quality_status to track data provenance certainty
    # Values: 'unknown' (legacy rows), 'verified' (from real source), 'provisional' (best effort),
    #         'rejected' (should not be used for analysis)
    for table in ("price_ohlcv", "index_ohlcv"):
        op.add_column(
            table,
            sa.Column("quality_status", sa.String(20), nullable=False, server_default="unknown"),
        )
        op.create_check_constraint(
            f"ck_{table}_quality_status",
            table,
            "quality_status IN ('unknown', 'verified', 'provisional', 'rejected')",
        )

    # Create index on is_synthetic for fast filtering of real vs synthetic data
    for table in ("price_ohlcv", "index_ohlcv"):
        op.create_index(f"ix_{table}_is_synthetic", table, ["is_synthetic"])


def downgrade() -> None:
    for table in ("price_ohlcv", "index_ohlcv"):
        op.drop_index(f"ix_{table}_is_synthetic", table_name=table)
        op.drop_constraint(f"ck_{table}_quality_status", table, type_="check")
        op.drop_column(table, "quality_status")
        op.drop_column(table, "is_synthetic")
