from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class ResearchInsight(Base):
    __tablename__ = "research_insights"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=False)
    insight_type = Column(String(50))  # anomaly, trend, flag, etc
    severity = Column(String(20))  # low, medium, high
    category = Column(String(50))  # growth, profitability, leverage, etc
    claim = Column(Text)
    explanation = Column(Text)
    supporting_fact_ids = Column(JSON)
    supporting_source_ids = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="research_insights")
    period = relationship("Period", back_populates="research_insights")
