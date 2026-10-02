"""Risk Engine — identify business, financial, market, macro, regulatory and governance risks.

Not just "risk score". Probability × Impact × Trend, ranked by severity.
"""

from typing import Optional, Dict, List

from app.analysis.evidence_context import ResearchContext, ContextualizedOutput
from app.analysis.period_alignment import PeriodAlignedAnalyzer


class RiskEngine:
    """Comprehensive risk assessment across all dimensions."""

    @staticmethod
    def analyze(context: ResearchContext) -> Dict:
        """Identify and rank risks using period-aligned Evidence Context."""
        output = ContextualizedOutput("risk_engine", context)
        analyzer = PeriodAlignedAnalyzer(context)

        risks = []
        period_type = "Q"  # Default to Q for latest snapshot

        # BUSINESS RISKS
        # Customer concentration: company-specific, requires customer_concentration metric
        customer_concentration = context.get_value("customer_concentration")
        if context.has_metric("customer_concentration") and customer_concentration and customer_concentration > 0.30:
            risks.append({
                "category": "Business",
                "title": "Customer concentration",
                "description": f"Top customer represents {customer_concentration:.0%} of revenue.",
                "probability": "Medium",
                "impact": "High",
                "trend": "Stable",
                "type": "company_specific",
            })
        elif not context.has_metric("customer_concentration"):
            # If metric missing, label as sector-level structural risk
            risks.append({
                "category": "Business",
                "title": "Customer base structure risk",
                "description": "Typical structural risk in fertilizer sector—customer base often concentrated.",
                "probability": "Medium",
                "impact": "Medium",
                "trend": "Stable",
                "type": "sector_level",
            })

        # Market share: company-specific
        market_share = context.get_value("market_share")
        if context.has_metric("market_share") and market_share and market_share < 0.05:
            risks.append({
                "category": "Business",
                "title": "Low market share",
                "description": "Company operates in a fragmented or competitive environment.",
                "probability": "High",
                "impact": "Medium",
                "trend": "Rising",
                "type": "company_specific",
            })

        # FINANCIAL RISKS
        # Calculate leverage from aligned period (not pre-calculated debt_to_equity)
        debt_equity_aligned = context.get_aligned_values(
            ["total_debt", "total_equity"],
            period_type="Q",
            limit=1
        )
        leverage = None
        if debt_equity_aligned and debt_equity_aligned[0].get("total_debt") and debt_equity_aligned[0].get("total_equity"):
            debt = debt_equity_aligned[0]["total_debt"]
            equity = debt_equity_aligned[0]["total_equity"]
            if equity > 0:
                leverage = debt / equity
                period_type = context.get_period_type(debt_equity_aligned[0].get("period_end"))

        if leverage and leverage > 1.5:
            risks.append({
                "category": "Financial",
                "title": "High leverage",
                "description": f"Debt-to-equity at {leverage:.1f}x limits balance-sheet flexibility.",
                "probability": "Medium",
                "impact": "High",
                "trend": "Rising" if leverage > 1.2 else "Stable",
                "type": "company_specific",
            })

        liquidity = context.get_value("current_ratio")
        if context.has_metric("current_ratio") and liquidity and liquidity < 1.0:
            risks.append({
                "category": "Financial",
                "title": "Liquidity pressure",
                "description": "Current ratio below 1.0 suggests potential short-term payment challenges.",
                "probability": "Medium",
                "impact": "High",
                "trend": "Rising",
                "type": "company_specific",
            })

        # MARKET RISKS
        volatility = context.get_value("volatility_annual")
        if context.has_metric("volatility_annual") and volatility and volatility > 0.40:
            risks.append({
                "category": "Market",
                "title": "High volatility",
                "description": f"Annual volatility of {volatility:.0%} makes the stock a high-beta instrument.",
                "probability": "High",
                "impact": "Medium",
                "trend": "Stable",
                "type": "market",
            })

        # MACRO RISKS
        fxexposure = context.get_value("fx_exposure_pct")
        if context.has_metric("fx_exposure_pct") and fxexposure and fxexposure > 0.20:
            risks.append({
                "category": "Macro",
                "title": "PKR depreciation exposure",
                "description": f"Approximately {fxexposure:.0%} of cash flows are in foreign currency.",
                "probability": "Medium",
                "impact": "Medium",
                "trend": "Rising",
                "type": "macro",
            })

        # REGULATORY RISKS (sector-level, always add)
        risks.append({
            "category": "Regulatory",
            "title": "Environmental / emissions regulation",
            "description": "Tightening emissions standards could increase compliance capex.",
            "probability": "Medium",
            "impact": "Medium",
            "trend": "Rising",
            "type": "sector_level",
        })

        # GOVERNANCE RISKS
        promoter_ownership = context.get_value("promoter_ownership")
        if context.has_metric("promoter_ownership") and promoter_ownership and promoter_ownership > 0.60:
            risks.append({
                "category": "Governance",
                "title": "High promoter concentration",
                "description": f"Promoters own {promoter_ownership:.0%}, limiting minority investor influence.",
                "probability": "Low",
                "impact": "Low",
                "trend": "Stable",
                "type": "company_specific",
            })

        # Sort by probability × impact
        score_map = {"High": 3, "Medium": 2, "Low": 1}
        for risk in risks:
            prob_score = score_map.get(risk["probability"], 1)
            impact_score = score_map.get(risk["impact"], 1)
            risk["composite_score"] = prob_score * impact_score

        risks.sort(key=lambda x: x["composite_score"], reverse=True)

        # Categorize by severity
        high_risks = [r for r in risks if r["composite_score"] >= 6]
        medium_risks = [r for r in risks if 3 <= r["composite_score"] < 6]
        low_risks = [r for r in risks if r["composite_score"] < 3]

        # Confidence based on data
        metrics_available = sum([
            context.has_metric("debt_to_equity"),
            context.has_metric("customer_concentration"),
            context.has_metric("market_share"),
            context.has_metric("liquidity"),
        ])
        confidence = "High" if metrics_available >= 3 else "Medium" if metrics_available >= 2 else "Low"
        coverage = (metrics_available / 4) * 100

        # Calculate score (lower is worse)
        score = 90 - (len(high_risks) * 15 + len(medium_risks) * 5)
        score = max(0, min(100, score))

        output.set_assessment(
            assessment="Complete" if len(risks) > 0 else "No risks",
            score=score,
            narrative=f"Identified {len(high_risks)} high-priority risks.",
            confidence=confidence,
            data_coverage=int(coverage),
        )

        result = output.to_dict()
        result["summary"] = {
            "high": len(high_risks),
            "medium": len(medium_risks),
            "low": len(low_risks),
        }
        result["high_priority_risks"] = high_risks[:3]
        result["all_risks"] = risks
        result["recommendation"] = "High caution" if len(high_risks) > 2 else ("Monitor" if len(high_risks) > 0 else "Acceptable")
        result["period_type"] = period_type  # Explicitly document which period type was analyzed

        # Validate
        result["validation"] = output.validate()

        return result
