"""add analyst_run and analyst_packet tables

Revision ID: c8f2a1d5e9b3
Revises: dd1df325c5a4
Create Date: 2026-07-31 12:00:00.000000

Adds the analyst_run and analyst_packet tables for the PSX Senior Analyst Agent
(Blueprint Section 13.3). analyst_run tracks invocation lifecycle (pending →
running → complete/failed/blocked). analyst_packet stores the full PSXAnalystPacket
JSON plus key scalar fields for fast filtering.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c8f2a1d5e9b3"
down_revision: Union[str, None] = "dd1df325c5a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analyst_run",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issuer_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("prompt_version", sa.String(length=40), nullable=False, server_default="psx-analyst-v1"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["issuer_id"], ["issuer.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analyst_run_issuer_id", "analyst_run", ["issuer_id"])

    op.create_table(
        "analyst_packet",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("analyst_run_id", sa.Integer(), nullable=False),
        sa.Column("issuer_id", sa.Integer(), nullable=False),
        sa.Column("research_posture", sa.String(length=30), nullable=False),
        sa.Column("business_health", sa.String(length=40), nullable=False),
        sa.Column("confidence", sa.String(length=10), nullable=False),
        sa.Column("one_sentence_view", sa.String(length=500), nullable=True),
        sa.Column("decision_hinge", sa.String(length=500), nullable=True),
        sa.Column("packet_json", sa.JSON(), nullable=False),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["analyst_run_id"], ["analyst_run.id"]),
        sa.ForeignKeyConstraint(["issuer_id"], ["issuer.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analyst_run_id"),
    )
    op.create_index("ix_analyst_packet_analyst_run_id", "analyst_packet", ["analyst_run_id"])
    op.create_index("ix_analyst_packet_issuer_id", "analyst_packet", ["issuer_id"])


def downgrade() -> None:
    op.drop_index("ix_analyst_packet_issuer_id", table_name="analyst_packet")
    op.drop_index("ix_analyst_packet_analyst_run_id", table_name="analyst_packet")
    op.drop_table("analyst_packet")
    op.drop_index("ix_analyst_run_issuer_id", table_name="analyst_run")
    op.drop_table("analyst_run")
