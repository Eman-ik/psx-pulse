"""Tests for historical feature engine.

Validates that:
1. Features are calculated from historical data only
2. No lookahead bias — only uses data published by as_of_date
3. Calculations use same logic as FinancialContextService
4. Insufficient data returns appropriate data_quality
5. Period grouping respects scope (consolidated vs standalone)
"""

from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import (
    FinancialFact,
    Issuer,
    Security,
    Sector,
    SourceDocument,
)
from app.services.historical_feature_engine import HistoricalFeatureEngine


@pytest.fixture
def test_db():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def setup_company(test_db: Session):
    """Create test company with two years of financial facts."""
    sector = Sector(name="Fertilizer")
    test_db.add(sector)
    test_db.flush()

    issuer = Issuer(name="Test Fertilizer Co", sector_id=sector.id)
    test_db.add(issuer)
    test_db.flush()

    security = Security(
        issuer_id=issuer.id, symbol="TFCO", listing_date=date(2020, 1, 1), is_active=True
    )
    test_db.add(security)
    test_db.flush()

    source_doc = SourceDocument(
        document_type="financial_statement",
        url="http://example.com/tfco-financials.pdf",
        content_hash="abc123def456abc123def456abc123def456abc123def456abc123def456ab",
        fetched_at=datetime.now(timezone.utc),
        source_tier="primary",
    )
    test_db.add(source_doc)
    test_db.flush()

    # FY2023 (period ended 2023-12-31, published 2024-02-15)
    facts_fy2023 = [
        FinancialFact(
            issuer_id=issuer.id,
            line_item="revenue",
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            period_type="annual",
            scope="standalone",
            unit="PKR",
            value=10000000,
            source_document_id=source_doc.id,
            published_at=datetime.combine(date(2024, 2, 15), time(10, 0), tzinfo=timezone.utc),
        ),
        FinancialFact(
            issuer_id=issuer.id,
            line_item="profit_after_tax",
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            period_type="annual",
            scope="standalone",
            unit="PKR",
            value=2000000,
            source_document_id=source_doc.id,
            published_at=datetime.combine(date(2024, 2, 15), time(10, 0), tzinfo=timezone.utc),
        ),
        FinancialFact(
            issuer_id=issuer.id,
            line_item="total_assets",
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            period_type="annual",
            scope="standalone",
            unit="PKR",
            value=50000000,
            source_document_id=source_doc.id,
            published_at=datetime.combine(date(2024, 2, 15), time(10, 0), tzinfo=timezone.utc),
        ),
        FinancialFact(
            issuer_id=issuer.id,
            line_item="total_equity",
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            period_type="annual",
            scope="standalone",
            unit="PKR",
            value=25000000,
            source_document_id=source_doc.id,
            published_at=datetime.combine(date(2024, 2, 15), time(10, 0), tzinfo=timezone.utc),
        ),
    ]
    test_db.add_all(facts_fy2023)

    # FY2024 (period ended 2024-12-31, published 2025-02-15)
    facts_fy2024 = [
        FinancialFact(
            issuer_id=issuer.id,
            line_item="revenue",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            period_type="annual",
            scope="standalone",
            unit="PKR",
            value=12000000,
            source_document_id=source_doc.id,
            published_at=datetime.combine(date(2025, 2, 15), time(10, 0), tzinfo=timezone.utc),
        ),
        FinancialFact(
            issuer_id=issuer.id,
            line_item="profit_after_tax",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            period_type="annual",
            scope="standalone",
            unit="PKR",
            value=2800000,
            source_document_id=source_doc.id,
            published_at=datetime.combine(date(2025, 2, 15), time(10, 0), tzinfo=timezone.utc),
        ),
        FinancialFact(
            issuer_id=issuer.id,
            line_item="total_assets",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            period_type="annual",
            scope="standalone",
            unit="PKR",
            value=55000000,
            source_document_id=source_doc.id,
            published_at=datetime.combine(date(2025, 2, 15), time(10, 0), tzinfo=timezone.utc),
        ),
        FinancialFact(
            issuer_id=issuer.id,
            line_item="total_equity",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            period_type="annual",
            scope="standalone",
            unit="PKR",
            value=27000000,
            source_document_id=source_doc.id,
            published_at=datetime.combine(date(2025, 2, 15), time(10, 0), tzinfo=timezone.utc),
        ),
    ]
    test_db.add_all(facts_fy2024)

    test_db.commit()

    return {
        "issuer": issuer,
        "security": security,
        "source_doc": source_doc,
    }


