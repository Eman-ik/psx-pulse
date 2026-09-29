"""
Research Studio (R1-R8)
Data-first financial research platform for PSX

Modules:
- R1: Company Master & Registry
- R2: Document Warehouse & Filing System
- R3: Financial Statement Parser & Normalizer
- R4: Metrics & KPI Engine
- R5: Valuation & Peer Comparison Engine
- R6: Announcement Intelligence Engine
- R7: AI Research Copilot
- R8: Research Workspace UI
"""

from .models import (
    Base,
    Sector,
    Company,
    Document,
    DocumentSource,
    FinancialStatement,
    StatementLineItem,
    MetricDefinition,
    FinancialMetric,
    StockPrice,
    Valuation,
    Announcement,
    CorporateEvent,
    ResearchSession,
    AIResponse,
    DataLineage,
)

__version__ = "0.1.0"
__all__ = [
    "Base",
    "Sector",
    "Company",
    "Document",
    "DocumentSource",
    "FinancialStatement",
    "StatementLineItem",
    "MetricDefinition",
    "FinancialMetric",
    "StockPrice",
    "Valuation",
    "Announcement",
    "CorporateEvent",
    "ResearchSession",
    "AIResponse",
    "DataLineage",
]
