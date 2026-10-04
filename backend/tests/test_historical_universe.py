"""Tests for historical universe reconstruction.

Validates that:
1. Future listings are excluded
2. Price coverage is counted correctly
3. Fundamental coverage is counted correctly
4. Sector filtering works
5. Timeline generation produces correct snapshots
"""

from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import (
    FinancialFact,
    Issuer,
    PriceOHLCV,
    Security,
    Sector,
    IngestionRun,
    SourceDocument,
)
from app.services.historical_universe import historical_universe, universe_timeline


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
def setup_universe(test_db: Session):
    """Create test universe with multiple securities and sectors."""
    # Create sectors
    fert_sector = Sector(name="Fertilizer")
    cement_sector = Sector(name="Cement")
    test_db.add_all([fert_sector, cement_sector])
    test_db.flush()

    # Create issuers
    ffco = Issuer(name="FFC Ltd", sector_id=fert_sector.id)
    efert = Issuer(name="EFERT Ltd", sector_id=fert_sector.id)
    luck = Issuer(name="LUCK Ltd", sector_id=cement_sector.id)
    test_db.add_all([ffco, efert, luck])
    test_db.flush()

    # Create securities with different listing dates
    sec_ffc = Security(
        issuer_id=ffco.id,
        symbol="FFC",
        listing_date=date(2020, 1, 1),
        is_active=True,
    )
    sec_efert = Security(
        issuer_id=efert.id,
        symbol="EFERT",
        listing_date=date(2021, 6, 1),
        is_active=True,
    )
    sec_luck = Security(
        issuer_id=luck.id,
        symbol="LUCK",
        listing_date=date(2024, 9, 1),  # Future listing
        is_active=True,
    )
    test_db.add_all([sec_ffc, sec_efert, sec_luck])
    test_db.flush()

    # Create source document for financials
    source_doc = SourceDocument(
        document_type="financial_statement",
        url="http://example.com/ffc-financials.pdf",
        content_hash="abc123def456abc123def456abc123def456abc123def456abc123def456ab",
        fetched_at=datetime.now(timezone.utc),
        source_tier="primary",
    )
    test_db.add(source_doc)
    test_db.flush()

    # Create ingestion run for prices
    ingest = IngestionRun(source="test", status="ok")
    test_db.add(ingest)
    test_db.flush()

    # Add price data for FFC (before and on test dates)
    for i in range(100):
        price_date = date(2024, 1, 1) + timedelta(days=i)
        price = PriceOHLCV(
            security_id=sec_ffc.id,
            trade_date=price_date,
            open=1000.0,
            high=1050.0,
            low=950.0,
            close=1000.0 + i,
            source="test",
            ingestion_run_id=ingest.id,
        )
        test_db.add(price)

    # Add price data for EFERT (limited)
    price_efert = PriceOHLCV(
        security_id=sec_efert.id,
        trade_date=date(2024, 6, 1),
        open=500.0,
        high=520.0,
        low=480.0,
        close=500.0,
        source="test",
        ingestion_run_id=ingest.id,
    )
    test_db.add(price_efert)

    test_db.commit()

    return {
        "sectors": {"fert": fert_sector, "cement": cement_sector},
        "issuers": {"ffc": ffco, "efert": efert, "luck": luck},
        "securities": {"ffc": sec_ffc, "efert": sec_efert, "luck": sec_luck},
        "ingest": ingest,
        "source_doc": source_doc,
    }


def test_universe_excludes_future_listings(test_db: Session, setup_universe):
    """Securities listed after as_of_date should not appear."""
    result = historical_universe(test_db, date(2024, 8, 31))

    symbols = [s["symbol"] for s in result["securities"]]
    assert "LUCK" not in symbols, "LUCK listed on 2024-09-01, should not appear as-of 2024-08-31"
    assert "FFC" in symbols
    assert "EFERT" in symbols


def test_universe_includes_current_listings(test_db: Session, setup_universe):
    """Securities listed on or before as_of_date should appear."""
    result = historical_universe(test_db, date(2024, 9, 1))

    symbols = [s["symbol"] for s in result["securities"]]
    assert "LUCK" in symbols, "LUCK listed on 2024-09-01, should appear"
    assert result["total_count"] == 3


