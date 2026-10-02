from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db.models  # noqa: F401  registers every table on Base
from app.db.base import Base
from app.db.models import IngestionRun, Issuer, PriceOHLCV, Security
from app.research_system.trade_check import position_size, run_trade_check


def _db(last_bar: date):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all([IngestionRun(id=1, source="test", status="ok", rows_inserted=0, errors=[]),
                Issuer(id=1, name="Test Co"), Security(id=1, issuer_id=1, symbol="TST")])
    # 30 bars, close 100, daily range 98-102 (ATR 4), volume 10,000.
    for i in range(30):
        db.add(PriceOHLCV(security_id=1, trade_date=last_bar - timedelta(days=i), open=100, high=102, low=98,
                          close=100, volume=10_000, source="test", ingestion_run_id=1))
    db.commit()
    return db


def _gates(result):
    return {g["name"]: g["status"] for g in result["gates"]}


def test_position_size_math():
    s = position_size(entry=100, stop=95, targets=[110, 115], portfolio_value=100_000, risk_percent=1)
    assert s["shares"] == 200 and s["max_loss"] == 1000 and s["capital_required"] == 20_000
    assert [r["ratio"] for r in s["reward_risk"]] == [2.0, 3.0]


def test_healthy_trade_passes_each_gate_without_a_verdict():
    db = _db(date.today())
    result = run_trade_check(db, "tst", entry=100, stop=94, targets=[115], portfolio_value=100_000, risk_percent=0.5)

    assert _gates(result) == {"DATA": "PASS", "TRADE_STRUCTURE": "PASS", "STOP_VS_NOISE": "PASS",
                              "LIQUIDITY": "PASS", "RISK_BUDGET": "PASS"}
    assert "ready_to_trade" not in result and "confidence" not in result
    assert result["fundamental_evidence"]["level"] == "NONE"


def test_each_gate_fails_on_its_own_condition():
    db = _db(date.today() - timedelta(days=30))
    # Stop 2 below entry (inside ATR 4), target gives 1:1, and 5,000 shares is 50% of ADV.
    result = run_trade_check(db, "TST", entry=100, stop=98, targets=[102], portfolio_value=1_000_000, risk_percent=1)

    gates = _gates(result)
    assert gates["DATA"] == "FAIL"
    assert gates["TRADE_STRUCTURE"] == "FAIL"
    assert gates["STOP_VS_NOISE"] == "FAIL"
    assert gates["LIQUIDITY"] == "FAIL"


def test_unknown_ticker():
    with pytest.raises(LookupError):
        run_trade_check(_db(date.today()), "NOPE", 100, 95, [110], 100_000, 1)
