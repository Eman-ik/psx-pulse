"""Tests for scripts/audit_price_discontinuities.py's detection logic -- the same
checks that found the MARI/LUCK/KOHC/BERG-class problems this session, now pinned
down with synthetic fixtures so a future change to the thresholds or the OHLC-
violation logic can't silently stop catching what it used to catch.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from audit_price_discontinuities import audit_security  # noqa: E402


def _frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    for col in ("open", "high", "low", "close"):
        if col not in df.columns:
            df[col] = df["close"] if "close" in df.columns else 100.0
    if "volume" not in df.columns:
        df["volume"] = 1000
    return df


def _clean_series(start_price: float, n: int, start_date: str = "2026-01-01") -> list[dict]:
    dates = pd.bdate_range(start=start_date, periods=n)
    return [
        {"trade_date": d, "open": start_price, "high": start_price, "low": start_price, "close": start_price, "volume": 1000}
        for d in dates
    ]


def test_no_findings_for_a_flat_clean_series():
    df = _frame(_clean_series(100.0, 30))
    findings = audit_security("TEST", df)
    assert findings["large_moves"] == []
    assert findings["ohlc_violations"] == []
    assert findings["volume_spikes"] == []
    assert findings["gaps"] == []


def test_flags_a_severe_move_and_classifies_a_clean_split_ratio():
    rows = _clean_series(100.0, 5)
    # KOHC-shaped 5-for-1 split: ratio 0.2, day-over-day.
    rows.append({"trade_date": pd.Timestamp("2026-01-08"), "open": 20.0, "high": 20.0, "low": 20.0, "close": 20.0, "volume": 1000})
    df = _frame(rows)

    findings = audit_security("TEST", df)

    assert len(findings["large_moves"]) == 1
    move = findings["large_moves"][0]
    assert move["severity"] == "SEVERE"
    assert "5-for-1 split" in move["classification_hint"]


def test_moderate_move_below_50pct_is_not_severe():
    rows = _clean_series(100.0, 5)
    rows.append({"trade_date": pd.Timestamp("2026-01-08"), "open": 75.0, "high": 75.0, "low": 75.0, "close": 75.0, "volume": 1000})
    df = _frame(rows)

    findings = audit_security("TEST", df)

    assert len(findings["large_moves"]) == 1
    assert findings["large_moves"][0]["severity"] == "moderate"


def test_move_below_20pct_threshold_is_not_flagged_at_all():
    rows = _clean_series(100.0, 5)
    rows.append({"trade_date": pd.Timestamp("2026-01-08"), "open": 90.0, "high": 90.0, "low": 90.0, "close": 90.0, "volume": 1000})
    df = _frame(rows)

    findings = audit_security("TEST", df)

    assert findings["large_moves"] == []


@pytest.mark.parametrize(
    "bad_bar",
    [
        {"open": 100.0, "high": 90.0, "low": 80.0, "close": 95.0},  # high < open
        {"open": 100.0, "high": 110.0, "low": 105.0, "close": 95.0},  # low > close
        {"open": 100.0, "high": 90.0, "low": 95.0, "close": 92.0},  # high < low
        {"open": -5.0, "high": 10.0, "low": -5.0, "close": 5.0},  # non-positive price
    ],
)
def test_detects_impossible_ohlc_relationships(bad_bar):
    rows = _clean_series(100.0, 5)
    bad_row = {"trade_date": pd.Timestamp("2026-01-08"), "volume": 1000, **bad_bar}
    rows.append(bad_row)
    df = _frame(rows)

    findings = audit_security("TEST", df)

    assert len(findings["ohlc_violations"]) == 1


def test_detects_volume_spike_far_above_trailing_average():
    # The volume check only activates with > 30 non-null volume rows (audit_security's
    # own threshold), so this needs more history than the other fixtures here.
    rows = _clean_series(100.0, 35)
    for r in rows:
        r["volume"] = 1000
    rows.append({"trade_date": pd.bdate_range("2026-01-01", periods=36)[-1], "open": 100, "high": 100, "low": 100, "close": 100, "volume": 50000})
    df = _frame(rows)

    findings = audit_security("TEST", df)

    assert len(findings["volume_spikes"]) == 1
    assert findings["volume_spikes"][0]["multiple"] >= 8.0


def test_detects_a_trading_gap_of_15_or_more_calendar_days():
    rows = _clean_series(100.0, 5, start_date="2026-01-01")
    # Jump straight to a date 20 calendar days after the last bar.
    rows.append({"trade_date": pd.Timestamp("2026-01-28"), "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1000})
    df = _frame(rows)

    findings = audit_security("TEST", df)

    assert len(findings["gaps"]) == 1
    assert findings["gaps"][0]["calendar_days"] >= 15


def test_gap_shorter_than_threshold_is_not_flagged():
    rows = _clean_series(100.0, 5, start_date="2026-01-01")  # ends on a Friday-ish weekday
    last_date = rows[-1]["trade_date"]
    rows.append({"trade_date": last_date + pd.Timedelta(days=5), "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1000})
    df = _frame(rows)

    findings = audit_security("TEST", df)

    assert findings["gaps"] == []
