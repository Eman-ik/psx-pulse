from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class DerivedMetric(Base):
    __tablename__ = "derived_metrics"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)  # roe, fcf, debt_equity, etc
    value = Column(Numeric(15, 4))
    formula_version = Column(String(20), default="1.0")
    source_fact_ids = Column(JSON)  # Array of financial_fact IDs used in calculation
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="derived_metrics")
    period = relationship("Period", back_populates="derived_metrics")
