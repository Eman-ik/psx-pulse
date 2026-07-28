"""add momentum and risk score to signal_score

Revision ID: dd1df325c5a4
Revises: 0719cce11289
Create Date: 2026-07-28 09:37:23.231151

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd1df325c5a4'
down_revision: Union[str, None] = '0719cce11289'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('signal_score', sa.Column('momentum_score', sa.Numeric(5, 2), nullable=True))
    op.add_column('signal_score', sa.Column('risk_score', sa.Numeric(5, 2), nullable=True))
    op.alter_column('signal_score', 'quality_score', existing_type=sa.Numeric(5, 2), nullable=True)
    op.alter_column('signal_score', 'growth_score', existing_type=sa.Numeric(5, 2), nullable=True)
    op.alter_column('signal_score', 'financial_health_score', existing_type=sa.Numeric(5, 2), nullable=True)
    op.alter_column('signal_score', 'valuation_score', existing_type=sa.Numeric(5, 2), nullable=True)
    op.alter_column('signal_score', 'catalyst_risk_score', existing_type=sa.Numeric(5, 2), nullable=True)


def downgrade() -> None:
    # Backfill any NULLs before re-adding the NOT NULL constraint -- these 5 columns predate
    # this migration and were never nullable, so downgrading must restore that invariant.
    op.execute("UPDATE signal_score SET quality_score = 0.0 WHERE quality_score IS NULL")
    op.execute("UPDATE signal_score SET growth_score = 0.0 WHERE growth_score IS NULL")
    op.execute("UPDATE signal_score SET financial_health_score = 0.0 WHERE financial_health_score IS NULL")
    op.execute("UPDATE signal_score SET valuation_score = 0.0 WHERE valuation_score IS NULL")
    op.execute("UPDATE signal_score SET catalyst_risk_score = 0.0 WHERE catalyst_risk_score IS NULL")
    op.alter_column('signal_score', 'catalyst_risk_score', existing_type=sa.Numeric(5, 2), nullable=False)
    op.alter_column('signal_score', 'valuation_score', existing_type=sa.Numeric(5, 2), nullable=False)
    op.alter_column('signal_score', 'financial_health_score', existing_type=sa.Numeric(5, 2), nullable=False)
    op.alter_column('signal_score', 'growth_score', existing_type=sa.Numeric(5, 2), nullable=False)
    op.alter_column('signal_score', 'quality_score', existing_type=sa.Numeric(5, 2), nullable=False)
    op.drop_column('signal_score', 'risk_score')
    op.drop_column('signal_score', 'momentum_score')
