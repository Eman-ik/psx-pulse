"""Data-quality audit across every security with price history, not just MARI/LUCK.

MARI and LUCK had real, unrecorded stock splits sitting in raw price_ohlcv that
silently corrupted every Kronos forecast touching them, discovered only by
noticing an 80%+ single-day "return" while investigating something else.
corporate_action has 0 rows -- nothing has ever been systematically checked for
this across the other 270+ securities with price history. This script does that
check.

Read-only: flags candidates for human review, never writes to corporate_action
or price_ohlcv. That table's own docstring is explicit -- "price adjustment must
derive from this, not be hardcoded" -- and a real corporate-action record needs
a verifiable source (source_document_id), which an algorithmic detector can't
supply on its own. Auto-inserting unverified guesses would be exactly the kind
of silent, unaccountable data corruption this audit exists to catch.

Flags, per the four checks below:
  - Large single-day moves (>=20%, >=50%) in close price -- the MARI/LUCK pattern.
    Each is checked against clean split/reverse-split ratios (1:2, 1:3, 2:1, etc.)
    for a classification hint, but every one still needs human confirmation
    against a real corporate announcement before being trusted.
  - Impossible OHLC relationships (high < low, high/low outside [min,max](open,close), non-positive prices).
  - Abnormal volume (>= 8x the trailing 20-session average).
  - Trading gaps (>= 15 consecutive calendar days between bars with no explanation
    on file) -- suspensions, delistings, or just missing data, all worth knowing about.

Run with: backend/.venv/Scripts/python.exe scripts/audit_price_discontinuities.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import select

from app.db.models import PriceOHLCV, Security
from app.db.session import SessionLocal

LARGE_MOVE_THRESHOLD = 0.20
SEVERE_MOVE_THRESHOLD = 0.50
VOLUME_SPIKE_MULTIPLE = 8.0
GAP_DAYS_THRESHOLD = 15

# Common split/reverse-split/bonus ratios, as the (post/pre) close-price multiplier
# they'd produce if genuinely a corporate action and not a real market move.
_KNOWN_RATIOS = {
    "2-for-1 split": 0.5, "3-for-1 split": 1 / 3, "3-for-2 split": 2 / 3,
    "4-for-1 split": 0.25, "5-for-1 split": 0.2, "10-for-1 split": 0.1,
    "1-for-2 reverse split": 2.0, "1-for-3 reverse split": 3.0,
    "1-for-4 reverse split": 4.0, "1-for-5 reverse split": 5.0, "1-for-10 reverse split": 10.0,
    "20% bonus issue": 1 / 1.2, "50% bonus issue": 1 / 1.5, "100% bonus issue": 0.5,
}


def _classify_jump(ratio: float) -> str:
    for label, expected in _KNOWN_RATIOS.items():
        if abs(ratio - expected) / expected < 0.05:  # within 5% of a clean ratio
            return f"looks like {label} (ratio {ratio:.3f} vs expected {expected:.3f})"
    return "no clean ratio match -- could be a real move, an unlisted action, or a data error"


def audit_security(symbol: str, df: pd.DataFrame) -> dict:
    df = df.sort_values("trade_date").reset_index(drop=True)
    findings: dict[str, list] = {"large_moves": [], "ohlc_violations": [], "volume_spikes": [], "gaps": []}

    prev_close = df["close"].shift(1)
    pct_change = (df["close"] - prev_close) / prev_close
    for i in range(1, len(df)):
        if pd.isna(pct_change.iloc[i]):
            continue
        pc = pct_change.iloc[i]
        if abs(pc) >= LARGE_MOVE_THRESHOLD:
            ratio = df["close"].iloc[i] / prev_close.iloc[i]
            findings["large_moves"].append({
                "date": str(df["trade_date"].iloc[i]),
                "prev_close": float(prev_close.iloc[i]),
                "close": float(df["close"].iloc[i]),
                "pct_change": round(float(pc) * 100, 2),
                "severity": "SEVERE" if abs(pc) >= SEVERE_MOVE_THRESHOLD else "moderate",
                "classification_hint": _classify_jump(ratio),
            })

    row_max = df[["open", "close"]].max(axis=1)
    row_min = df[["open", "close"]].min(axis=1)
    bad_ohlc = df[
        (df["high"] < df["low"])
        | (df["high"] < row_max)
        | (df["low"] > row_min)
        | (df[["open", "high", "low", "close"]] <= 0).any(axis=1)
    ]
    for _, row in bad_ohlc.iterrows():
        findings["ohlc_violations"].append({
            "date": str(row["trade_date"]), "open": float(row["open"]), "high": float(row["high"]),
            "low": float(row["low"]), "close": float(row["close"]),
        })

    if df["volume"].notna().sum() > 30:
        vol_avg20 = df["volume"].rolling(20, min_periods=10).mean().shift(1)
        spikes = df[(df["volume"] > vol_avg20 * VOLUME_SPIKE_MULTIPLE) & vol_avg20.notna() & (vol_avg20 > 0)]
        for idx, row in spikes.iterrows():
            findings["volume_spikes"].append({
                "date": str(row["trade_date"]), "volume": int(row["volume"]),
                "trailing_20d_avg": round(float(vol_avg20.loc[idx]), 0),
                "multiple": round(float(row["volume"] / vol_avg20.loc[idx]), 1),
            })

    gap_days = df["trade_date"].diff().dt.days
    gaps = df[gap_days >= GAP_DAYS_THRESHOLD]
    for idx, row in gaps.iterrows():
        findings["gaps"].append({
            "gap_start": str(df["trade_date"].iloc[idx - 1]), "gap_end": str(row["trade_date"]),
            "calendar_days": int(gap_days.loc[idx]),
        })

    return findings


def main() -> None:
    with SessionLocal() as db:
        rows = db.execute(
            select(
                Security.symbol, PriceOHLCV.trade_date, PriceOHLCV.open,
                PriceOHLCV.high, PriceOHLCV.low, PriceOHLCV.close, PriceOHLCV.volume,
            ).join(Security, Security.id == PriceOHLCV.security_id)
        ).all()

    df = pd.DataFrame(rows, columns=["symbol", "trade_date", "open", "high", "low", "close", "volume"])
    for col in ("open", "high", "low", "close"):
        df[col] = df[col].astype(float)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    n_symbols = df["symbol"].nunique()
    print(f"Auditing {n_symbols} securities, {len(df)} total bars...\n")

    report: dict[str, dict] = {}
    flagged_symbols = 0
    severe_symbols = []
    for symbol, g in df.groupby("symbol", sort=True):
        if len(g) < 5:
            continue
        findings = audit_security(symbol, g)
        if any(findings.values()):
            report[symbol] = findings
            flagged_symbols += 1
            if any(m["severity"] == "SEVERE" for m in findings["large_moves"]):
                severe_symbols.append(symbol)

    out_path = Path("scripts/price_discontinuity_report.json")
    out_path.write_text(json.dumps(report, indent=2))

    print(f"{flagged_symbols} of {n_symbols} securities have at least one flagged finding.")
    print(f"{len(severe_symbols)} have a SEVERE (>=50%) single-day move: {', '.join(sorted(severe_symbols))}\n")

    print("=== SEVERE large moves (>=50% single-day) ===")
    for symbol in sorted(severe_symbols):
        for m in report[symbol]["large_moves"]:
            if m["severity"] == "SEVERE":
                print(f"  {symbol} {m['date']}: {m['prev_close']:.2f} -> {m['close']:.2f} "
                      f"({m['pct_change']:+.1f}%) -- {m['classification_hint']}")

    print(f"\nFull report (all categories, all flagged symbols) saved to {out_path}")


if __name__ == "__main__":
    main()
