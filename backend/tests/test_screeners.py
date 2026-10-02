from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db.models  # noqa: F401  registers every table on Base
from app.db.base import Base
from app.db.models import IngestionRun, Issuer, PriceOHLCV, Security
from app.research_system.momentum_screener import MomentumScreener
from app.research_system.technical_screener import TechnicalScreener

LATEST = date(2026, 9, 30)


@pytest.fixture
def db():
    session = sessionmaker(bind=_engine())()
    session.add_all([IngestionRun(id=1, source="test", status="ok", rows_inserted=0, errors=[]),
                     Issuer(id=1, name="Test Co"), Security(id=1, issuer_id=1, symbol="TST")])
    session.commit()
    yield session
    session.close()


def _engine():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine


def _bars(db, days_and_closes):
    for d, close in days_and_closes:
        db.add(PriceOHLCV(security_id=1, trade_date=d, open=close, high=close, low=close, close=close,
                          volume=1000, source="test", ingestion_run_id=1))
    db.commit()


def test_short_history_reports_unavailable_not_false(db):
    _bars(db, [(LATEST - timedelta(days=i), 100.0 + i) for i in range(30)])
    s = TechnicalScreener.screen_security(db, db.get(Security, 1), LATEST)

    assert s.above_20dma is not None
    assert s.price_vs_200dma is None and s.above_200dma is None
    assert s.lookback_days == 30 and s.lookback_complete is False


def test_flat_price_is_a_zero_return_not_missing(db):
    _bars(db, [(LATEST - timedelta(days=i), 50.0) for i in range(0, 40)])
    s = MomentumScreener.screen_security(db, db.get(Security, 1), LATEST, 50.0)

    assert s.return_1m == 0.0
    assert "1m" not in s.unavailable


def test_data_gap_makes_horizon_unavailable_instead_of_stale(db):
    # Nothing between 60 days ago and today, so the 1-month anchor would be two months stale.
    _bars(db, [(LATEST, 110.0)] + [(LATEST - timedelta(days=i), 100.0) for i in range(60, 120)])
    s = MomentumScreener.screen_security(db, db.get(Security, 1), LATEST, 110.0)

    assert s.return_1m is None and "1m" in s.unavailable
    assert s.return_3m == pytest.approx(10.0)
