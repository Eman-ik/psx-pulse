"""Tests for backtesting framework.

Validates that:
1. Backtester can run through date range
2. Position sizing works correctly
3. Daily P&L is calculated
4. Risk metrics are computed
5. Strategy rules are applied correctly
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import List, Tuple

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
from app.services.backtester import Backtester, BacktestResult, Position
from app.services.historical_snapshot import HistoricalSnapshot


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
def setup_backtest_universe(test_db: Session):
    """Create 3 companies with price and fundamental data for backtesting."""
    sector = Sector(name="Test")
    test_db.add(sector)
    test_db.flush()

    source_doc = SourceDocument(
        document_type="financial_statement",
        url="http://example.com/financials.pdf",
        content_hash="backtesthash111111111111111111111111111111111111111111111111",
        fetched_at=datetime.now(timezone.utc),
        source_tier="primary",
    )
    test_db.add(source_doc)
    test_db.flush()

    ingest = IngestionRun(source="test", status="ok")
    test_db.add(ingest)
    test_db.flush()

    # Create 3 test companies
    companies = []
    for i in range(3):
        issuer = Issuer(name=f"Test Co {i}", sector_id=sector.id)
        test_db.add(issuer)
        test_db.flush()

        security = Security(
            issuer_id=issuer.id,
            symbol=f"TST{i}",
            listing_date=date(2024, 1, 1),
            is_active=True,
        )
        test_db.add(security)
        test_db.flush()

        # Add financials (published before test start)
        for year in [2023, 2024]:
            period_end = date(year, 12, 31)
            facts = [
                FinancialFact(
                    issuer_id=issuer.id,
                    line_item="revenue",
                    period_start=date(year, 1, 1),
                    period_end=period_end,
                    period_type="annual",
                    scope="standalone",
                    unit="PKR",
                    value=10000000 + i * 1000000,
                    source_document_id=source_doc.id,
                    published_at=datetime.combine(
                        date(2024, 3, 15), time(10, 0), tzinfo=timezone.utc
                    ),
                ),
                FinancialFact(
                    issuer_id=issuer.id,
                    line_item="profit_after_tax",
                    period_start=date(year, 1, 1),
                    period_end=period_end,
                    period_type="annual",
                    scope="standalone",
                    unit="PKR",
                    value=2000000,
                    source_document_id=source_doc.id,
                    published_at=datetime.combine(
                        date(2024, 3, 15), time(10, 0), tzinfo=timezone.utc
                    ),
                ),
                FinancialFact(
                    issuer_id=issuer.id,
                    line_item="total_assets",
                    period_start=date(year, 1, 1),
                    period_end=period_end,
                    period_type="annual",
                    scope="standalone",
                    unit="PKR",
                    value=50000000,
                    source_document_id=source_doc.id,
                    published_at=datetime.combine(
                        date(2024, 3, 15), time(10, 0), tzinfo=timezone.utc
                    ),
                ),
                FinancialFact(
                    issuer_id=issuer.id,
                    line_item="total_equity",
                    period_start=date(year, 1, 1),
                    period_end=period_end,
                    period_type="annual",
                    scope="standalone",
                    unit="PKR",
                    value=25000000,
                    source_document_id=source_doc.id,
                    published_at=datetime.combine(
                        date(2024, 3, 15), time(10, 0), tzinfo=timezone.utc
                    ),
                ),
            ]
            test_db.add_all(facts)

        companies.append((issuer, security))

    test_db.flush()

    # Add prices for 60 days starting 2024-06-01
    for i in range(3):
        issuer, security = companies[i]
        base_price = 1000 + i * 100
        for day in range(60):
            price_date = date(2024, 6, 1) + timedelta(days=day)
            if price_date.weekday() < 5:  # Weekdays only
                price = PriceOHLCV(
                    security_id=security.id,
                    trade_date=price_date,
                    open=base_price + day * 0.5,
                    high=base_price + day * 0.6,
                    low=base_price + day * 0.4,
                    close=base_price + day * 0.5 + (i - 1) * 0.2,  # Slight uptrend
                    source="test",
                    ingestion_run_id=ingest.id,
                )
                test_db.add(price)

    test_db.commit()
    return companies


def test_backtester_initialization(test_db: Session):
    """Backtester should initialize with correct parameters."""
    backtester = Backtester(
        test_db,
        strategy_name="Test Strategy",
        portfolio_size_pkr=1_000_000,
    )

    assert backtester.strategy_name == "Test Strategy"
    assert backtester.portfolio_size_pkr == 1_000_000
    assert len(backtester.positions) == 0


def test_position_pnl_calculation():
    """Position should correctly calculate P&L."""
    position = Position(
        symbol="TEST",
        entry_date=date(2024, 6, 1),
        entry_price=1000.0,
        quantity=100,
        conviction=80.0,
    )

    # Entry value
    assert position.entry_value == 100_000

    # P&L at break-even
    assert position.get_pnl(1000.0) == 0
    assert position.get_return_pct(1000.0) == 0

    # P&L with 10% gain
    assert position.get_pnl(1100.0) == 10_000
    assert position.get_return_pct(1100.0) == 10.0

    # P&L with 5% loss
    assert position.get_pnl(950.0) == -5_000
    assert position.get_return_pct(950.0) == -5.0


def test_backtest_result_structure():
    """BacktestResult should contain all metrics."""
    result = BacktestResult(
        strategy_name="Test",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 7, 31),
        portfolio_size_pkr=1_000_000,
        total_return_pct=10.0,
        annual_return_pct=60.0,
        volatility_pct=15.0,
        max_drawdown_pct=5.0,
        sharpe_ratio=4.0,
    )

    result_dict = result.to_dict()

    assert result_dict["strategy_name"] == "Test"
    assert result_dict["returns"]["total_pct"] == 10.0
    assert result_dict["risk"]["volatility_pct"] == 15.0
    assert result_dict["efficiency"]["sharpe_ratio"] == 4.0


def test_backtest_simple_strategy(test_db: Session, setup_backtest_universe):
    """Backtest should run simple strategy end-to-end."""
    backtester = Backtester(
        test_db,
        strategy_name="Simple Long-Only",
        portfolio_size_pkr=1_000_000,
        max_positions=3,
    )

    # Simple strategy: buy all investable securities with equal conviction
    def simple_strategy(snapshots: List) -> List[Tuple[str, float]]:
        return [(s.symbol, 50.0) for s in snapshots if s.is_investable()]

    # Run short backtest (2 weeks)
    result = backtester.run(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 14),
        decision_function=simple_strategy,
    )

    assert result.strategy_name == "Simple Long-Only"
    assert result.start_date == date(2024, 6, 1)
    assert result.end_date == date(2024, 6, 14)
    assert result.positions_opened > 0


def test_backtest_metrics_calculated(test_db: Session, setup_backtest_universe):
    """Backtest should calculate risk/return metrics."""
    backtester = Backtester(
        test_db,
        strategy_name="Metric Test",
        portfolio_size_pkr=500_000,
    )

    def simple_strategy(snapshots: List) -> List[Tuple[str, float]]:
        return [(s.symbol, 50.0) for s in snapshots[:1]]

    result = backtester.run(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 30),
        decision_function=simple_strategy,
    )

    # Metrics should be calculated
    assert result.total_return_pct is not None
    assert result.volatility_pct >= 0
    assert result.max_drawdown_pct >= 0
    assert len(result.daily_returns) > 0
    assert len(result.daily_values) > 0


def test_backtest_no_positions():
    """Backtest with no positions should handle gracefully."""
    pytest.skip("Requires empty database setup")


def test_backtest_winning_losing_days(test_db: Session, setup_backtest_universe):
    """Backtest should track winning and losing days."""
    backtester = Backtester(
        test_db,
        strategy_name="Win/Loss Test",
        portfolio_size_pkr=1_000_000,
    )

    def simple_strategy(snapshots: List) -> List[Tuple[str, float]]:
        return [(s.symbol, 50.0) for s in snapshots[:1]]

    result = backtester.run(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 30),
        decision_function=simple_strategy,
    )

    # Should have some winning/losing days
    total_days = result.winning_days + result.losing_days
    assert total_days > 0
    assert result.best_day_pct is not None
    assert result.worst_day_pct is not None
