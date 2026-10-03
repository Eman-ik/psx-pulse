"""Step 18: Evidence Citation Service — Track sources for analysis claims.

Maintains citation chain for all analysis:
- Links analysis claims to source data
- Tracks data point origin (filing, market data, etc.)
- Confidence scoring based on source quality
- Source breakdown for evidence audit trail

Input: Analysis results + source data
Output: AnalysisWithCitations (claims linked to sources)
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class SourceType(str, Enum):
    """Types of data sources."""

    FILING = "Filing"
    MARKET_DATA = "Market Data"
    FINANCIAL_METRIC = "Financial Metric"
    TECHNICAL_ANALYSIS = "Technical Analysis"
    ANNOUNCEMENT = "Announcement"
    DERIVED = "Derived"
    LLM_INFERENCE = "LLM Inference"


class SourceTier(str, Enum):
    """Source reliability tiers."""

    PRIMARY = "Primary"  # Official filings, regulatory data
    SECONDARY = "Secondary"  # Market data, news
    DERIVED_CALC = "Derived Calculation"  # Calculated from primary
    INFERENCE = "Inference"  # LLM-inferred


@dataclass
class Citation:
    """Single citation linking claim to source."""

    claim: str  # e.g., "Revenue grew 20% YoY"
    source_type: SourceType
    source_tier: SourceTier
    source_name: str  # e.g., "Annual Report 2024", "PSX API"
    data_point: str  # e.g., "net_revenue:2024_vs_2023"
    confidence: float  # 0-100%
    source_date: Optional[str] = None  # e.g., "2024-06-30"
    supporting_value: Optional[Any] = None  # Actual value from source

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "claim": self.claim,
            "source_type": self.source_type.value,
            "source_tier": self.source_tier.value,
            "source_name": self.source_name,
            "source_date": self.source_date,
            "data_point": self.data_point,
            "confidence": round(self.confidence, 1),
        }


@dataclass
class AnalysisWithCitations:
    """Analysis result with source citations."""

    ticker: str
    analysis_id: str  # Unique identifier for this analysis
    analysis_type: str  # "quick", "deep", "forecast"
    thesis: str  # Main investment thesis

    citations: List[Citation] = field(default_factory=list)
    source_breakdown: Dict[str, int] = field(default_factory=dict)  # source_name -> count
    average_confidence: float = 50.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "analysis_id": self.analysis_id,
            "analysis_type": self.analysis_type,
            "citation_count": len(self.citations),
            "unique_sources": len(self.source_breakdown),
            "average_confidence": round(self.average_confidence, 1),
            "source_breakdown": self.source_breakdown,
            "citations": [c.to_dict() for c in self.citations],
        }


class EvidenceCitationService:
    """Tracks and manages citations for analysis claims."""

    def __init__(self):
        """Initialize citation service."""
        self.logger = logging.getLogger(__name__)

    def create_analysis_with_citations(
        self,
        ticker: str,
        analysis_id: str,
        analysis_type: str,
        thesis: str,
        citations: List[Citation],
    ) -> AnalysisWithCitations:
        """Create analysis result with citations.

        Args:
            ticker: Company ticker
            analysis_id: Unique analysis identifier
            analysis_type: Type of analysis (quick, deep, forecast)
            thesis: Main investment thesis
            citations: List of citations supporting the thesis

        Returns:
            AnalysisWithCitations with source breakdown
        """
        try:
            # Build source breakdown
            source_breakdown = self._build_source_breakdown(citations)

            # Calculate average confidence
            avg_confidence = self._calculate_average_confidence(citations)

            analysis = AnalysisWithCitations(
                ticker=ticker,
                analysis_id=analysis_id,
                analysis_type=analysis_type,
                thesis=thesis,
                citations=citations,
                source_breakdown=source_breakdown,
                average_confidence=avg_confidence,
            )

            self.logger.info(
                f"Created analysis {analysis_id} for {ticker} with {len(citations)} "
                f"citations from {len(source_breakdown)} sources (confidence: {avg_confidence:.0f}%)"
            )
            return analysis

        except Exception as e:
            self.logger.error(f"Error creating analysis with citations: {e}")
            return AnalysisWithCitations(
                ticker=ticker,
                analysis_id=analysis_id,
                analysis_type=analysis_type,
                thesis=thesis,
            )

    def add_citation(
        self,
        analysis: AnalysisWithCitations,
        claim: str,
        source_type: SourceType,
        source_tier: SourceTier,
        source_name: str,
        data_point: str,
        confidence: float,
        source_date: Optional[str] = None,
        supporting_value: Optional[Any] = None,
    ) -> AnalysisWithCitations:
        """Add a citation to existing analysis.

        Args:
            analysis: Existing analysis to add citation to
            claim: The claim being cited
            source_type: Type of source (Filing, Market Data, etc.)
            source_tier: Reliability tier (Primary, Secondary, etc.)
            source_name: Name of specific source (e.g., "Q2 2024 Report")
            data_point: Data point identifier
            confidence: Confidence score (0-100%)
            source_date: Optional date of source
            supporting_value: Optional actual value from source

        Returns:
            Updated AnalysisWithCitations
        """
        citation = Citation(
            claim=claim,
            source_type=source_type,
            source_tier=source_tier,
            source_name=source_name,
            source_date=source_date,
            data_point=data_point,
            confidence=confidence,
            supporting_value=supporting_value,
        )

        analysis.citations.append(citation)
        analysis.source_breakdown = self._build_source_breakdown(analysis.citations)
        analysis.average_confidence = self._calculate_average_confidence(analysis.citations)

        return analysis

    def get_citations_by_source(
        self,
        analysis: AnalysisWithCitations,
        source_name: str,
    ) -> List[Citation]:
        """Get all citations from a specific source."""
        return [c for c in analysis.citations if c.source_name == source_name]

    def get_citations_by_type(
        self,
        analysis: AnalysisWithCitations,
        source_type: SourceType,
    ) -> List[Citation]:
        """Get all citations of a specific type."""
        return [c for c in analysis.citations if c.source_type == source_type]

    def get_citations_by_tier(
        self,
        analysis: AnalysisWithCitations,
        source_tier: SourceTier,
    ) -> List[Citation]:
        """Get all citations from specific tier."""
        return [c for c in analysis.citations if c.source_tier == source_tier]

    def get_weak_citations(
        self,
        analysis: AnalysisWithCitations,
        confidence_threshold: float = 70.0,
    ) -> List[Citation]:
        """Get citations below confidence threshold."""
        return [c for c in analysis.citations if c.confidence < confidence_threshold]

    def audit_sources(
        self,
        analysis: AnalysisWithCitations,
    ) -> Dict[str, Any]:
        """Generate source audit report."""
        return {
            "ticker": analysis.ticker,
            "total_citations": len(analysis.citations),
            "unique_sources": len(analysis.source_breakdown),
            "sources": analysis.source_breakdown,
            "source_types": self._count_by_type(analysis.citations),
            "source_tiers": self._count_by_tier(analysis.citations),
            "average_confidence": analysis.average_confidence,
            "weak_citations": len(self.get_weak_citations(analysis)),
        }

    @staticmethod
    def _build_source_breakdown(citations: List[Citation]) -> Dict[str, int]:
        """Count citations per source."""
        breakdown = {}
        for citation in citations:
            breakdown[citation.source_name] = breakdown.get(citation.source_name, 0) + 1
        return breakdown

    @staticmethod
    def _calculate_average_confidence(citations: List[Citation]) -> float:
        """Calculate average confidence across citations."""
        if not citations:
            return 50.0
        return sum(c.confidence for c in citations) / len(citations)

    @staticmethod
    def _count_by_type(citations: List[Citation]) -> Dict[str, int]:
        """Count citations by source type."""
        counts = {}
        for citation in citations:
            source_type = citation.source_type.value
            counts[source_type] = counts.get(source_type, 0) + 1
        return counts

    @staticmethod
    def _count_by_tier(citations: List[Citation]) -> Dict[str, int]:
        """Count citations by source tier."""
        counts = {}
        for citation in citations:
            source_tier = citation.source_tier.value
            counts[source_tier] = counts.get(source_tier, 0) + 1
        return counts
