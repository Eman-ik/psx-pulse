"""Tests for historical snapshot engine.

Validates that:
1. Snapshots merge all data correctly (Stages 1-3 + price)
2. Universe membership is correct
3. Investability assessment works
4. Quality assessment reflects data completeness
5. Batch snapshots work correctly
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
    SourceDocument,
    IngestionRun,
)
from app.services.historical_snapshot import HistoricalSnapshotEngine


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
def setup_complete_company(test_db: Session):
    """Create company with all data: listing, prices, and financials."""
    sector = Sector(name="Fertilizer")
    test_db.add(sector)
    test_db.flush()

    issuer = Issuer(name="Complete Co", sector_id=sector.id)
    test_db.add(issuer)
    test_db.flush()

    security = Security(
        issuer_id=issuer.id,
        symbol="COMPLETE",
        listing_date=date(2023, 1, 1),
        is_active=True,
    )
    test_db.add(security)
    test_db.flush()

    source_doc = SourceDocument(
        document_type="financial_statement",
        url="http://example.com/complete.pdf",
        content_hash="hash1111111111111111111111111111111111111111111111111111111111",
        fetched_at=datetime.now(timezone.utc),
        source_tier="primary",
    )
    test_db.add(source_doc)
    test_db.flush()

    ingest = IngestionRun(source="test", status="ok")
    test_db.add(ingest)
    test_db.flush()

    # Add 2 years of financials (published before 2024-06-01)
    for year in [2023, 2024]:
        period_end = date(year, 12, 31)
        # Publish all financials before 2024-06-01 for test
        publish_date = date(2024, 3, 15)

        revenue = 10000000 + (year - 2023) * 2000000
        pat = 2000000 + (year - 2023) * 800000

        facts = [
            FinancialFact(
                issuer_id=issuer.id,
                line_item="revenue",
                period_start=date(year, 1, 1),
                period_end=period_end,
                period_type="annual",
                scope="standalone",
                unit="PKR",
                value=revenue,
                source_document_id=source_doc.id,
                published_at=datetime.combine(publish_date, time(10, 0), tzinfo=timezone.utc),
            ),
            FinancialFact(
                issuer_id=issuer.id,
                line_item="profit_after_tax",
                period_start=date(year, 1, 1),
                period_end=period_end,
                period_type="annual",
                scope="standalone",
                unit="PKR",
                value=pat,
                source_document_id=source_doc.id,
                published_at=datetime.combine(publish_date, time(10, 0), tzinfo=timezone.utc),
            ),
            FinancialFact(
                issuer_id=issuer.id,
                line_item="total_assets",
                period_start=date(year, 1, 1),
                period_end=period_end,
                period_type="annual",
                scope="standalone",
                unit="PKR",
                value=50000000 + (year - 2023) * 5000000,
                source_document_id=source_doc.id,
                published_at=datetime.combine(publish_date, time(10, 0), tzinfo=timezone.utc),
            ),
            FinancialFact(
                issuer_id=issuer.id,
                line_item="total_equity",
                period_start=date(year, 1, 1),
                period_end=period_end,
                period_type="annual",
                scope="standalone",
                unit="PKR",
                value=25000000 + (year - 2023) * 2000000,
                source_document_id=source_doc.id,
                published_at=datetime.combine(publish_date, time(10, 0), tzinfo=timezone.utc),
            ),
        ]
        test_db.add_all(facts)

    # Add prices for 6 months before snapshot date
    test_db.flush()
    for i in range(120):  # 120 trading days ≈ 6 months
        price_date = date(2024, 1, 1) + timedelta(days=i)
        if price_date.weekday() < 5:  # Weekdays only
            price = PriceOHLCV(
                security_id=security.id,
                trade_date=price_date,
                open=1000.0 + i,
                high=1050.0 + i,
                low=950.0 + i,
                close=1000.0 + i * 0.5,
                source="test",
                ingestion_run_id=ingest.id,
            )
            test_db.add(price)

    test_db.commit()

    return {
        "issuer": issuer,
        "security": security,
        "source_doc": source_doc,
        "ingest": ingest,
    }


def test_snapshot_structure(test_db: Session, setup_complete_company):
    """Snapshot should have all required fields."""
    engine = HistoricalSnapshotEngine(test_db)
    snapshot = engine.snapshot("COMPLETE", date(2024, 6, 1))

    snapshot_dict = snapshot.to_dict()
    assert "symbol" in snapshot_dict
    assert "issuer_id" in snapshot_dict
    assert "as_of_date" in snapshot_dict
    assert "universe_membership" in snapshot_dict
    assert "price" in snapshot_dict
    assert "features" in snapshot_dict
    assert "snapshot_quality" in snapshot_dict


def test_snapshot_complete_data(test_db: Session, setup_complete_company):
    """With all data, snapshot should be complete and investable."""
    engine = HistoricalSnapshotEngine(test_db)
    snapshot = engine.snapshot("COMPLETE", date(2024, 6, 1))

    assert snapshot.symbol == "COMPLETE"
    assert snapshot.is_listed is True
    assert snapshot.has_price_coverage is True
    assert snapshot.has_fundamentals_coverage is True
    assert snapshot.close_price is not None
    assert snapshot.features is not None
    assert snapshot.features.data_quality == "available"
    assert snapshot.is_investable() is True
    assert snapshot.snapshot_quality == "complete"


def test_snapshot_future_listing_not_listed(test_db: Session, setup_complete_company):
    """Company listed in future should not be listed as-of past date."""
    # Create new company with future listing
    sector = test_db.query(__import__('app.db.models', fromlist=['Sector']).Sector).first()
    issuer = Issuer(name="Future Co", sector_id=sector.id)
    test_db.add(issuer)
    test_db.flush()

    security = Security(
        issuer_id=issuer.id,
        symbol="FUTURE",
        listing_date=date(2024, 9, 1),
        is_active=True,
    )
    test_db.add(security)
    test_db.commit()

    engine = HistoricalSnapshotEngine(test_db)
    snapshot = engine.snapshot("FUTURE", date(2024, 6, 1))

    assert snapshot.is_listed is False
    assert snapshot.is_investable() is False
    assert snapshot.snapshot_quality == "insufficient"


def test_snapshot_no_price_data(test_db: Session, setup_complete_company):
    """Company with no price data should be partial."""
    # Create company with financials but no prices
    sector = test_db.query(__import__('app.db.models', fromlist=['Sector']).Sector).first()
    issuer = Issuer(name="No Price Co", sector_id=sector.id)
    test_db.add(issuer)
    test_db.flush()

    security = Security(
        issuer_id=issuer.id,
        symbol="NOPRICE",
        listing_date=date(2023, 1, 1),
        is_active=True,
    )
    test_db.add(security)
    test_db.commit()

    engine = HistoricalSnapshotEngine(test_db)
    snapshot = engine.snapshot("NOPRICE", date(2024, 6, 1))

    assert snapshot.is_listed is True
    assert snapshot.close_price is None
    assert snapshot.is_investable() is False
    assert snapshot.snapshot_quality == "insufficient"


def test_snapshot_gets_most_recent_price(test_db: Session, setup_complete_company):
    """Should get most recent price on or before as_of_date."""
    engine = HistoricalSnapshotEngine(test_db)
    snapshot = engine.snapshot("COMPLETE", date(2024, 6, 1))

    # Price on 2024-06-01 should be approximately 1000 + 0.5 * trading_days
    assert snapshot.close_price is not None
    assert snapshot.price_date <= date(2024, 6, 1)


def test_snapshot_investable_flag(test_db: Session, setup_complete_company):
    """is_investable() should be true only when all conditions met."""
    engine = HistoricalSnapshotEngine(test_db)

    # Complete snapshot should be investable
    snapshot = engine.snapshot("COMPLETE", date(2024, 6, 1))
    assert snapshot.is_investable() is True

    # Incomplete snapshot should not be investable
    snapshot_early = engine.snapshot("COMPLETE", date(2023, 1, 15))
    # Listed but no fundamental data (only published 2024-02-15)
    assert snapshot_early.is_investable() is False


def test_snapshot_batch(test_db: Session, setup_complete_company):
    """Batch snapshots should return list of snapshots."""
    engine = HistoricalSnapshotEngine(test_db)
    snapshots = engine.snapshot_batch(
        ["COMPLETE", "UNKNOWN"], date(2024, 6, 1)
    )

    assert len(snapshots) == 2
    assert snapshots[0].symbol == "COMPLETE"
    assert snapshots[0].is_investable() is True
    assert snapshots[1].symbol == "UNKNOWN"
    assert snapshots[1].is_investable() is False


def test_snapshot_quality_assessment(test_db: Session, setup_complete_company):
    """Quality should reflect data completeness."""
    engine = HistoricalSnapshotEngine(test_db)

    # With all data
    snapshot_complete = engine.snapshot("COMPLETE", date(2024, 6, 1))
    assert snapshot_complete.snapshot_quality == "complete"

    # Before financials published (2024-03-15), but with price data
    snapshot_early = engine.snapshot("COMPLETE", date(2024, 2, 1))
    assert snapshot_early.snapshot_quality == "partial"  # Has price, no fundamentals


def test_snapshot_features_included(test_db: Session, setup_complete_company):
    """Snapshot features should match feature engine output."""
    engine = HistoricalSnapshotEngine(test_db)
    snapshot = engine.snapshot("COMPLETE", date(2024, 6, 1))

    assert snapshot.features is not None
    assert snapshot.features.symbol == "COMPLETE"
    assert snapshot.features.as_of_date == date(2024, 6, 1)
    assert snapshot.features.revenue_growth_pct is not None


def test_snapshot_unknown_ticker(test_db: Session):
    """Unknown ticker should return minimal snapshot."""
    engine = HistoricalSnapshotEngine(test_db)
    snapshot = engine.snapshot("UNKNOWN", date(2024, 6, 1))

    assert snapshot.symbol == "UNKNOWN"
    assert snapshot.issuer_id == 0
    assert snapshot.is_investable() is False
    assert snapshot.snapshot_quality == "insufficient"