def test_universe_counts_price_coverage(test_db: Session, setup_universe):
    """Price bars should be counted correctly."""
    result = historical_universe(test_db, date(2024, 6, 1))

    # Find FFC in results
    ffc_data = next(s for s in result["securities"] if s["symbol"] == "FFC")
    assert ffc_data["price_coverage"]["available"] is True
    assert ffc_data["price_coverage"]["bars_count"] > 0

    # EFERT has price as of 2024-06-01
    efert_data = next(s for s in result["securities"] if s["symbol"] == "EFERT")
    assert efert_data["price_coverage"]["available"] is True


def test_universe_price_coverage_before_data(test_db: Session, setup_universe):
    """Securities with no price data on date should not have coverage."""
    result = historical_universe(test_db, date(2023, 12, 31))

    # No prices exist before 2024-01-01
    ffc_data = next(s for s in result["securities"] if s["symbol"] == "FFC")
    assert ffc_data["price_coverage"]["available"] is False
    assert ffc_data["price_coverage"]["bars_count"] == 0


def test_universe_counts_fundamentals_coverage(test_db: Session, setup_universe):
    """Fundamental facts should be counted correctly."""
    # Add financial facts
    today = date(2024, 6, 1)
    fact = FinancialFact(
        issuer_id=setup_universe["issuers"]["ffc"].id,
        line_item="revenue",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 3, 31),
        period_type="quarterly",
        scope="standalone",
        unit="PKR",
        value=1000000,
        source_document_id=setup_universe["source_doc"].id,
        published_at=datetime.combine(today, time(12, 0), tzinfo=timezone.utc),
    )
    test_db.add(fact)
    test_db.commit()

    result = historical_universe(test_db, date(2024, 6, 1))

    ffc_data = next(s for s in result["securities"] if s["symbol"] == "FFC")
    assert ffc_data["fundamentals_coverage"]["available"] is True
    assert ffc_data["fundamentals_coverage"]["facts_count"] == 1


def test_universe_excludes_future_facts(test_db: Session, setup_universe):
    """Facts published after as_of_date should not count."""
    # Add fact published in future
    future_date = date(2024, 7, 1)
    future_fact = FinancialFact(
        issuer_id=setup_universe["issuers"]["ffc"].id,
        line_item="profit",
        period_start=date(2024, 4, 1),
        period_end=date(2024, 6, 30),
        period_type="quarterly",
        scope="standalone",
        unit="PKR",
        value=500000,
        source_document_id=setup_universe["source_doc"].id,
        published_at=datetime.combine(
            future_date, time(12, 0), tzinfo=timezone.utc
        ),
    )
    test_db.add(future_fact)
    test_db.commit()

    # Query before publication
    result = historical_universe(test_db, date(2024, 6, 30))

    ffc_data = next(s for s in result["securities"] if s["symbol"] == "FFC")
    assert ffc_data["fundamentals_coverage"]["facts_count"] == 0


def test_universe_sector_filtering(test_db: Session, setup_universe):
    """Sector filter should isolate results."""
    result = historical_universe(test_db, date(2024, 6, 1), sector_name="Fertilizer")

    symbols = [s["symbol"] for s in result["securities"]]
    assert "FFC" in symbols
    assert "EFERT" in symbols
    assert "LUCK" not in symbols, "LUCK is in Cement, not Fertilizer"


def test_universe_coverage_percentages(test_db: Session, setup_universe):
    """Coverage percentages should be calculated correctly."""
    result = historical_universe(test_db, date(2024, 6, 1))

    assert result["coverage_summary"]["price_coverage_pct"] > 0
    # FFC has price, EFERT has price, LUCK doesn't exist yet
    assert result["price_covered_count"] == 2


def test_universe_timeline_intervals(test_db: Session, setup_universe):
    """Timeline should generate snapshots at correct intervals."""
    result = universe_timeline(
        test_db,
        date(2024, 1, 1),
        date(2024, 9, 30),
        sample_interval_days=30,
    )

    # 9 months / 30 days ≈ 9 snapshots (actually 10 including start)
    assert len(result["snapshots"]) >= 9
    assert result["snapshots"][0]["total_count"] == 2  # FFC and EFERT, not LUCK
    assert result["snapshots"][-1]["total_count"] == 3  # Now LUCK is included


def test_universe_timeline_summary(test_db: Session, setup_universe):
    """Timeline summary should track min/max coverage."""
    result = universe_timeline(
        test_db,
        date(2024, 1, 1),
        date(2024, 9, 30),
        sample_interval_days=30,
    )

    summary = result["summary"]
    assert "min_total_count" in summary
    assert "max_total_count" in summary
    assert summary["max_total_count"] >= summary["min_total_count"]
