"""
Valuation & Comparative Intelligence — Core Calculation Engine

Module 2 Sprint V1: Foundation
- Market cap and enterprise value calculation
- TTM (trailing twelve months) aggregation
- Core valuation metrics (P/E, P/B, EV/EBITDA, FCF Yield, Dividend Yield)
- Valuation snapshot storage
"""

from decimal import Decimal
from datetime import datetime, timedelta, date
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from .schema import (
    Security, FinancialLineItem, FinancialPeriod, FinancialMetric,
    MetricDefinition, MarketSnapshot, ValuationInput, ValuationSnapshot,
    PeriodType, StatementType
)


class ValuationEngine:
    """Core valuation calculation engine."""

    def __init__(self, session: Session):
        self.session = session

    def calculate_market_cap(
        self,
        close_price: Decimal,
        shares_outstanding: Decimal
    ) -> Decimal:
        """Calculate market cap from price and shares."""
        return Decimal(close_price) * Decimal(shares_outstanding)

    def calculate_enterprise_value(
        self,
        market_cap: Decimal,
        total_debt: Optional[Decimal] = None,
        cash: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate enterprise value.
        EV = Market Cap + Debt - Cash
        """
        ev = Decimal(market_cap)

        if total_debt:
            ev += Decimal(total_debt)

        if cash:
            ev -= Decimal(cash)

        return ev

    def get_ttm_value(
        self,
        security_id: int,
        metric_code: str,
        as_of_date: date
    ) -> Optional[Decimal]:
        """
        Calculate TTM (trailing twelve months) value for a metric.
        Aggregates last 4 quarters of data.
        """
        # Find metric definition
        metric_def = self.session.query(MetricDefinition).filter(
            MetricDefinition.metric_code == metric_code
        ).first()

        if not metric_def:
            return None

        # Find financial periods for last 12 months
        cutoff_date = as_of_date - timedelta(days=365)

        periods = self.session.query(FinancialPeriod).filter(
            FinancialPeriod.security_id == security_id,
            FinancialPeriod.period_end >= cutoff_date,
            FinancialPeriod.period_end <= as_of_date,
            FinancialPeriod.is_complete == True
        ).order_by(FinancialPeriod.period_end.desc()).limit(4).all()

        if not periods:
            return None

        # Sum values from line items
        total_value = Decimal(0)

        for period in periods:
            line_item = self.session.query(FinancialLineItem).filter(
                FinancialLineItem.period_id == period.period_id,
                FinancialLineItem.metric_id == metric_def.metric_id
            ).first()

            if line_item:
                total_value += Decimal(line_item.value)

        return total_value if total_value > 0 else None

    def get_latest_balance_sheet_value(
        self,
        security_id: int,
        metric_code: str,
        as_of_date: date
    ) -> Optional[Decimal]:
        """Get latest balance sheet value (as-of specific date)."""
        metric_def = self.session.query(MetricDefinition).filter(
            MetricDefinition.metric_code == metric_code
        ).first()

        if not metric_def:
            return None

        # Get most recent period on or before as_of_date
        period = self.session.query(FinancialPeriod).filter(
            FinancialPeriod.security_id == security_id,
            FinancialPeriod.period_end <= as_of_date,
            FinancialPeriod.is_complete == True
        ).order_by(FinancialPeriod.period_end.desc()).first()

        if not period:
            return None

        line_item = self.session.query(FinancialLineItem).filter(
            FinancialLineItem.period_id == period.period_id,
            FinancialLineItem.metric_id == metric_def.metric_id
        ).first()

        return Decimal(line_item.value) if line_item else None

    def calculate_eps_ttm(
        self,
        security_id: int,
        shares_outstanding: Decimal,
        as_of_date: date
    ) -> Optional[Decimal]:
        """Calculate EPS TTM from net income TTM."""
        net_income_ttm = self.get_ttm_value(security_id, "NET_INCOME", as_of_date)

        if not net_income_ttm or net_income_ttm == 0:
            return None

        # Net income is in millions, EPS in individual shares
        eps = Decimal(net_income_ttm) * Decimal(1_000_000) / Decimal(shares_outstanding)

        return eps if eps > 0 else None

    def calculate_book_value_per_share(
        self,
        security_id: int,
        shares_outstanding: Decimal,
        as_of_date: date
    ) -> Optional[Decimal]:
        """Calculate book value per share."""
        equity = self.get_latest_balance_sheet_value(
            security_id, "TOTAL_EQUITY", as_of_date
        )

        if not equity or equity == 0:
            return None

        # Equity in millions
        bvps = Decimal(equity) * Decimal(1_000_000) / Decimal(shares_outstanding)

        return bvps if bvps > 0 else None

    def calculate_pe_ratio(
        self,
        close_price: Decimal,
        eps_ttm: Optional[Decimal]
    ) -> Optional[Decimal]:
        """Calculate P/E ratio."""
        if not eps_ttm or eps_ttm <= 0:
            return None

        pe = Decimal(close_price) / Decimal(eps_ttm)

        return pe if pe > 0 else None

    def calculate_pb_ratio(
        self,
        close_price: Decimal,
        book_value_per_share: Optional[Decimal]
    ) -> Optional[Decimal]:
        """Calculate P/B ratio."""
        if not book_value_per_share or book_value_per_share <= 0:
            return None

        pb = Decimal(close_price) / Decimal(book_value_per_share)

        return pb if pb > 0 else None

    def calculate_ps_ratio(
        self,
        market_cap: Decimal,
        revenue_ttm: Optional[Decimal]
    ) -> Optional[Decimal]:
        """Calculate Price/Sales ratio. Both values in same currency unit."""
        if not revenue_ttm or revenue_ttm <= 0:
            return None

        ps = Decimal(market_cap) / Decimal(revenue_ttm)

        return ps if ps > 0 else None

    def calculate_ev_ebitda_ratio(
        self,
        enterprise_value: Decimal,
        ebitda_ttm: Optional[Decimal]
    ) -> Optional[Decimal]:
        """Calculate EV/EBITDA ratio. Both values in same currency unit."""
        if not ebitda_ttm or ebitda_ttm <= 0:
            return None

        ratio = Decimal(enterprise_value) / Decimal(ebitda_ttm)

        return ratio if ratio > 0 else None

    def calculate_fcf_yield(
        self,
        fcf_ttm: Optional[Decimal],
        market_cap: Decimal
    ) -> Optional[Decimal]:
        """Calculate free cash flow yield (%). Both values in same currency unit."""
        if not fcf_ttm or fcf_ttm <= 0 or market_cap <= 0:
            return None

        yield_pct = (Decimal(fcf_ttm) / Decimal(market_cap)) * 100

        return yield_pct if yield_pct > 0 else None

    def calculate_dividend_yield(
        self,
        close_price: Decimal,
        dps_ttm: Optional[Decimal]
    ) -> Optional[Decimal]:
        """Calculate dividend yield (%)."""
        if not dps_ttm or dps_ttm <= 0 or close_price <= 0:
            return None

        yield_pct = (Decimal(dps_ttm) / Decimal(close_price)) * 100

        return yield_pct if yield_pct > 0 else None

    def create_valuation_input(
        self,
        security_id: int,
        close_price: Decimal,
        shares_outstanding: Decimal,
        as_of_date: date
    ) -> Optional[ValuationInput]:
        """
        Create comprehensive valuation input from Module 1 data.
        Aggregates TTM metrics, balance sheet values, and market data.
        """
        # Calculate market cap
        market_cap = self.calculate_market_cap(close_price, shares_outstanding)

        # Get TTM values
        revenue_ttm = self.get_ttm_value(security_id, "REVENUE", as_of_date)
        ebitda_ttm = self.get_ttm_value(security_id, "EBITDA", as_of_date)
        fcf_ttm = self.get_ttm_value(security_id, "FREE_CASH_FLOW", as_of_date)
        dps_ttm = self.get_ttm_value(security_id, "DIVIDEND_PER_SHARE", as_of_date)

        # Get balance sheet values
        total_debt = self.get_latest_balance_sheet_value(
            security_id, "TOTAL_DEBT", as_of_date
        )
        cash = self.get_latest_balance_sheet_value(
            security_id, "CASH_AND_EQUIVALENTS", as_of_date
        )
        total_equity = self.get_latest_balance_sheet_value(
            security_id, "TOTAL_EQUITY", as_of_date
        )

        # Calculate per-share metrics
        eps_ttm = self.calculate_eps_ttm(security_id, shares_outstanding, as_of_date)
        bvps = self.calculate_book_value_per_share(
            security_id, shares_outstanding, as_of_date
        )

        # Create valuation input record
        valuation_input = ValuationInput(
            security_id=security_id,
            as_of_date=as_of_date,
            eps_ttm=eps_ttm,
            book_value_per_share=bvps,
            revenue_ttm=revenue_ttm,
            ebitda_ttm=ebitda_ttm,
            free_cash_flow_ttm=fcf_ttm,
            dividend_per_share_ttm=dps_ttm,
            total_debt=total_debt,
            cash_and_equivalents=cash,
            total_equity=total_equity,
            shares_outstanding=shares_outstanding,
            close_price=close_price,
            market_cap=market_cap,
            normalized=False,
            ttm_complete=True
        )

        return valuation_input

    def create_valuation_snapshot(
        self,
        security_id: int,
        close_price: Decimal,
        shares_outstanding: Decimal,
        as_of_date: date
    ) -> Optional[ValuationSnapshot]:
        """
        Calculate and store valuation multiples.
        Creates a ValuationSnapshot with all core metrics.
        """
        # Create valuation input first
        val_input = self.create_valuation_input(
            security_id, close_price, shares_outstanding, as_of_date
        )

        if not val_input:
            return None

        # Calculate enterprise value
        ev = self.calculate_enterprise_value(
            val_input.market_cap,
            val_input.total_debt,
            val_input.cash_and_equivalents
        )

        # Calculate all ratios
        pe = self.calculate_pe_ratio(close_price, val_input.eps_ttm)
        pb = self.calculate_pb_ratio(close_price, val_input.book_value_per_share)
        ps = self.calculate_ps_ratio(val_input.market_cap, val_input.revenue_ttm)
        ev_ebitda = self.calculate_ev_ebitda_ratio(ev, val_input.ebitda_ttm)
        fcf_yield = self.calculate_fcf_yield(val_input.free_cash_flow_ttm, val_input.market_cap)
        div_yield = self.calculate_dividend_yield(close_price, val_input.dividend_per_share_ttm)

        # Create snapshot
        snapshot = ValuationSnapshot(
            security_id=security_id,
            snapshot_date=as_of_date,
            pe_ratio=pe,
            pb_ratio=pb,
            ps_ratio=ps,
            ev_ebitda_ratio=ev_ebitda,
            fcf_yield=fcf_yield,
            dividend_yield=div_yield,
            enterprise_value=ev
        )

        return snapshot

    def get_sector_applicable_metrics(self, sector_id: int) -> Dict[str, int]:
        """Get applicable valuation metrics for a sector."""
        from .schema import ValuationMetricApplicability

        metrics = self.session.query(
            ValuationMetricApplicability.metric_code,
            ValuationMetricApplicability.priority
        ).filter(
            ValuationMetricApplicability.sector_id == sector_id,
            ValuationMetricApplicability.enabled == True
        ).order_by(ValuationMetricApplicability.priority).all()

        return {m[0]: m[1] for m in metrics}
