"""Historical universe reconstruction — what was investable on any given date.

For backtesting, we need to know: on date X, which securities existed, which
had price data, and which had fundamental coverage? This service answers that.
"""

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import and_, select, func
from sqlalchemy.orm import Session

from app.db.models import Security, FinancialFact, PriceOHLCV, Issuer, Sector


def historical_universe(
    db: Session,
    as_of_date: date,
    min_price_bars: int = 1,
    min_financial_facts: int = 1,
    sector_name: Optional[str] = None,
) -> dict:
    """Get the investable universe as it was known on a specific date.

    Args:
        db: Database session
        as_of_date: Query date (securities must be listed on or before this)
        min_price_bars: Minimum number of price records required to count as "price_covered"
        min_financial_facts: Minimum financial facts required to count as "fundamentals_covered"
        sector_name: Filter to a specific sector (e.g., "Fertilizer"), or None for all

    Returns:
        Dict with:
        - as_of_date: Query date
        - total_count: All active securities on this date
        - price_covered: Count with 1+ price bars
        - fundamentals_covered: Count with 1+ published facts
        - by_sector: Breakdown by sector
        - securities: List of {symbol, name, sector, price_coverage, fundamentals_coverage, issuer_id}
        - coverage_summary: Overall statistics
    """

    # Get all securities that were listed by as_of_date (listing_date <= as_of_date or null)
    base_filters = [
        Security.is_active.is_(True),
        (Security.listing_date.is_(None)) | (Security.listing_date <= as_of_date),
    ]

    securities_query = select(Security).where(and_(*base_filters)).order_by(Security.symbol)

    if sector_name:
        securities_query = securities_query.join(Issuer).join(Sector).where(
            Sector.name == sector_name
        )

    securities = db.execute(securities_query).scalars().all()

    # Build coverage map for efficiency
    price_coverage_query = (
        select(
            PriceOHLCV.security_id,
            func.count(PriceOHLCV.id).label("count"),
        )
        .where(PriceOHLCV.trade_date <= as_of_date)
        .group_by(PriceOHLCV.security_id)
    )
    price_coverage = {
        row[0]: row[1]
        for row in db.execute(price_coverage_query).all()
    }

    fundamentals_coverage_query = (
        select(
            FinancialFact.issuer_id,
            func.count(FinancialFact.id).label("count"),
        )
        .where(
            and_(
                FinancialFact.published_at.isnot(None),
                FinancialFact.published_at <= datetime.combine(as_of_date, time(23, 59, 59)),
                FinancialFact.superseded_by_id.is_(None),  # Only latest version
            )
        )
        .group_by(FinancialFact.issuer_id)
    )
    fundamentals_coverage = {
        row[0]: row[1]
        for row in db.execute(fundamentals_coverage_query).all()
    }

    # Build response
    securities_list = []
    price_covered_count = 0
    fundamentals_covered_count = 0
    sector_stats = {}

    for security in securities:
        price_bars = price_coverage.get(security.id, 0)
        fundamental_facts = fundamentals_coverage.get(security.issuer_id, 0)

        has_price_coverage = price_bars >= min_price_bars
        has_fundamentals_coverage = fundamental_facts >= min_financial_facts

        if has_price_coverage:
            price_covered_count += 1
        if has_fundamentals_coverage:
            fundamentals_covered_count += 1

        # Update sector stats
        sector_name_actual = security.issuer.sector.name if security.issuer.sector else "Uncategorized"
        if sector_name_actual not in sector_stats:
            sector_stats[sector_name_actual] = {
                "total": 0,
                "price_covered": 0,
                "fundamentals_covered": 0,
            }
        sector_stats[sector_name_actual]["total"] += 1
        if has_price_coverage:
            sector_stats[sector_name_actual]["price_covered"] += 1
        if has_fundamentals_coverage:
            sector_stats[sector_name_actual]["fundamentals_covered"] += 1

        securities_list.append(
            {
                "symbol": security.symbol,
                "name": security.issuer.name,
                "sector": sector_name_actual,
                "issuer_id": security.issuer_id,
                "listing_date": security.listing_date.isoformat() if security.listing_date else None,
                "price_coverage": {
                    "available": has_price_coverage,
                    "bars_count": price_bars,
                    "meets_minimum": has_price_coverage,
                },
                "fundamentals_coverage": {
                    "available": has_fundamentals_coverage,
                    "facts_count": fundamental_facts,
                    "meets_minimum": has_fundamentals_coverage,
                },
            }
        )

    return {
        "as_of_date": as_of_date.isoformat(),
        "total_count": len(securities),
        "price_covered_count": price_covered_count,
        "fundamentals_covered_count": fundamentals_covered_count,
        "coverage_summary": {
            "price_coverage_pct": (price_covered_count / len(securities) * 100) if securities else 0,
            "fundamentals_coverage_pct": (fundamentals_covered_count / len(securities) * 100) if securities else 0,
            "fully_covered_count": sum(
                1 for s in securities_list
                if s["price_coverage"]["available"] and s["fundamentals_coverage"]["available"]
            ),
        },
        "by_sector": sector_stats,
        "securities": securities_list,
    }


def universe_timeline(
    db: Session,
    start_date: date,
    end_date: date,
    sample_interval_days: int = 30,
) -> dict:
    """Get historical universe snapshots at regular intervals.

    Useful for understanding how coverage evolved over time.

    Args:
        db: Database session
        start_date: Timeline start
        end_date: Timeline end
        sample_interval_days: Snapshot every N days

    Returns:
        Dict with timeline snapshots and summary statistics
    """
    from datetime import timedelta

    snapshots = []
    current = start_date

    while current <= end_date:
        snapshot = historical_universe(db, current)
        snapshots.append(snapshot)
        current += timedelta(days=sample_interval_days)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "sample_interval_days": sample_interval_days,
        "snapshots_count": len(snapshots),
        "snapshots": snapshots,
        "summary": {
            "min_total_count": min(s["total_count"] for s in snapshots) if snapshots else 0,
            "max_total_count": max(s["total_count"] for s in snapshots) if snapshots else 0,
            "min_price_coverage_pct": min(
                s["coverage_summary"]["price_coverage_pct"] for s in snapshots
            ) if snapshots else 0,
            "max_price_coverage_pct": max(
                s["coverage_summary"]["price_coverage_pct"] for s in snapshots
            ) if snapshots else 0,
            "min_fundamentals_coverage_pct": min(
                s["coverage_summary"]["fundamentals_coverage_pct"] for s in snapshots
            ) if snapshots else 0,
            "max_fundamentals_coverage_pct": max(
                s["coverage_summary"]["fundamentals_coverage_pct"] for s in snapshots
            ) if snapshots else 0,
        },
    }
