from datetime import datetime, date
from sqlalchemy import CheckConstraint, Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (CheckConstraint("url IS NOT NULL OR file_path IS NOT NULL", name="ck_sources_locator"),)

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    source_type = Column(String(50), nullable=False)  # annual_report, quarterly_results, announcement, etc
    publisher = Column(String(255))
    title = Column(String(500))
    document_type = Column(String(100))  # annual_report, financial_statements, etc
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=True)
    url = Column(String(2000))
    file_path = Column(String(500))  # Local path to document
    document_date = Column(Date)
    publication_date = Column(Date)
    retrieved_date = Column(Date)
    document_hash = Column(String(64))  # SHA256 for reproducibility
    status = Column(String(20), default="pending")  # pending, extracted, validated, stored
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="sources")
    documents = relationship("Document", back_populates="source", cascade="all, delete-orphan")
    financial_facts = relationship("app.models.financial_fact.FinancialFact", back_populates="source", cascade="all, delete-orphan")
