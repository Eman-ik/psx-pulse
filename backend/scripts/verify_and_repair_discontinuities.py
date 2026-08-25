"""Resolves every symbol flagged by audit_price_discontinuities.py's clean-ratio-match
buckets (14 repeating-pattern + 21 one-off = 35 symbols) into one of two outcomes,
by re-fetching fresh data from psxdata and comparing against what's stored:

  - REPAIRED: fresh data disagrees with stored data for the flagged dates -- this is
    corrupted rows (confirmed root cause for BERG: a fresh pull returns a smooth,
    sensible series with zero trace of the wild stored values -- see the 2023-09
    investigation this script's classification is based on). Fresh values overwrite
    the stored ones.

  - CANDIDATE: fresh data confirms the stored jump -- this is a real, unadjusted price
    discontinuity (confirmed for KOHC/MARI/LUCK the same way). Written to
    corporate_action as action_type="split", verified=False -- "unverified" because an
    algorithmic detector confirming its own prior scrape isn't the same as cross-
    checking against an actual PSX announcement (source_document_id stays null). Never
    silently trusted as fully verified.

  - UNRESOLVED: fresh psxdata returns nothing for the flagged range (e.g. a since-
    delisted symbol) -- can't be checked this way. Left untouched, reported separately.

Never deletes anything; every row that gets its price data changed is overwritten with
psxdata's own current values, not synthesized.

Run with: backend/.venv/Scripts/python.exe scripts/verify_and_repair_discontinuities.py
"""

import json
from datetime import timedelta
from pathlib import Path

import psxdata
from sqlalchemy import select

from app.db.models import CorporateAction, PriceOHLCV, Security
from app.db.session import SessionLocal

TOLERANCE = 0.02  # 2% -- fresh vs stored close must agree within this to call it "confirmed"


