"""Point-in-time historical financial facts service.

Queries financial facts as they were known on a specific date.
Respects publication dates and corrects/restated facts.
"""

from datetime import date, datetime, time, timezone
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.db.models import FinancialFact, Issuer, Security


def get_financials_as_of(
    db: Session,
    symbol: str,
    as_of_date: date,
    period_type: Optional[str] = None,
    scope: str = "standalone",
) -> dict:
    """Get financial facts as they were known on a specific date.

    Args:
        db: Database session
        symbol: Ticker symbol
        as_of_date: Date to query financials as-of (published_at <= as_of_date)
        period_type: Filter by period type (annual/half_year/quarterly/ttm), or None for all
        scope: Filter by scope (standalone/consolidated)

    Returns:
        Dict with:
        - symbol: Ticker symbol
        - as_of_date: Query date
        - count: Number of facts returned
        - facts: List of {line_item, period_end, value, period_type, published_at, is_restated}
        - error: Error message if lookup failed
    """
    # Resolve ticker to issuer_id
    security = db.execute(
        select(Security).where(Security.symbol == symbol.upper(), Security.is_active.is_(True))
    ).scalar_one_or_none()

    if not security:
        return {
            "symbol": symbol.upper(),
            "as_of_date": as_of_date.isoformat(),
            "count": 0,
            "facts": [],
            "error": f"No active security found for {symbol.upper()}",
        }

    issuer_id = security.issuer_id

    # Build query: facts known as of as_of_date (published_at <= as_of_date)
    # Exclude facts that are superseded
    filters = [
        FinancialFact.issuer_id == issuer_id,
        FinancialFact.published_at <= datetime.combine(as_of_date, time(23, 59, 59)),
        FinancialFact.superseded_by_id.is_(None),  # Only latest version of each fact
        FinancialFact.scope == scope,
    ]

    if period_type:
        filters.append(FinancialFact.period_type == period_type)

    query = select(FinancialFact).where(and_(*filters)).order_by(
        FinancialFact.period_end.desc(), FinancialFact.line_item
    )

    facts = db.execute(query).scalars().all()

    return {
        "symbol": symbol.upper(),
        "as_of_date": as_of_date.isoformat(),
        "issuer_id": issuer_id,
        "count": len(facts),
        "facts": [
            {
                "line_item": f.line_item,
                "period_end": f.period_end.isoformat(),
                "period_start": f.period_start.isoformat(),
                "period_type": f.period_type,
                "value": float(f.value),
                "unit": f.unit,
                "scope": f.scope,
                "published_at": f.published_at.isoformat() if f.published_at else None,
                "is_restated": f.is_restated,
            }
            for f in facts
        ],
    }


def get_financials_series(
    db: Session,
    symbol: str,
    line_item: str,
    scope: str = "standalone",
) -> dict:
    """Get time series of a single line item (raw, unfiltered by as-of date).

    Useful for historical analysis of when numbers changed.

    Args:
        db: Database session
        symbol: Ticker symbol
        line_item: Canonical line item key (e.g. revenue, profit_after_tax)
        scope: Filter by scope (standalone/consolidated)

    Returns:
        Dict with symbol, line_item, and list of {period_end, value, published_at, is_restated}
    """
    security = db.execute(
        select(Security).where(Security.symbol == symbol.upper(), Security.is_active.is_(True))
    ).scalar_one_or_none()

    if not security:
        return {
            "symbol": symbol.upper(),
            "line_item": line_item,
            "series": [],
            "error": f"No active security found for {symbol.upper()}",
        }

    issuer_id = security.issuer_id

    # Get all versions of this line item (including superseded)
    query = (
        select(FinancialFact)
        .where(
            FinancialFact.issuer_id == issuer_id,
            FinancialFact.line_item == line_item,
            FinancialFact.scope == scope,
        )
        .order_by(FinancialFact.period_end.desc(), FinancialFact.created_at.desc())
    )

    facts = db.execute(query).scalars().all()

    return {
        "symbol": symbol.upper(),
        "issuer_id": issuer_id,
        "line_item": line_item,
        "scope": scope,
        "count": len(facts),
        "series": [
            {
                "period_end": f.period_end.isoformat(),
                "value": float(f.value),
                "published_at": f.published_at.isoformat() if f.published_at else None,
                "is_restated": f.is_restated,
                "superseded": f.superseded_by_id is not None,
            }
            for f in facts
        ],
    }
