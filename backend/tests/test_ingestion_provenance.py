from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import app.db.models  # noqa: F401  registers every table on Base
from app.db.base import Base
from app.db.models import IngestionRun, Issuer, PriceOHLCV, Security
from app.ingestion import psx_prices


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    for i, symbol in enumerate(["GOOD", "BAD"], start=1):
        session.add(Issuer(id=i, name=f"{symbol} Ltd"))
        session.add(Security(id=i, issuer_id=i, symbol=symbol))
    session.commit()
    yield session
    session.close()


def _bars():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-09-22", "2026-09-23"]),
            "open": [10.0, 11.0], "high": [12.0, 12.0], "low": [9.0, 10.0], "close": [11.0, 11.5],
            "volume": [1000, 2000], "is_anomaly": [False, False],
        }
    )


def _stocks(symbol, start, end):
    if symbol == "BAD":
        raise ConnectionError("403 from PSX")
    return _bars()


def test_failed_fetch_is_recorded_and_stores_nothing(db, monkeypatch):
    monkeypatch.setattr(psx_prices.psxdata, "stocks", _stocks)
    securities = db.execute(select(Security).order_by(Security.id)).scalars().all()

    psx_prices.backfill_all(db, securities, date(2026, 9, 1), date(2026, 9, 30))

    run = db.execute(select(IngestionRun)).scalar_one()
    assert run.status == "partial"
    assert run.rows_inserted == 2
    assert run.finished_at is not None
    assert len(run.errors) == 1 and run.errors[0].startswith("BAD: ConnectionError")

    bars = db.execute(select(PriceOHLCV)).scalars().all()
    assert {b.security_id for b in bars} == {1}
    assert all(b.ingestion_run_id == run.id and b.source == "psxdata" and b.retrieved_at for b in bars)


def test_run_with_only_failures_is_failed(db, monkeypatch):
    monkeypatch.setattr(psx_prices.psxdata, "stocks", lambda *a, **k: pd.DataFrame())
    psx_prices.backfill_all(db, db.execute(select(Security)).scalars().all(), date(2026, 9, 1), date(2026, 9, 30))

    run = db.execute(select(IngestionRun)).scalar_one()
    assert run.status == "failed" and run.rows_inserted == 0
    assert db.execute(select(PriceOHLCV)).first() is None


def test_bar_without_run_is_rejected(db):
    db.add(PriceOHLCV(security_id=1, trade_date=date(2026, 9, 22), open=1, high=1, low=1, close=1, source="psxdata"))
    with pytest.raises(IntegrityError):
        db.commit()
