"""Verifies actual recent trading activity for every seeded security, via a short-window
psxdata.stocks() pull -- psxdata's own symbol table (seed_identity.seed_full_market's source)
includes stale entries PSX hasn't purged, so a symbol existing there is not proof it's still
trading (already confirmed for FFBL/ENGRO, see mark_delisted_securities.py).

This check is deliberately weaker than mark_delisted_securities.py: it has no corporate-action
evidence (no merger/delisting notice tied to a SourceDocument), just an absence of recent bars --
so it marks listing_status="no_recent_trading" rather than "delisted", and never overwrites an
already-confirmed "delisted" status. Non-destructive like that script: never deletes history,
only flips is_active/listing_status, and re-activates a symbol if trading resumes on a later run.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import psxdata
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Security

logger = logging.getLogger(__name__)

# 90 days: long enough that a real (even thinly-traded) listed company should show at least one
# print, short enough to run in reasonable time across the full universe. A fetch failure (network
# error, symbol suspended from the endpoint, etc.) is NOT treated as evidence of inactivity --
# defaults to "leave it active" rather than punishing a transient scrape failure.
def _has_recent_trades(symbol: str, days: int = 90) -> bool:
    end = date.today()
    start = end - timedelta(days=days)
    try:
        bars = psxdata.stocks(symbol, start=start.isoformat(), end=end.isoformat())
    except Exception as exc:
        logger.warning("psxdata.stocks failed for %s: %s", symbol, exc)
        return True
    return bars is not None and len(bars) > 0


def verify_active_listings(
    db: Session, securities: list[Security] | None = None, max_workers: int = 10
) -> dict[str, str]:
    if securities is None:
        securities = list(db.execute(select(Security)).scalars().all())

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        active_flags = list(pool.map(lambda s: _has_recent_trades(s.symbol), securities))

    results: dict[str, str] = {}
    for security, is_active_now in zip(securities, active_flags):
        if security.listing_status == "delisted":
            # Confirmed via real corporate-action evidence elsewhere -- this weaker check
            # doesn't get to override that either way.
            results[security.symbol] = "already delisted (confirmed, skipped)"
            continue

        if is_active_now:
            if security.listing_status == "no_recent_trading":
                security.listing_status = "listed"
                security.is_active = True
                results[security.symbol] = "reactivated"
            else:
                results[security.symbol] = "active"
        else:
            security.listing_status = "no_recent_trading"
            security.is_active = False
            results[security.symbol] = "marked no_recent_trading"

    db.commit()
    return results


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        summary = verify_active_listings(session)
        counts: dict[str, int] = {}
        for outcome in summary.values():
            counts[outcome] = counts.get(outcome, 0) + 1
        print("Outcome counts:", counts)
        no_recent = [sym for sym, v in summary.items() if v == "marked no_recent_trading"]
        print(f"\n{len(no_recent)} symbols marked no_recent_trading:")
        print(no_recent)
