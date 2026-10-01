"""Sprint 1: Add core data foundation models

Revision ID: 23093aff0f19
Revises: 
Create Date: 2026-10-01 18:36:26.685648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23093aff0f19'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(10), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('sector', sa.String(100), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('listed_date', sa.DateTime(), nullable=True),
        sa.Column('fiscal_year_end', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='PKR'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('coverage_tier', sa.String(20), nullable=False, server_default='price_only'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticker'),
    )
    op.create_index(op.f('ix_companies_id'), 'companies', ['id'], unique=False)
    op.create_index(op.f('ix_companies_ticker'), 'companies', ['ticker'], unique=False)

    # Create periods table
    op.create_table(
        'periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('quarter', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'period_type', 'fiscal_year', 'quarter', name='uq_company_period'),
    )
    op.create_index(op.f('ix_periods_id'), 'periods', ['id'], unique=False)

    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('publisher', sa.String(255), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('document_type', sa.String(100), nullable=True),
        sa.Column('period_id', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(2000), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('document_date', sa.Date(), nullable=True),
        sa.Column('publication_date', sa.Date(), nullable=True),
        sa.Column('retrieved_date', sa.Date(), nullable=True),
        sa.Column('document_hash', sa.String(64), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['period_id'], ['periods.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sources_id'), 'sources', ['id'], unique=False)

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(100), nullable=True),
        sa.Column('period_id', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['period_id'], ['periods.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)

    # Create financial_facts table
    op.create_table(
        'financial_facts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('metric', sa.String(100), nullable=False),
        sa.Column('value', sa.Numeric(15, 2), nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='PKR'),
        sa.Column('statement_type', sa.String(50), nullable=True),
        sa.Column('consolidation_type', sa.String(50), nullable=False, server_default='consolidated'),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('source_page', sa.Integer(), nullable=True),
        sa.Column('extraction_method', sa.String(50), nullable=False, server_default='manual'),
        sa.Column('validation_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('validation_notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['period_id'], ['periods.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'period_id', 'metric', 'consolidation_type', name='uq_company_period_metric'),
    )
    op.create_index(op.f('ix_financial_facts_id'), 'financial_facts', ['id'], unique=False)
    op.create_index(op.f('ix_financial_facts_source_id'), 'financial_facts', ['source_id'], unique=False)

    # Create derived_metrics table
    op.create_table(
        'derived_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('value', sa.Numeric(15, 4), nullable=True),
        sa.Column('formula_version', sa.String(20), nullable=False, server_default='1.0'),
        sa.Column('source_fact_ids', sa.JSON(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['period_id'], ['periods.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_derived_metrics_id'), 'derived_metrics', ['id'], unique=False)

    # Create research_insights table
    op.create_table(
        'research_insights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('insight_type', sa.String(50), nullable=True),
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('claim', sa.Text(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('supporting_fact_ids', sa.JSON(), nullable=True),
        sa.Column('supporting_source_ids', sa.JSON(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['period_id'], ['periods.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_research_insights_id'), 'research_insights', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_research_insights_id'), table_name='research_insights')
    op.drop_table('research_insights')
    op.drop_index(op.f('ix_derived_metrics_id'), table_name='derived_metrics')
    op.drop_table('derived_metrics')
    op.drop_index(op.f('ix_financial_facts_source_id'), table_name='financial_facts')
    op.drop_index(op.f('ix_financial_facts_id'), table_name='financial_facts')
    op.drop_table('financial_facts')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_table('documents')
    op.drop_index(op.f('ix_sources_id'), table_name='sources')
    op.drop_table('sources')
    op.drop_index(op.f('ix_periods_id'), table_name='periods')
    op.drop_table('periods')
    op.drop_index(op.f('ix_companies_ticker'), table_name='companies')
    op.drop_index(op.f('ix_companies_id'), table_name='companies')
    op.drop_table('companies')
