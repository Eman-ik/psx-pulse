"""add significance test fields to ml_signal_score

Revision ID: bb9a354d1c69
Revises: 49473b019419
Create Date: 2026-08-27 13:09:48.482518

Closes a real parity gap with Kronos's own gate (signal_qualification.py): this model had
no significance test at all before this, only the accuracy floor and beats_naive_baseline.
validation_p_value is Float, not Numeric(6,4) like the other metrics -- this model's
buy-confident subset can be tens of thousands of rows, where a genuinely significant result
can be many orders of magnitude smaller than 0.0001, and a fixed 4-decimal column would
silently round it to 0.0000. See app/etl/ml_signal_engine.py's validation_metrics().

Existing rows predate this check and default to significant_at_10pct=False
(validation_p_value NULL) -- correctly conservative, same reasoning as the
beats_naive_baseline migration before this one: a row computed before this gate existed was
never actually checked against it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb9a354d1c69'
down_revision: Union[str, None] = '49473b019419'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ml_signal_score', sa.Column('validation_p_value', sa.Float(), nullable=True))
    op.add_column('ml_signal_score', sa.Column('significant_at_10pct', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('ml_signal_score', 'significant_at_10pct')
    op.drop_column('ml_signal_score', 'validation_p_value')
