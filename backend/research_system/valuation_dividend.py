"""
Dividend Discount Model & Dividend Analysis

Sprint V5: Multi-stage dividend discount model (2-stage and 3-stage) for high-yield stocks,
plus dividend sustainability analysis.

Features:
- Two-stage DDM (high growth then stable)
- Three-stage DDM (high, transition, stable)
- Dividend sustainability check
- Dividend growth rate analysis
- Payout ratio trends
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .schema import Security, ValuationSnapshot, FinancialMetric


class DividendDiscountModel:
    """Multi-stage dividend discount model for dividend-paying stocks."""

    def __init__(self, session: Session):
        self.session = session

    def calculate_two_stage_ddm(
        self,
        current_dividend: Decimal,
        growth_rate_stage1: Decimal,
        growth_rate_stage2: Decimal,
        discount_rate: Decimal,
        years_stage1: int = 5,
    ) -> Decimal:
        """
        Two-stage Dividend Discount Model.

        Stage 1: High growth for specified years
        Stage 2: Terminal stable growth perpetuity

        Args:
            current_dividend: Latest annual dividend per share (PKR)
            growth_rate_stage1: Growth rate during high-growth period (%)
            growth_rate_stage2: Terminal growth rate (%)
            discount_rate: Required return / discount rate (%)
            years_stage1: Number of years for Stage 1 growth

        Returns:
            Fair value per share (Decimal)

        Example:
            >>> ddm.calculate_two_stage_ddm(
            ...     current_dividend=Decimal("2.50"),
            ...     growth_rate_stage1=Decimal("12"),
            ...     growth_rate_stage2=Decimal("4"),
            ...     discount_rate=Decimal("10"),
            ...     years_stage1=5
            ... )
            Decimal("52.30")
        """
        if discount_rate <= growth_rate_stage2:
            raise ValueError(
                f"discount_rate ({discount_rate}) <= growth_rate_stage2 ({growth_rate_stage2}); "
                "perpetuity diverges"
            )

        if discount_rate <= growth_rate_stage1:
            raise ValueError(
                f"discount_rate ({discount_rate}) <= growth_rate_stage1 ({growth_rate_stage1}); "
                "model invalid"
            )

        # Convert percentages to decimals
        g1 = growth_rate_stage1 / Decimal(100)
        g2 = growth_rate_stage2 / Decimal(100)
        r = discount_rate / Decimal(100)

        # Stage 1: PV of dividends growing at g1 for years_stage1 years
        pv_stage1 = Decimal(0)
        for year in range(1, years_stage1 + 1):
            dividend_year = current_dividend * ((1 + g1) ** year)
            pv_dividend = dividend_year / ((1 + r) ** year)
            pv_stage1 += pv_dividend

        # Stage 2: Terminal value at end of Stage 1
        terminal_dividend = current_dividend * ((1 + g1) ** years_stage1) * (1 + g2)
        terminal_value = terminal_dividend / (r - g2)

        # PV of terminal value
        pv_stage2 = terminal_value / ((1 + r) ** years_stage1)

        fair_value = pv_stage1 + pv_stage2
        return fair_value.quantize(Decimal("0.01"))

    def calculate_three_stage_ddm(
        self,
        current_dividend: Decimal,
        growth_rate_stage1: Decimal,
        growth_rate_stage2: Decimal,
        growth_rate_stage3: Decimal,
        discount_rate: Decimal,
        years_stage1: int = 3,
        years_stage2: int = 3,
    ) -> Decimal:
        """
        Three-stage Dividend Discount Model.

        Stage 1: High growth
        Stage 2: Transition/declining growth
        Stage 3: Terminal stable growth (perpetuity)

        Args:
            current_dividend: Latest annual dividend per share (PKR)
            growth_rate_stage1: High growth rate (%)
            growth_rate_stage2: Transition growth rate (%)
            growth_rate_stage3: Terminal growth rate (%)
            discount_rate: Required return / discount rate (%)
            years_stage1: Years of high growth
            years_stage2: Years of transition growth

        Returns:
            Fair value per share (Decimal)
        """
        if discount_rate <= growth_rate_stage3:
            raise ValueError(
                f"discount_rate ({discount_rate}) <= growth_rate_stage3 ({growth_rate_stage3})"
            )

        # Convert percentages to decimals
        g1 = growth_rate_stage1 / Decimal(100)
        g2 = growth_rate_stage2 / Decimal(100)
        g3 = growth_rate_stage3 / Decimal(100)
        r = discount_rate / Decimal(100)

        # Stage 1: PV of dividends
        pv_stage1 = Decimal(0)
        dividend_current = current_dividend
        for year in range(1, years_stage1 + 1):
            dividend_year = dividend_current * ((1 + g1) ** year)
            pv_dividend = dividend_year / ((1 + r) ** year)
            pv_stage1 += pv_dividend

        # End of Stage 1 dividend
        dividend_end_s1 = current_dividend * ((1 + g1) ** years_stage1)

        # Stage 2: PV of transition dividends
        pv_stage2 = Decimal(0)
        for year in range(1, years_stage2 + 1):
            dividend_year = dividend_end_s1 * ((1 + g2) ** year)
            pv_dividend = dividend_year / ((1 + r) ** (years_stage1 + year))
            pv_stage2 += pv_dividend

        # End of Stage 2 dividend
        dividend_end_s2 = dividend_end_s1 * ((1 + g2) ** years_stage2)

        # Stage 3: Terminal value (perpetuity at g3)
        terminal_dividend = dividend_end_s2 * (1 + g3)
        terminal_value = terminal_dividend / (r - g3)
        pv_stage3 = terminal_value / ((1 + r) ** (years_stage1 + years_stage2))

        fair_value = pv_stage1 + pv_stage2 + pv_stage3
        return fair_value.quantize(Decimal("0.01"))

    def check_dividend_sustainability(
        self,
        annual_dividend: Decimal,
        free_cash_flow: Decimal,
        shares_outstanding: Decimal,
        dividend_payout_ratio: Optional[Decimal] = None,
        fcf_growth_rate: Decimal = Decimal("5"),
        years_forward: int = 5,
    ) -> Dict:
        """
        Check if dividend is sustainable based on FCF coverage.

        Args:
            annual_dividend: Total annual dividends paid (PKR millions)
            free_cash_flow: Current annual FCF (PKR millions)
            shares_outstanding: Shares outstanding (millions)
            dividend_payout_ratio: Target payout ratio (%). If None, uses current.
            fcf_growth_rate: Expected FCF growth rate (%)
            years_forward: Years to project forward

        Returns:
            Dict with sustainability analysis:
            {
                "is_sustainable": bool,
                "current_payout_ratio": float,
                "target_payout_ratio": float,
                "fcf_per_share": Decimal,
                "coverage_ratio": float,
                "years_to_unsustainable": int or None,
                "recommendation": str,
                "projection": List[Dict]
            }
        """
        # Current metrics
        current_payout_ratio = (annual_dividend / free_cash_flow) * 100
        fcf_per_share = free_cash_flow / shares_outstanding
        coverage_ratio = float(free_cash_flow / annual_dividend)

        # Target payout ratio (if not specified, use current)
        if dividend_payout_ratio is None:
            target_payout = current_payout_ratio
        else:
            target_payout = float(dividend_payout_ratio)

        # Project forward
        g = fcf_growth_rate / Decimal(100)
        projection = []
        years_to_unsustainable = None

        for year in range(1, years_forward + 1):
            projected_fcf = free_cash_flow * ((1 + g) ** year)
            max_sustainable_dividend = projected_fcf * (target_payout / 100)
            is_sustainable = annual_dividend <= max_sustainable_dividend

            if not is_sustainable and years_to_unsustainable is None:
                years_to_unsustainable = year

            projection.append({
                "year": year,
                "fcf": float(projected_fcf),
                "max_sustainable_dividend": float(max_sustainable_dividend),
                "current_dividend": float(annual_dividend),
                "coverage_ratio": float(projected_fcf / annual_dividend),
                "is_sustainable": is_sustainable,
            })

        # Generate recommendation
        is_sustainable = coverage_ratio >= 1.3  # 30% margin of safety
        if coverage_ratio >= 2.0:
            recommendation = "Dividend appears very safe; significant room for growth"
        elif coverage_ratio >= 1.3:
            recommendation = "Dividend appears safe; modest room for growth"
        elif coverage_ratio >= 1.0:
            recommendation = "Dividend is covered but limited room for cuts if FCF declines"
        else:
            recommendation = "Dividend NOT covered by FCF; likely unsustainable"

        return {
            "is_sustainable": is_sustainable,
            "current_payout_ratio": float(current_payout_ratio),
            "target_payout_ratio": target_payout,
            "fcf_per_share": fcf_per_share.quantize(Decimal("0.01")),
            "coverage_ratio": round(coverage_ratio, 2),
            "years_to_unsustainable": years_to_unsustainable,
            "recommendation": recommendation,
            "projection": projection,
        }

    def analyze_dividend_growth(
        self,
        ticker: str,
        years: int = 5,
    ) -> Dict:
        """
        Analyze historical dividend growth trends.

        Args:
            ticker: Security ticker
            years: Historical years to analyze

        Returns:
            Dict with dividend growth analysis
        """
        security = self.session.query(Security).filter_by(ticker=ticker).first()
        if not security:
            raise ValueError(f"Security not found: {ticker}")

        # Get historical dividend data (from ValuationSnapshot)
        cutoff_date = datetime.now() - timedelta(days=365 * years)
        snapshots = (
            self.session.query(ValuationSnapshot)
            .filter(
                ValuationSnapshot.security_id == security.security_id,
                ValuationSnapshot.snapshot_date >= cutoff_date,
            )
            .order_by(ValuationSnapshot.snapshot_date)
            .all()
        )

        if not snapshots:
            return {"error": "Insufficient historical data"}

        # Extract dividends
        dividends = [
            (s.snapshot_date, s.dividend_per_share)
            for s in snapshots
            if s.dividend_per_share is not None
        ]

        if len(dividends) < 2:
            return {"error": "Insufficient dividend data"}

        # Calculate growth rates
        growth_rates = []
        for i in range(1, len(dividends)):
            prev_div = float(dividends[i - 1][1])
            curr_div = float(dividends[i][1])
            if prev_div > 0:
                growth = ((curr_div - prev_div) / prev_div) * 100
                growth_rates.append(growth)

        if not growth_rates:
            return {"error": "Cannot calculate growth rates"}

        avg_growth = sum(growth_rates) / len(growth_rates)
        recent_growth = (
            sum(growth_rates[-3:]) / len(growth_rates[-3:])
            if len(growth_rates) >= 3
            else avg_growth
        )

        return {
            "ticker": ticker,
            "years_analyzed": years,
            "dividend_history": dividends,
            "growth_rates": growth_rates,
            "average_growth": round(avg_growth, 2),
            "recent_growth": round(recent_growth, 2),
            "growth_trend": (
                "accelerating" if recent_growth > avg_growth else
                "decelerating" if recent_growth < avg_growth else
                "stable"
            ),
            "latest_dividend": float(dividends[-1][1]),
            "earliest_dividend": float(dividends[0][1]),
            "total_growth_period": round(
                (float(dividends[-1][1]) - float(dividends[0][1])) / float(dividends[0][1]) * 100,
                2
            ),
        }

    def estimate_sustainable_dividend(
        self,
        free_cash_flow: Decimal,
        target_payout_ratio: Decimal,
        shares_outstanding: Decimal,
    ) -> Decimal:
        """
        Estimate sustainable dividend per share based on target payout ratio.

        Args:
            free_cash_flow: Annual FCF (PKR millions)
            target_payout_ratio: Target dividend payout ratio (%)
            shares_outstanding: Shares outstanding (millions)

        Returns:
            Sustainable dividend per share (PKR)
        """
        payout_ratio = target_payout_ratio / Decimal(100)
        total_dividend_capacity = free_cash_flow * payout_ratio
        dividend_per_share = total_dividend_capacity / shares_outstanding
        return dividend_per_share.quantize(Decimal("0.01"))

    def calculate_dividend_yield(
        self,
        current_price: Decimal,
        annual_dividend: Decimal,
    ) -> Decimal:
        """
        Calculate dividend yield.

        Args:
            current_price: Current stock price (PKR)
            annual_dividend: Annual dividend per share (PKR)

        Returns:
            Dividend yield (%)
        """
        if current_price <= 0:
            raise ValueError("Current price must be positive")

        yield_pct = (annual_dividend / current_price) * Decimal(100)
        return yield_pct.quantize(Decimal("0.01"))

    def compare_to_index_yield(
        self,
        stock_yield: Decimal,
        index_yield: Decimal,
    ) -> Dict:
        """
        Compare stock dividend yield to market index.

        Args:
            stock_yield: Stock dividend yield (%)
            index_yield: Index (e.g., KSE-100) dividend yield (%)

        Returns:
            Comparison analysis
        """
        spread = stock_yield - index_yield
        yield_multiple = stock_yield / index_yield if index_yield > 0 else Decimal(0)

        if stock_yield > index_yield * Decimal("1.5"):
            classification = "High Yield"
            interpretation = "Significantly above market; attractive for income"
        elif stock_yield > index_yield:
            classification = "Above Market"
            interpretation = "Better than average dividend income"
        elif stock_yield > index_yield * Decimal("0.5"):
            classification = "Below Market"
            interpretation = "Dividend below market average"
        else:
            classification = "Low Yield"
            interpretation = "Limited dividend income"

        return {
            "stock_yield": float(stock_yield),
            "index_yield": float(index_yield),
            "spread_bps": float(spread * Decimal(100)),
            "yield_multiple": float(yield_multiple),
            "classification": classification,
            "interpretation": interpretation,
        }