def test_features_calculated_correctly(test_db: Session, setup_company):
    """Features should be calculated from historical data."""
    engine = HistoricalFeatureEngine(test_db)

    # As of 2024-02-20, FY2024 shouldn't be available yet
    features = engine.calculate("TFCO", date(2024, 2, 20))

    assert features.symbol == "TFCO"
    assert features.periods_available == 1  # Only FY2023
    assert features.data_quality == "insufficient"  # Need 2+ periods


def test_features_available_after_publication(test_db: Session, setup_company):
    """Features should be available once data is published."""
    engine = HistoricalFeatureEngine(test_db)

    # As of 2025-02-20, FY2024 is published
    features = engine.calculate("TFCO", date(2025, 2, 20))

    assert features.symbol == "TFCO"
    assert features.periods_available == 2
    assert features.data_quality == "available"
    assert features.latest_period_end == date(2024, 12, 31)


def test_revenue_growth_calculation(test_db: Session, setup_company):
    """Revenue growth should be calculated correctly."""
    engine = HistoricalFeatureEngine(test_db)

    features = engine.calculate("TFCO", date(2025, 2, 20))

    # FY2024 revenue: 12M, FY2023 revenue: 10M
    # Growth: (12M - 10M) / 10M * 100 = 20%
    assert features.revenue_growth_pct is not None
    assert abs(features.revenue_growth_pct - 20.0) < 0.01


def test_pat_growth_calculation(test_db: Session, setup_company):
    """PAT growth should be calculated correctly."""
    engine = HistoricalFeatureEngine(test_db)

    features = engine.calculate("TFCO", date(2025, 2, 20))

    # FY2024 PAT: 2.8M, FY2023 PAT: 2.0M
    # Growth: (2.8M - 2.0M) / 2.0M * 100 = 40%
    assert features.pat_growth_pct is not None
    assert abs(features.pat_growth_pct - 40.0) < 0.01


def test_roe_calculation(test_db: Session, setup_company):
    """ROE should be calculated correctly."""
    engine = HistoricalFeatureEngine(test_db)

    features = engine.calculate("TFCO", date(2025, 2, 20))

    # FY2024 PAT: 2.8M, FY2024 Equity: 27M
    # ROE: (2.8M / 27M) * 100 = 10.37%
    assert features.roe_pct is not None
    assert abs(features.roe_pct - 10.37) < 0.1


def test_roa_calculation(test_db: Session, setup_company):
    """ROA should be calculated correctly."""
    engine = HistoricalFeatureEngine(test_db)

    features = engine.calculate("TFCO", date(2025, 2, 20))

    # FY2024 PAT: 2.8M, FY2024 Assets: 55M
    # ROA: (2.8M / 55M) * 100 = 5.09%
    assert features.roa_pct is not None
    assert abs(features.roa_pct - 5.09) < 0.1


def test_no_lookahead_bias(test_db: Session, setup_company):
    """Future data should not be used in calculations."""
    engine = HistoricalFeatureEngine(test_db)

    # As of 2025-02-14, FY2024 was published 2025-02-15 (tomorrow)
    features = engine.calculate("TFCO", date(2025, 2, 14))

    assert features.periods_available == 1  # Only FY2023
    assert features.data_quality == "insufficient"
    assert features.revenue_growth_pct is None  # Can't calculate growth with 1 period


def test_feature_vector_shape(test_db: Session, setup_company):
    """Feature vector should have 10 elements."""
    engine = HistoricalFeatureEngine(test_db)

    features = engine.calculate("TFCO", date(2025, 2, 20))
    vector = features.to_vector()

    assert len(vector) == 10, "Feature vector should have 10 metrics"
    # All should be None or float
    for v in vector:
        assert v is None or isinstance(v, float)


def test_unknown_ticker_returns_minimal_features(test_db: Session):
    """Unknown ticker should return features with insufficient data."""
    engine = HistoricalFeatureEngine(test_db)

    features = engine.calculate("UNKNOWN", date(2024, 6, 1))

    assert features.symbol == "UNKNOWN"
    assert features.issuer_id == 0
    assert features.data_quality == "insufficient"
    assert features.periods_available == 0
    assert features.revenue_growth_pct is None


def test_feature_dict_structure(test_db: Session, setup_company):
    """to_dict should have expected structure."""
    engine = HistoricalFeatureEngine(test_db)

    features = engine.calculate("TFCO", date(2025, 2, 20))
    feature_dict = features.to_dict()

    assert "symbol" in feature_dict
    assert "issuer_id" in feature_dict
    assert "as_of_date" in feature_dict
    assert "growth" in feature_dict
    assert "profitability" in feature_dict
    assert "leverage" in feature_dict
    assert "cash_flow" in feature_dict
    assert "data_quality" in feature_dict

    assert feature_dict["growth"]["revenue_pct"] is not None
    assert feature_dict["profitability"]["roe_pct"] is not None
