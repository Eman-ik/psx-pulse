from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    listed_date = Column(DateTime)
    fiscal_year_end = Column(Integer)  # Month (1-12)
    currency = Column(String(3), default="PKR")
    status = Column(String(20), default="active")  # active, delisted, suspended
    coverage_tier = Column(String(20), default="price_only")  # price_only, partial, full
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    periods = relationship("Period", back_populates="company", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="company", cascade="all, delete-orphan")
    financial_facts = relationship("FinancialFact", back_populates="company", cascade="all, delete-orphan")
    derived_metrics = relationship("DerivedMetric", back_populates="company", cascade="all, delete-orphan")
    research_insights = relationship("ResearchInsight", back_populates="company", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")
