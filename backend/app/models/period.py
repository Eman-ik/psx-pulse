from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class Period(Base):
    __tablename__ = "periods"
    __table_args__ = (
        UniqueConstraint("company_id", "period_type", "fiscal_year", "quarter", name="uq_company_period"),
    )

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period_type = Column(String(20), nullable=False)  # annual, q1, q2, q3, q4, h1, h2
    fiscal_year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=True)  # 1-4 if quarterly
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="periods")
    financial_facts = relationship("app.models.financial_fact.FinancialFact", back_populates="period", cascade="all, delete-orphan")
    derived_metrics = relationship("DerivedMetric", back_populates="period", cascade="all, delete-orphan")
    research_insights = relationship("ResearchInsight", back_populates="period", cascade="all, delete-orphan")
