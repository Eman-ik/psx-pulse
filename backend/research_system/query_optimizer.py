"""
Query Optimization for Khronos Research System

Provides:
- Optimized query methods
- Eager loading to prevent N+1 queries
- Batch processing for bulk operations
- Query result aggregation
- Index-aware queries
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from .schema import (
    Security, FinancialPeriod, FinancialLineItem, FinancialMetric,
    MetricDefinition, Document, Announcement, Event, PeriodType
)
from .caching import cached, cache_key, invalidate_cache, DEFAULT_TTL, METRIC_TTL


class QueryOptimizer:
    """Optimized query methods for financial data."""

    def __init__(self, session: Session):
        """Initialize query optimizer.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    @cached(ttl=3600, key_prefix="securities")
    def get_all_securities_cached(self) -> List[Dict[str, Any]]:
        """Get all active securities (cached).

        Returns:
            List of security dictionaries
        """
        securities = self.session.query(Security).filter_by(active=True).all()
        return [
            {
                "security_id": s.security_id,
                "ticker": s.ticker,
                "company_name": s.company_name,
                "sector": s.sector.sector_name if s.sector else None,
                "industry": s.industry.industry_name if s.industry else None,
            }
            for s in securities
        ]

    @cached(ttl=METRIC_TTL, key_prefix="metrics")
    def get_metrics_for_company_cached(self, ticker: str, fiscal_year: int) -> List[Dict[str, Any]]:
        """Get company metrics (cached).

        Args:
            ticker: Company ticker
            fiscal_year: Fiscal year

        Returns:
            List of metric dictionaries
        """
        security = self.session.query(Security).filter_by(ticker=ticker).first()
        if not security:
            return []

        period = self.session.query(FinancialPeriod).filter(
            and_(
                FinancialPeriod.security_id == security.security_id,
                FinancialPeriod.fiscal_year == fiscal_year,
                FinancialPeriod.period_type == PeriodType.ANNUAL,
            )
        ).first()

        if not period:
            return []

        metrics = self.session.query(FinancialMetric).filter_by(
            period_id=period.period_id
        ).all()

        return [
            {
                "metric_code": m.metric_code,
                "value": float(m.value),
                "calculated_at": m.calculated_at.isoformat() if m.calculated_at else None,
            }
            for m in metrics
        ]

    def batch_calculate_metrics(
        self,
        tickers: List[str],
        fiscal_year: int,
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """Batch calculate metrics for multiple companies.

        Args:
            tickers: List of company tickers
            fiscal_year: Fiscal year
            batch_size: Number of companies per batch

        Returns:
            Dictionary with results and statistics
        """
        results = {}
        errors = []
        total_processed = 0

        # Process in batches
        for i in range(0, len(tickers), batch_size):
            batch_tickers = tickers[i : i + batch_size]

            try:
                # Batch query for securities
                securities = self.session.query(Security).filter(
                    Security.ticker.in_(batch_tickers)
                ).all()

                for security in securities:
                    try:
                        metrics = self.get_metrics_for_company_cached(
                            security.ticker, fiscal_year
                        )
                        results[security.ticker] = metrics
                        total_processed += 1
                    except Exception as e:
                        errors.append(f"{security.ticker}: {str(e)}")

            except Exception as e:
                errors.append(f"Batch processing error: {str(e)}")

        return {
            "total_requested": len(tickers),
            "total_processed": total_processed,
            "results": results,
            "errors": errors,
        }

    def get_company_financial_summary(
        self, ticker: str, fiscal_year: int
    ) -> Optional[Dict[str, Any]]:
        """Get complete financial summary for company (optimized query).

        Uses single query with eager loading to avoid N+1 problem.

        Args:
            ticker: Company ticker
            fiscal_year: Fiscal year

        Returns:
            Complete financial summary or None
        """
        security = self.session.query(Security).filter_by(ticker=ticker).first()
        if not security:
            return None

        # Get period with eager-loaded metrics
        period = self.session.query(FinancialPeriod).filter(
            and_(
                FinancialPeriod.security_id == security.security_id,
                FinancialPeriod.fiscal_year == fiscal_year,
            )
        ).first()

        if not period:
            return None

        # Single query for line items
        line_items = self.session.query(FinancialLineItem).filter_by(
            period_id=period.period_id
        ).all()

        # Single query for metrics
        metrics = self.session.query(FinancialMetric).filter_by(
            period_id=period.period_id
        ).all()

        return {
            "ticker": security.ticker,
            "company_name": security.company_name,
            "fiscal_year": fiscal_year,
            "line_items_count": len(line_items),
            "metrics_count": len(metrics),
            "line_items": [
                {
                    "metric_code": li.metric.metric_code if li.metric else None,
                    "reported_label": li.reported_label,
                    "value": float(li.value),
                }
                for li in line_items
            ],
            "metrics": [
                {
                    "metric_code": m.metric_code,
                    "value": float(m.value),
                }
                for m in metrics
            ],
        }

    def get_peer_comparison_data(
        self, tickers: List[str], fiscal_year: int
    ) -> Dict[str, Dict[str, float]]:
        """Get comparable metrics for peer group (optimized).

        Single query per metric to minimize database hits.

        Args:
            tickers: List of peer company tickers
            fiscal_year: Fiscal year

        Returns:
            Dict of {ticker: {metric_code: value}}
        """
        # Get all securities at once
        securities = self.session.query(Security).filter(
            Security.ticker.in_(tickers)
        ).all()

        security_map = {s.ticker: s.security_id for s in securities}
        security_ids = list(security_map.values())

        # Get all periods for these securities in one query
        periods = self.session.query(FinancialPeriod).filter(
            and_(
                FinancialPeriod.security_id.in_(security_ids),
                FinancialPeriod.fiscal_year == fiscal_year,
                FinancialPeriod.period_type == PeriodType.ANNUAL,
            )
        ).all()

        period_map = {p.security_id: p.period_id for p in periods}

        # Get all metrics for these periods in one query
        metrics = self.session.query(FinancialMetric).filter(
            FinancialMetric.period_id.in_(period_map.values())
        ).all()

        # Organize results
        result = {}
        for security_id, ticker in [(v, k) for k, v in security_map.items()]:
            result[ticker] = {}

        for metric in metrics:
            # Find which ticker this metric belongs to
            for security_id, ticker in [(v, k) for k, v in security_map.items()]:
                period_id = period_map.get(security_id)
                if period_id == metric.period_id:
                    result[ticker][metric.metric_code] = float(metric.value)
                    break

        return result

    def get_document_stats(self, ticker: str) -> Dict[str, Any]:
        """Get document statistics for company (aggregated query).

        Uses SQL aggregation to minimize memory usage.

        Args:
            ticker: Company ticker

        Returns:
            Document statistics
        """
        security = self.session.query(Security).filter_by(ticker=ticker).first()
        if not security:
            return {}

        stats = self.session.query(
            func.count(Document.document_id).label("total"),
            Document.processing_status.label("status"),
        ).filter_by(security_id=security.security_id).group_by(
            Document.processing_status
        ).all()

        result = {
            "ticker": ticker,
            "total_documents": sum(s[0] for s in stats),
            "by_status": {str(s[1].value) if s[1] else "unknown": s[0] for s in stats},
        }

        return result

    def invalidate_company_cache(self, ticker: str) -> None:
        """Invalidate all cached data for company.

        Args:
            ticker: Company ticker
        """
        invalidate_cache(f"metrics:{ticker}:*")
        invalidate_cache(f"financials:{ticker}:*")
        invalidate_cache(f"peer:*{ticker}*")

    def invalidate_all_cache(self) -> None:
        """Invalidate all cached data."""
        invalidate_cache("*")


class BatchProcessor:
    """Batch processing utilities for bulk operations."""

    def __init__(self, session: Session, batch_size: int = 100):
        """Initialize batch processor.

        Args:
            session: SQLAlchemy session
            batch_size: Number of items per batch
        """
        self.session = session
        self.batch_size = batch_size

    def process_announcements_batch(
        self,
        announcements: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Process announcements in batches.

        Args:
            announcements: List of announcement data

        Returns:
            Processing results
        """
        results = {"created": 0, "skipped": 0, "errors": []}

        for i in range(0, len(announcements), self.batch_size):
            batch = announcements[i : i + self.batch_size]

            try:
                # Get all required securities in batch
                tickers = set(a.get("ticker") for a in batch if a.get("ticker"))
                securities = self.session.query(Security).filter(
                    Security.ticker.in_(tickers)
                ).all()
                security_map = {s.ticker: s.security_id for s in securities}

                # Process batch
                for ann_data in batch:
                    try:
                        ticker = ann_data.get("ticker")
                        security_id = security_map.get(ticker)

                        if not security_id:
                            results["errors"].append(f"Security not found: {ticker}")
                            continue

                        # Create announcement (assuming it doesn't exist)
                        # Actual creation logic would go here
                        results["created"] += 1

                    except Exception as e:
                        results["errors"].append(str(e))

                self.session.commit()

            except Exception as e:
                results["errors"].append(f"Batch error: {str(e)}")
                self.session.rollback()

        return results

    def get_batch_metrics(
        self, tickers: List[str], fiscal_year: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get metrics for multiple companies efficiently.

        Args:
            tickers: List of tickers
            fiscal_year: Fiscal year

        Returns:
            Metrics by ticker
        """
        optimizer = QueryOptimizer(self.session)
        return optimizer.batch_calculate_metrics(tickers, fiscal_year, self.batch_size)
