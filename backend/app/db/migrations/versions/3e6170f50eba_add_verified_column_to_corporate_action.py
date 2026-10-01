"""add verified column to corporate_action

Revision ID: 3e6170f50eba
Revises: 048788e792ac
Create Date: 2026-08-25 13:05:02.386642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e6170f50eba'
down_revision: Union[str, None] = '048788e792ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Autogenerate also picked up an unrelated pre-existing analyst_packet index/constraint
    # drift (same class of thing stripped from 048788e792ac) -- not part of this change,
    # left alone here too.
    op.add_column('corporate_action', sa.Column('verified', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    op.drop_column('corporate_action', 'verified')
