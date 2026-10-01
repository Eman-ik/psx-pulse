from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    document_type = Column(String(100))
    period_id = Column(Integer, ForeignKey("periods.id"), nullable=True)
    file_path = Column(String(500))  # s3://bucket/company/year/document.pdf
    file_size = Column(Integer)
    file_hash = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source = relationship("Source", back_populates="documents")
    company = relationship("Company", back_populates="documents")