def resolve_symbol(db, symbol: str, findings: dict) -> dict:
    security_id = db.execute(select(Security.id).where(Security.symbol == symbol)).scalar()
    if security_id is None:
        return {"symbol": symbol, "outcome": "UNRESOLVED", "reason": "security not found"}

    dates_involved = sorted({m["date"][:10] for m in findings["large_moves"] if m["severity"] == "SEVERE"})
    if not dates_involved:
        return {"symbol": symbol, "outcome": "UNRESOLVED", "reason": "no severe moves"}

    # Full stored history, not a narrow window around the flagged dates -- a ±30-day
    # window around MARI's one flagged date missed 1,272 further corrupted rows
    # stretching back to 2016 that a full-history compare caught. psxdata itself often
    # doesn't go back as far as what's stored (confirmed for MARI: fresh data starts
    # 2016-08-04, stored starts 2005-01-03) -- that earlier, unverifiable stretch is a
    # real, separate limitation, not something a wider window request can fix.
    all_stored_dates = db.execute(
        select(PriceOHLCV.trade_date).where(PriceOHLCV.security_id == security_id).order_by(PriceOHLCV.trade_date)
    ).scalars().all()
    if not all_stored_dates:
        return {"symbol": symbol, "outcome": "UNRESOLVED", "reason": "no stored price history"}
    window_start = all_stored_dates[0]
    window_end = all_stored_dates[-1]

    fresh = psxdata.stocks(symbol, start=window_start.isoformat(), end=window_end.isoformat())
    if fresh is None or len(fresh) == 0:
        return {"symbol": symbol, "outcome": "UNRESOLVED", "reason": "psxdata returned no data for this window"}

    fresh_by_date = {}
    for _, row in fresh.iterrows():
        d = row["date"].date() if hasattr(row["date"], "date") else row["date"]
        fresh_by_date[d] = row

    stored_rows = {
        r.trade_date: r
        for r in db.execute(
            select(PriceOHLCV).where(
                PriceOHLCV.security_id == security_id,
                PriceOHLCV.trade_date >= window_start,
                PriceOHLCV.trade_date <= window_end,
            )
        ).scalars().all()
    }

    disagreements = []
    for d, stored in stored_rows.items():
        if d not in fresh_by_date:
            continue
        fresh_close = float(fresh_by_date[d]["close"])
        stored_close = float(stored.close)
        if stored_close <= 0:
            continue
        if abs(fresh_close - stored_close) / stored_close > TOLERANCE:
            disagreements.append({
                "date": str(d), "stored_close": stored_close, "fresh_close": fresh_close,
            })

    if disagreements:
        for d, stored in stored_rows.items():
            if d not in fresh_by_date:
                continue
            row = fresh_by_date[d]
            stored.open = float(row["open"])
            stored.high = float(row["high"])
            stored.low = float(row["low"])
            stored.close = float(row["close"])
            stored.volume = int(row["volume"]) if row["volume"] == row["volume"] else None
        db.commit()
        return {
            "symbol": symbol, "outcome": "REPAIRED",
            "rows_overwritten": len(disagreements),
            "sample_disagreements": disagreements[:5],
        }

    # Fresh data confirms every stored value in the window -- every clean-ratio-match
    # move in it is a real, confirmed event (a symbol can have had more than one).
    clean_moves = [
        m for m in findings["large_moves"]
        if m["severity"] == "SEVERE" and "looks like" in m["classification_hint"]
        and pd_to_date(m["date"][:10]) >= window_start and pd_to_date(m["date"][:10]) <= window_end
    ]
    created = []
    for m in clean_moves:
        effective_date = pd_to_date(m["date"][:10])
        ratio = round(m["close"] / m["prev_close"], 4)
        existing = db.execute(
            select(CorporateAction).where(
                CorporateAction.security_id == security_id, CorporateAction.effective_date == effective_date
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(CorporateAction(
                security_id=security_id, action_type="split", effective_date=effective_date,
                ratio_or_amount=ratio, currency=None, source_document_id=None, verified=False,
            ))
            created.append({"effective_date": str(effective_date), "ratio": ratio, "hint": m["classification_hint"]})
    db.commit()
    return {"symbol": symbol, "outcome": "CANDIDATE", "events": created}


def pd_to_date(s: str):
    from datetime import date as _date
    y, m, d = s.split("-")
    return _date(int(y), int(m), int(d))


def main() -> None:
    import sys
    report = json.loads(Path("scripts/price_discontinuity_report.json").read_text())
    from collections import Counter
    # Every symbol with at least one SEVERE (>=50%) move -- not just the ones whose move
    # happens to match a clean split ratio. A "no clean ratio match" severe move still
    # needs the same fresh-data cross-check: it might be corrupted rows (repaired, same
    # as the clean-ratio cases), or a real move with no clean-ratio classification
    # (confirmed-real, left alone -- resolve_symbol's CANDIDATE path only creates a
    # corporate_action row for a clean-ratio match, never fabricates one for an
    # unclassified move). Narrowing this to clean-ratio-only earlier was an artificial
    # scope cut for a first pass, not a real boundary on what needed checking.
    target_symbols = set()
    for symbol, findings in report.items():
        if any(m["severity"] == "SEVERE" for m in findings["large_moves"]):
            target_symbols.add(symbol)

    # Optional: python verify_and_repair_discontinuities.py SYM1 SYM2 ... to run only
    # specific symbols (e.g. resuming after an interrupted run, or re-checking one name).
    if len(sys.argv) > 1:
        target_symbols &= set(sys.argv[1:])

    print(f"Resolving {len(target_symbols)} flagged symbols...\n")
    results = []
    with SessionLocal() as db:
        for symbol in sorted(target_symbols):
            try:
                result = resolve_symbol(db, symbol, report[symbol])
            except Exception as exc:
                db.rollback()
                result = {"symbol": symbol, "outcome": "ERROR", "reason": str(exc)}
            results.append(result)
            print(f"  {symbol}: {result['outcome']}" + (f" -- {result.get('reason', '')}" if result['outcome'] in ('UNRESOLVED', 'ERROR') else ''))

    # Merge into (not overwrite) any prior run's results -- this script gets rerun in
    # batches (see the sys.argv filter above), and each run's own record is worth
    # keeping, not just the last one's.
    report_path = Path("scripts/discontinuity_resolution_report.json")
    prior = json.loads(report_path.read_text()) if report_path.exists() else []
    merged = {r["symbol"]: r for r in prior}
    merged.update({r["symbol"]: r for r in results})
    report_path.write_text(json.dumps(list(merged.values()), indent=2))

    outcomes = Counter(r["outcome"] for r in results)
    print(f"\nThis run: {dict(outcomes)}")
    print(f"All runs combined: {dict(Counter(r['outcome'] for r in merged.values()))}")
    print(f"Saved to {report_path}")


if __name__ == "__main__":
    main()
