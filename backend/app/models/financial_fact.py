from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class FinancialFact(Base):
    __tablename__ = "financial_facts"
    __table_args__ = (
        UniqueConstraint("company_id", "period_id", "metric", "consolidation_type", name="uq_company_period_metric"),
    )

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=False)
    metric = Column(String(100), nullable=False)  # revenue, net_income, eps, etc
    value = Column(Numeric(15, 2), nullable=False)
    unit = Column(String(50))  # PKR, shares, %, etc
    currency = Column(String(3), default="PKR")
    statement_type = Column(String(50))  # income_statement, balance_sheet, cashflow, etc
    consolidation_type = Column(String(50), default="consolidated")  # consolidated, unconsolidated
    source_id = Column(Integer, ForeignKey("sources.id"))
    source_page = Column(Integer)
    extraction_method = Column(String(50), default="manual")  # manual, ocr, structured
    validation_status = Column(String(20), default="pending")  # pending, validated, flagged, rejected
    validation_notes = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="financial_facts")
    period = relationship("Period", back_populates="financial_facts")
    source = relationship("Source", back_populates="financial_facts")
