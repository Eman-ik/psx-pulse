"""Tests for Step 18: EvidenceCitationService."""

import pytest
from app.services.evidence_citation_service import (
    EvidenceCitationService,
    Citation,
    SourceType,
    SourceTier,
)


@pytest.fixture
def citation_service():
    """Create citation service instance."""
    return EvidenceCitationService()


@pytest.fixture
def sample_citations():
    """Create sample citations."""
    return [
        Citation(
            claim="Revenue grew 15% YoY",
            source_type=SourceType.FILING,
            source_tier=SourceTier.PRIMARY,
            source_name="Annual Report 2024",
            source_date="2024-06-30",
            data_point="net_revenue:growth",
            confidence=95.0,
            supporting_value=15.0,
        ),
        Citation(
            claim="P/E ratio is 12.5x",
            source_type=SourceType.MARKET_DATA,
            source_tier=SourceTier.SECONDARY,
            source_name="PSX API",
            source_date="2024-10-02",
            data_point="pe_ratio:current",
            confidence=90.0,
            supporting_value=12.5,
        ),
        Citation(
            claim="ROE improved 200bps",
            source_type=SourceType.DERIVED,
            source_tier=SourceTier.DERIVED_CALC,
            source_name="Financial Calculation",
            source_date="2024-10-02",
            data_point="roe:change",
            confidence=85.0,
            supporting_value=2.0,
        ),
    ]


def test_citation_creation():
    """Test creating a citation."""
    citation = Citation(
        claim="Revenue grew 20%",
        source_type=SourceType.FILING,
        source_tier=SourceTier.PRIMARY,
        source_name="Annual Report 2024",
        source_date="2024-06-30",
        data_point="net_revenue",
        confidence=95.0,
    )

    assert citation.claim == "Revenue grew 20%"
    assert citation.source_type == SourceType.FILING
    assert citation.confidence == 95.0


def test_citation_to_dict(sample_citations):
    """Test citation dictionary conversion."""
    citation = sample_citations[0]
    citation_dict = citation.to_dict()

    assert "claim" in citation_dict
    assert "source_type" in citation_dict
    assert "source_tier" in citation_dict
    assert citation_dict["source_name"] == "Annual Report 2024"
    assert citation_dict["confidence"] == 95.0


def test_create_analysis_with_citations(citation_service, sample_citations):
    """Test creating analysis with multiple citations."""
    analysis = citation_service.create_analysis_with_citations(
        ticker="APTX",
        analysis_id="analysis_001",
        analysis_type="deep",
        thesis="Strong buy due to revenue growth",
        citations=sample_citations,
    )

    assert analysis.ticker == "APTX"
    assert analysis.analysis_id == "analysis_001"
    assert len(analysis.citations) == 3
    assert "Annual Report 2024" in analysis.source_breakdown
    assert analysis.average_confidence > 85


def test_source_breakdown(citation_service, sample_citations):
    """Test source breakdown calculation."""
    analysis = citation_service.create_analysis_with_citations(
        ticker="APTX",
        analysis_id="analysis_001",
        analysis_type="deep",
        thesis="Test thesis",
        citations=sample_citations,
    )

    assert len(analysis.source_breakdown) == 3
    assert analysis.source_breakdown["Annual Report 2024"] == 1
    assert analysis.source_breakdown["PSX API"] == 1


def test_average_confidence_calculation(citation_service, sample_citations):
    """Test average confidence calculation."""
    analysis = citation_service.create_analysis_with_citations(
        ticker="APTX",
        analysis_id="analysis_001",
        analysis_type="deep",
        thesis="Test thesis",
        citations=sample_citations,
    )

    # (95 + 90 + 85) / 3 = 90
    assert analysis.average_confidence == 90.0


def test_add_citation(citation_service, sample_citations):
    """Test adding citation to existing analysis."""
    analysis = citation_service.create_analysis_with_citations(
        ticker="APTX",
        analysis_id="analysis_001",
        analysis_type="deep",
        thesis="Test thesis",
        citations=sample_citations[:1],
    )

    original_count = len(analysis.citations)

    analysis = citation_service.add_citation(
        analysis,
        claim="New claim",
        source_type=SourceType.ANNOUNCEMENT,
        source_tier=SourceTier.SECONDARY,
        source_name="Company Announcement",
        data_point="announcement:dividend",
        confidence=80.0,
    )

    assert len(analysis.citations) == original_count + 1
    assert "Company Announcement" in analysis.source_breakdown


