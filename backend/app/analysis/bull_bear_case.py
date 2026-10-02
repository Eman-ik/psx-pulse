"""Bull Case & Bear Case Engine — derives strongest evidence-based thesis arguments.

Not generic "the stock is bullish", but: "If margins remain above X%, volume growth continues,
and finance costs decline, earnings could remain above current market trajectory. The major
re-rating argument is not simply earnings growth; it's earnings growth + declining balance-sheet risk."
"""

from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.analysis.evidence_context import ResearchContext, ContextualizedOutput


class BullBearCaseEngine:
    """Generate strongest evidence-based bull and bear theses."""

    @staticmethod
    def analyze(db: Session, issuer_id: int) -> Dict:
        """Generate bull, bear, and critical debate theses with Evidence Context."""
        # Single database scan
        context = ResearchContext(db, issuer_id)
        output = ContextualizedOutput("bull_bear_case", context)

        # Check data availability upfront
        has_revenue = context.has_metric("revenue")
        has_pat = context.has_metric("profit_after_tax")
        has_gross_profit = context.has_metric("gross_profit")
        has_total_debt = context.has_metric("total_debt")
        has_equity = context.has_metric("total_equity")
        has_pe_ratio = context.has_metric("pe_ratio")
        has_ocf = context.has_metric("operating_cash_flow")
        has_dps = context.has_metric("dividend_per_share")

        # Get data from context
        revenue = context.get_series("revenue", periods=3)
        pat = context.get_series("profit_after_tax", periods=3)
        gross_profit = context.get_series("gross_profit", periods=3)
        total_debt = context.get_series("total_debt", periods=3)
        equity = context.get_series("total_equity", periods=3)
        pe_ratio = context.get_value("pe_ratio")

        # Calculate trends
        rev_growth = None
        if len(revenue) >= 2 and revenue[-2] > 0:
            rev_growth = (revenue[-1] - revenue[-2]) / revenue[-2]

        margin = None
        if len(gross_profit) > 0 and len(revenue) > 0 and revenue[-1] > 0:
            margin = gross_profit[-1] / revenue[-1]

        leverage = None
        if len(total_debt) > 0 and len(equity) > 0 and equity[-1] > 0:
            leverage = total_debt[-1] / equity[-1]

        # BULL CASE
        bull_drivers = []
        if rev_growth and rev_growth > 0.05:
            bull_drivers.append(f"Revenue growth of {rev_growth:.1%} suggests sector tailwinds and pricing power.")
        if margin and margin > 0.25:
            bull_drivers.append("Gross margins above 25% provide cushion for operating leverage.")
        if leverage and leverage < 1.0:
            bull_drivers.append("Conservative leverage (below 1.0x D/E) allows debt reduction and increased distributions.")
        if pat and len(pat) >= 2 and pat[-1] > pat[-2]:
            bull_drivers.append("Profit is expanding despite industry headwinds.")

        bull_case = ""
        # ONLY add valuation language if PE data exists
        if context.can_claim("valuation"):
            if pe_ratio and pe_ratio < 10:
                bull_case = f"At {pe_ratio:.1f}x earnings, the stock trades below historical median and sector peers. "
        else:
            bull_case = "Current earnings trajectory suggests opportunity. "

        bull_case += f"If {', '.join(bull_drivers[-2:]) if bull_drivers else 'current operating trends'} continue, earnings expansion is likely. "

        # ONLY add dividend claim if data exists
        if context.can_claim("dividend_sustainable"):
            bull_case += "Dividend sustainability is strong given cash generation."
        else:
            bull_case += "Dividend capacity depends on cash flow sustainability."

        # BEAR CASE
        bear_drivers = []
        if rev_growth and rev_growth < 0.02:
            bear_drivers.append("Revenue growth below inflation signals stalling market share or pricing weakness.")
        if margin and margin < 0.15:
            bear_drivers.append("Margins near cycle lows offer limited protection in a downturn.")
        if leverage and leverage > 1.5:
            bear_drivers.append("Leverage above 1.5x limits balance-sheet flexibility and increases refinancing risk.")
        # Only claim valuation if data exists
        if has_pe_ratio and pe_ratio and pe_ratio > 12:
            bear_drivers.append("Valuation at or above historical median despite uncertain earnings trajectory.")

        bear_case = "Earnings sustainability is in question. "
        if bear_drivers:
            bear_case += f"{bear_drivers[0]} " if bear_drivers else ""
            bear_case += "If cost inflation persists while pricing discipline erodes, margins compress and earnings disappoint. "
        else:
            bear_case += "Working capital pressure and leverage constraints limit downside protection. "
        bear_case += "Market multiples may contract without visibility on earnings recovery."

        # CRITICAL DEBATE
        debate = "The stock's next material move depends most on: "
        if margin is not None:
            debate += f"(1) Whether gross margins hold above {margin * 100:.0f}% (bull thesis) or compress toward 15% (bear thesis). "
        if rev_growth is not None:
            debate += f"(2) Whether revenue growth can remain above {rev_growth * 100:.0f}% without sacrificing margins (bull) or slows materially (bear). "
        debate += "(3) The timing and scale of any balance-sheet improvement."

        # Confidence based on data
        metrics_available = sum([has_revenue, has_pat, has_gross_profit, has_total_debt, has_equity])
        confidence = "High" if metrics_available >= 4 else "Medium" if metrics_available >= 3 else "Low"
        coverage = (metrics_available / 5) * 100

        # Calculate score based on drivers
        score = 50 + len(bull_drivers) * 5 - len(bear_drivers) * 5
        score = max(0, min(100, score))

        output.set_assessment(
            assessment="Complete" if bull_drivers or bear_drivers else "Limited",
            score=score,
            narrative=bull_case,
            confidence=confidence,
            data_coverage=int(coverage),
        )

        result = output.to_dict()
        result["bull_case"] = {
            "drivers": bull_drivers,
            "thesis": bull_case,
        }
        result["bear_case"] = {
            "drivers": bear_drivers,
            "thesis": bear_case,
        }
        result["critical_debate"] = debate
        result["key_metrics"] = {
            "revenue_growth": rev_growth,
            "gross_margin": margin,
            "debt_to_equity": leverage,
            "pe_ratio": pe_ratio,
        }

        # Validate
        result["validation"] = output.validate()

        return result
