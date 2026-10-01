"""add naive baseline fields to ml_signal_score

Revision ID: 49473b019419
Revises: 3e6170f50eba
Create Date: 2026-08-27 10:41:07.414813

validation_positive_rate + beats_naive_baseline close the same gate gap
signal_qualification.py's beats_naive_baseline already closed for Kronos: a fixed
validation_buy_precision floor (ModelConfig.minimum_validated_accuracy) means
nothing if the pooled walk-forward population's own base rate already clears it.
See app/etl/ml_signal_engine.py's validation_metrics() and app/db/models/scoring.py.

Existing rows predate this check and default to beats_naive_baseline=False
(validation_positive_rate NULL, unknown) -- correctly conservative: a row computed
before this gate existed was never actually checked against it, so it must not be
read as having passed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49473b019419'
down_revision: Union[str, None] = '3e6170f50eba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ml_signal_score', sa.Column('validation_positive_rate', sa.Numeric(precision=6, scale=4), nullable=True))
    op.add_column('ml_signal_score', sa.Column('beats_naive_baseline', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('ml_signal_score', 'beats_naive_baseline')
    op.drop_column('ml_signal_score', 'validation_positive_rate')
