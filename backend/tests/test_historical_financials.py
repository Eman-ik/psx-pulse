"""Tests for point-in-time historical financial facts.

Validates that:
1. Facts published after query date are not returned
2. Facts superseded are not returned
3. Restated facts are marked correctly
4. Period-end filtering works as expected
"""

from datetime import date, datetime, timedelta, timezone, time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import FinancialFact, Issuer, Security, Sector
from app.services.historical_financials import get_financials_as_of, get_financials_series


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
def setup_issuer(test_db: Session):
    """Create test issuer and security."""
    sector = Sector(name="Test Sector")
    test_db.add(sector)
    test_db.flush()

    issuer = Issuer(name="Test Co Ltd", sector_id=sector.id)
    test_db.add(issuer)
    test_db.flush()

    security = Security(issuer_id=issuer.id, symbol="TEST", is_active=True)
    test_db.add(security)
    test_db.commit()

    return issuer, security


def test_as_of_excludes_future_published_facts(test_db: Session, setup_issuer):
    """Facts published after as_of_date should not appear."""
    issuer, security = setup_issuer
    today = date.today()

    # Fact published tomorrow
    future_fact = FinancialFact(
        issuer_id=issuer.id,
        line_item="revenue",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
        period_type="annual",
        scope="standalone",
        unit="PKR",
        value=1000,
        source_document_id=1,
        published_at=datetime.combine(today + timedelta(days=1), time(12, 0), tzinfo=timezone.utc),
    )
    test_db.add(future_fact)
    test_db.commit()

    result = get_financials_as_of(test_db, "TEST", today)

    assert result["count"] == 0, "Future published facts should be excluded"
    assert len(result["facts"]) == 0


def test_as_of_includes_published_facts(test_db: Session, setup_issuer):
    """Facts published on or before as_of_date should appear."""
    issuer, security = setup_issuer
    today = date.today()

    fact = FinancialFact(
        issuer_id=issuer.id,
        line_item="revenue",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
        period_type="annual",
        scope="standalone",
        unit="PKR",
        value=1000,
        source_document_id=1,
        published_at=datetime.combine(today, time(12, 0), tzinfo=timezone.utc),
    )
    test_db.add(fact)
    test_db.commit()

    result = get_financials_as_of(test_db, "TEST", today)

    assert result["count"] == 1
    assert result["facts"][0]["line_item"] == "revenue"
    assert result["facts"][0]["value"] == 1000.0
    assert result["facts"][0]["is_restated"] is False


def test_as_of_excludes_superseded_facts(test_db: Session, setup_issuer):
    """Superseded facts should not appear (only latest version)."""
    issuer, security = setup_issuer
    today = date.today()

    # Original fact
    original_fact = FinancialFact(
        issuer_id=issuer.id,
        line_item="revenue",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
        period_type="annual",
        scope="standalone",
        unit="PKR",
        value=1000,
        source_document_id=1,
        published_at=datetime.combine(today - timedelta(days=10), time(12, 0), tzinfo=timezone.utc),
    )
    test_db.add(original_fact)
    test_db.flush()

    # Restated fact supersedes original
    restated_fact = FinancialFact(
        issuer_id=issuer.id,
        line_item="revenue",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
        period_type="annual",
        scope="standalone",
        unit="PKR",
        value=1100,  # Corrected value
        source_document_id=1,
        published_at=datetime.combine(today - timedelta(days=5), time(12, 0), tzinfo=timezone.utc),
        is_restated=True,
        superseded_by_id=None,  # Will be set below
    )
    test_db.add(restated_fact)
    test_db.flush()

    original_fact.superseded_by_id = restated_fact.id
    test_db.commit()

    result = get_financials_as_of(test_db, "TEST", today)

    assert result["count"] == 1, "Only latest (restated) fact should appear"
    assert result["facts"][0]["value"] == 1100.0
    assert result["facts"][0]["is_restated"] is True


def test_as_of_respects_period_filter(test_db: Session, setup_issuer):
    """period_type filter should exclude other period types."""
    issuer, security = setup_issuer
    today = date.today()

    # Add annual fact
    annual = FinancialFact(
        issuer_id=issuer.id,
        line_item="revenue",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
        period_type="annual",
        scope="standalone",
        unit="PKR",
        value=1000,
        source_document_id=1,
        published_at=datetime.combine(today, time(12, 0), tzinfo=timezone.utc),
    )
    test_db.add(annual)

    # Add quarterly fact
    quarterly = FinancialFact(
        issuer_id=issuer.id,
        line_item="revenue",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 3, 31),
        period_type="quarterly",
        scope="standalone",
        unit="PKR",
        value=250,
        source_document_id=1,
        published_at=datetime.combine(today, time(12, 0), tzinfo=timezone.utc),
    )
    test_db.add(quarterly)
    test_db.commit()

    # Query with period_type filter
    result = get_financials_as_of(test_db, "TEST", today, period_type="annual")

    assert result["count"] == 1
    assert result["facts"][0]["period_type"] == "annual"


def test_series_includes_all_versions(test_db: Session, setup_issuer):
    """Series should include all historical versions (superseded too)."""
    issuer, security = setup_issuer
    today = date.today()

    # Original value
    original = FinancialFact(
        issuer_id=issuer.id,
        line_item="revenue",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
        period_type="annual",
        scope="standalone",
        unit="PKR",
        value=1000,
        source_document_id=1,
        published_at=datetime.combine(today - timedelta(days=10), time(12, 0), tzinfo=timezone.utc),
    )
    test_db.add(original)
    test_db.flush()

    # Restated value
    restated = FinancialFact(
        issuer_id=issuer.id,
        line_item="revenue",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
        period_type="annual",
        scope="standalone",
        unit="PKR",
        value=1100,
        source_document_id=1,
        published_at=datetime.combine(today - timedelta(days=5), time(12, 0), tzinfo=timezone.utc),
        is_restated=True,
    )
    test_db.add(restated)
    test_db.flush()

    original.superseded_by_id = restated.id
    test_db.commit()

    result = get_financials_series(test_db, "TEST", "revenue")

    assert result["count"] == 2, "Series should include both original and restated"
    assert result["series"][0]["superseded"] is True  # Original is superseded
    assert result["series"][1]["superseded"] is False  # Restated is not


def test_unknown_ticker_returns_error(test_db: Session):
    """Unknown ticker should return error."""
    result = get_financials_as_of(test_db, "UNKNOWN", date.today())

    assert "error" in result
    assert "No active security found" in result["error"]
    assert result["count"] == 0