def test_get_citations_by_source(citation_service, sample_citations):
    """Test filtering citations by source."""
    analysis = citation_service.create_analysis_with_citations(
        ticker="APTX",
        analysis_id="analysis_001",
        analysis_type="deep",
        thesis="Test thesis",
        citations=sample_citations,
    )

    filing_cites = citation_service.get_citations_by_source(
        analysis, "Annual Report 2024"
    )

    assert len(filing_cites) == 1
    assert filing_cites[0].claim == "Revenue grew 15% YoY"


def test_get_citations_by_type(citation_service, sample_citations):
    """Test filtering citations by source type."""
    analysis = citation_service.create_analysis_with_citations(
        ticker="APTX",
        analysis_id="analysis_001",
        analysis_type="deep",
        thesis="Test thesis",
        citations=sample_citations,
    )

    filing_cites = citation_service.get_citations_by_type(
        analysis, SourceType.FILING
    )

    assert len(filing_cites) == 1
    assert filing_cites[0].source_type == SourceType.FILING


def test_get_weak_citations(citation_service):
    """Test finding weak citations below confidence threshold."""
    citations = [
        Citation(
            claim="Claim 1",
            source_type=SourceType.FILING,
            source_tier=SourceTier.PRIMARY,
            source_name="Source 1",
            data_point="dp1",
            confidence=95.0,
            source_date=None,
        ),
        Citation(
            claim="Claim 2",
            source_type=SourceType.FILING,
            source_tier=SourceTier.PRIMARY,
            source_name="Source 2",
            data_point="dp2",
            confidence=65.0,  # Below 70 threshold
            source_date=None,
        ),
    ]

    analysis = citation_service.create_analysis_with_citations(
        ticker="APTX",
        analysis_id="analysis_001",
        analysis_type="deep",
        thesis="Test thesis",
        citations=citations,
    )

    weak = citation_service.get_weak_citations(analysis, confidence_threshold=70.0)

    assert len(weak) == 1
    assert weak[0].confidence == 65.0


def test_audit_sources(citation_service, sample_citations):
    """Test source audit report generation."""
    analysis = citation_service.create_analysis_with_citations(
        ticker="APTX",
        analysis_id="analysis_001",
        analysis_type="deep",
        thesis="Test thesis",
        citations=sample_citations,
    )

    audit = citation_service.audit_sources(analysis)

    assert audit["ticker"] == "APTX"
    assert audit["total_citations"] == 3
    assert audit["unique_sources"] == 3
    assert "sources" in audit
    assert "source_types" in audit
    assert "source_tiers" in audit


def test_analysis_to_dict(citation_service, sample_citations):
    """Test analysis dictionary conversion."""
    analysis = citation_service.create_analysis_with_citations(
        ticker="APTX",
        analysis_id="analysis_001",
        analysis_type="deep",
        thesis="Test thesis",
        citations=sample_citations,
    )

    analysis_dict = analysis.to_dict()

    assert analysis_dict["ticker"] == "APTX"
    assert analysis_dict["analysis_id"] == "analysis_001"
    assert analysis_dict["citation_count"] == 3
    assert "citations" in analysis_dict


def test_empty_analysis(citation_service):
    """Test creating analysis with no citations."""
    analysis = citation_service.create_analysis_with_citations(
        ticker="APTX",
        analysis_id="analysis_001",
        analysis_type="quick",
        thesis="Quick analysis",
        citations=[],
    )

    assert len(analysis.citations) == 0
    assert analysis.average_confidence == 50.0  # Default


def test_citation_with_supporting_value():
    """Test citation with supporting numeric value."""
    citation = Citation(
        claim="Revenue is 500M",
        source_type=SourceType.FILING,
        source_tier=SourceTier.PRIMARY,
        source_name="Annual Report",
        data_point="net_revenue",
        confidence=95.0,
        source_date=None,
        supporting_value=500.0,
    )

    assert citation.supporting_value == 500.0
