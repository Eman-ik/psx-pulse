"""add Stage 2 industry observations and assessments

Revision ID: f1a2b3c4d5e6
Revises: bb9a354d1c69
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "bb9a354d1c69"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "industry_observation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sector_id", sa.Integer(), nullable=False),
        sa.Column("company_issuer_id", sa.Integer(), nullable=True),
        sa.Column("metric_key", sa.String(length=60), nullable=False),
        sa.Column("product", sa.String(length=50), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("value", sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_issuer_id"], ["issuer.id"]),
        sa.ForeignKeyConstraint(["sector_id"], ["sector.id"]),
        sa.ForeignKeyConstraint(["source_document_id"], ["source_document.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sector_id", "metric_key", "company_issuer_id", "product", "period_end", name="uq_industry_observation_dimension_period"),
    )
    for column in ("sector_id", "company_issuer_id", "metric_key", "period_end", "source_document_id", "is_verified"):
        op.create_index(f"ix_industry_observation_{column}", "industry_observation", [column], unique=False)

    op.create_table(
        "industry_assessment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sector_id", sa.Integer(), nullable=False),
        sa.Column("dimension", sa.String(length=50), nullable=False),
        sa.Column("rating", sa.String(length=30), nullable=False),
        sa.Column("assessment", sa.Text(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("analyst", sa.String(length=120), nullable=False),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sector_id"], ["sector.id"]),
        sa.ForeignKeyConstraint(["source_document_id"], ["source_document.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sector_id", "dimension", "as_of_date", name="uq_industry_assessment_dimension_date"),
    )
    for column in ("sector_id", "dimension", "as_of_date", "source_document_id"):
        op.create_index(f"ix_industry_assessment_{column}", "industry_assessment", [column], unique=False)


def downgrade() -> None:
    op.drop_table("industry_assessment")
    op.drop_table("industry_observation")
