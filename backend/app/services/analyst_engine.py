"""Analyst Engine — Convert LLM analysis into investment decisions.

Transforms LLMAnalysisResult (thesis, catalysts, risks) into:
- Investment recommendation (Buy/Hold/Sell)
- Position sizing (quantity, % of portfolio)
- Entry/exit levels with confidence bands
- Risk management (stop loss, take profit)
- Scenario analysis (bull/base/bear cases)
- Monitoring triggers and alerts

Input: LLMAnalysisResult + EvidencePack (for context)
Output: InvestmentDecision (actionable trading recommendation)
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    """Investment recommendation types."""

    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    HOLD = "Hold"
    SELL = "Sell"
    STRONG_SELL = "Strong Sell"


class PositionSizeCategory(str, Enum):
    """Position size categories."""

    FULL = "Full"        # 5-10% of portfolio
    STANDARD = "Standard"  # 2-5% of portfolio
    REDUCED = "Reduced"   # <2% of portfolio
    AVOID = "Avoid"      # 0% of portfolio


@dataclass
class ScenarioProjection:
    """Price projection under different scenarios."""

    name: str  # "Bull", "Base", "Bear"
    target_price: float
    probability_pct: float
    upside_pct: float  # (target - current) / current * 100
    reasoning: str


@dataclass
class RiskManagementRules:
    """Risk management configuration."""

    stop_loss_pct: float  # Below current price (e.g., 10.0 = 10% stop)
    take_profit_pct: float  # Above entry (e.g., 30.0 = 30% profit target)
    position_size_pct: float  # % of portfolio
    max_drawdown_pct: float  # Maximum acceptable loss
    monitoring_interval_days: int  # Check position every N days


@dataclass
class InvestmentDecision:
    """Complete investment decision."""

    ticker: str
    recommendation: RecommendationType
    confidence_pct: float  # 0-100%
    conviction_level: str  # "High", "Medium", "Low"

    # Entry & Exit
    suggested_entry_price: float
    entry_confidence_band_pct: float  # ± from entry
    target_exit_price: float
    stop_loss_price: float

    # Position Management
    position_size_category: PositionSizeCategory
    position_size_pct: float  # % of portfolio
    suggested_quantity: Optional[int]  # For specific portfolio size

    # Scenarios
    bull_case_projection: ScenarioProjection
    base_case_projection: ScenarioProjection
    bear_case_projection: ScenarioProjection
    expected_return_pct: float  # Probability-weighted

    # Risk Management
    risk_management: RiskManagementRules
    key_upside_catalysts: List[str]
    key_downside_risks: List[str]
    monitoring_triggers: List[str]  # Signals to recheck thesis

    # Metadata
    analysis_timestamp: str
    time_horizon: str
    invalidation_events: List[str]  # Thesis breakers

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "recommendation": self.recommendation.value,
            "confidence_pct": self.confidence_pct,
            "conviction_level": self.conviction_level,
            "suggested_entry_price": self.suggested_entry_price,
            "entry_confidence_band_pct": self.entry_confidence_band_pct,
            "target_exit_price": self.target_exit_price,
            "stop_loss_price": self.stop_loss_price,
            "position_size_category": self.position_size_category.value,
            "position_size_pct": self.position_size_pct,
            "suggested_quantity": self.suggested_quantity,
            "bull_case": {
                "target_price": self.bull_case_projection.target_price,
                "upside_pct": self.bull_case_projection.upside_pct,
                "probability_pct": self.bull_case_projection.probability_pct,
            },
            "base_case": {
                "target_price": self.base_case_projection.target_price,
                "upside_pct": self.base_case_projection.upside_pct,
                "probability_pct": self.base_case_projection.probability_pct,
            },
            "bear_case": {
                "target_price": self.bear_case_projection.target_price,
                "upside_pct": self.bear_case_projection.upside_pct,
                "probability_pct": self.bear_case_projection.probability_pct,
            },
            "expected_return_pct": self.expected_return_pct,
            "risk_management": {
                "stop_loss_pct": self.risk_management.stop_loss_pct,
                "take_profit_pct": self.risk_management.take_profit_pct,
                "position_size_pct": self.risk_management.position_size_pct,
            },
            "key_upside_catalysts": self.key_upside_catalysts,
            "key_downside_risks": self.key_downside_risks,
            "time_horizon": self.time_horizon,
        }


class AnalystEngine:
    """Converts LLM analysis into investment decisions."""

    def __init__(self):
        """Initialize analyst engine."""
        self.logger = logging.getLogger(__name__)

    def decide(
        self,
        llm_result: "LLMAnalysisResult",
        evidence_pack: "EvidencePack",
        portfolio_size_thousands: Optional[int] = 100,
    ) -> Optional[InvestmentDecision]:
        """Generate investment decision from LLM analysis.

        Args:
            llm_result: Analysis from LLMClient
            evidence_pack: Structured facts about company
            portfolio_size_thousands: Portfolio size in thousands PKR (for sizing)

        Returns:
            InvestmentDecision or None on error
        """
        try:
            # Extract basic data
            ticker = llm_result.ticker
            current_price = evidence_pack.current_price or 100.0
            confidence = llm_result.confidence

            # Determine recommendation & conviction
            recommendation, conviction = self._determine_recommendation(
                llm_result.overall_thesis,
                confidence,
                len(llm_result.key_catalysts),
                len(llm_result.key_risks),
            )

            # Calculate entry/exit prices
            entry_price = self._calculate_entry_price(current_price, llm_result.overall_thesis)
            entry_band = self._calculate_confidence_band(entry_price, confidence)
            exit_price = self._calculate_exit_price(entry_price, llm_result.overall_thesis)
            stop_loss = self._calculate_stop_loss(entry_price, confidence)

            # Position sizing
            pos_category, pos_pct = self._calculate_position_size(confidence, conviction)
            suggested_qty = self._calculate_quantity(
                pos_pct, portfolio_size_thousands or 100, entry_price
            )

            # Scenario analysis
            bull = self._build_scenario(
                "Bull", entry_price, confidence, 40, 1.15
            )
            base = self._build_scenario(
                "Base", entry_price, confidence, 35, 1.05
            )
            bear = self._build_scenario(
                "Bear", entry_price, confidence, 25, 0.85
            )

            expected_return = (
                (bull.upside_pct * bull.probability_pct / 100)
                + (base.upside_pct * base.probability_pct / 100)
                + (bear.upside_pct * bear.probability_pct / 100)
            )

            # Risk management
            risk_mgmt = RiskManagementRules(
                stop_loss_pct=self._calculate_stop_loss_pct(entry_price, stop_loss),
                take_profit_pct=self._calculate_take_profit_pct(exit_price, entry_price),
                position_size_pct=pos_pct,
                max_drawdown_pct=20.0,
                monitoring_interval_days=7,
            )

            # Monitoring triggers
            triggers = self._build_monitoring_triggers(evidence_pack, llm_result)

            # Invalidation events
            invalidations = self._build_invalidation_events(llm_result, evidence_pack)

            # Build decision
            decision = InvestmentDecision(
                ticker=ticker,
                recommendation=recommendation,
                confidence_pct=confidence,
                conviction_level=conviction,
                suggested_entry_price=entry_price,
                entry_confidence_band_pct=entry_band,
                target_exit_price=exit_price,
                stop_loss_price=stop_loss,
                position_size_category=pos_category,
                position_size_pct=pos_pct,
                suggested_quantity=suggested_qty,
                bull_case_projection=bull,
                base_case_projection=base,
                bear_case_projection=bear,
                expected_return_pct=expected_return,
                risk_management=risk_mgmt,
                key_upside_catalysts=llm_result.key_catalysts[:3],
                key_downside_risks=llm_result.key_risks[:3],
                monitoring_triggers=triggers,
                analysis_timestamp=str(__import__("datetime").datetime.utcnow()),
                time_horizon=llm_result.time_horizon,
                invalidation_events=invalidations,
            )

            self.logger.info(f"Generated decision for {ticker}: {recommendation.value}")
            return decision

        except Exception as e:
            self.logger.error(f"Error generating decision: {e}")
            return None

    @staticmethod
    def _determine_recommendation(
        thesis: str, confidence: float, catalyst_count: int, risk_count: int
    ) -> tuple:
        """Determine recommendation and conviction from thesis.

        Args:
            thesis: Overall thesis (Bullish/Bearish/Neutral/Mixed)
            confidence: Confidence 0-100%
            catalyst_count: Number of upside catalysts
            risk_count: Number of downside risks

        Returns:
            (RecommendationType, conviction_level_str)
        """
        # Base recommendation on thesis
        if thesis == "Bullish":
            if confidence >= 80:
                return (RecommendationType.STRONG_BUY, "High")
            else:
                return (RecommendationType.BUY, "Medium")
        elif thesis == "Bearish":
            if confidence >= 80:
                return (RecommendationType.STRONG_SELL, "High")
            else:
                return (RecommendationType.SELL, "Medium")
        elif thesis == "Mixed":
            return (RecommendationType.HOLD, "Medium")
        else:  # Neutral
            return (RecommendationType.HOLD, "Low")

    @staticmethod
    def _calculate_entry_price(current_price: float, thesis: str) -> float:
        """Calculate suggested entry price.

        Args:
            current_price: Current market price
            thesis: Investment thesis

        Returns:
            Suggested entry price
        """
        if thesis == "Bullish":
            # Enter slightly above current (momentum)
            return current_price * 1.02
        elif thesis == "Bearish":
            # Enter at market (or wait for rebound)
            return current_price
        else:
            # Neutral/Mixed: wait for consolidation
            return current_price * 0.98

    @staticmethod
    def _calculate_confidence_band(entry_price: float, confidence: float) -> float:
        """Calculate confidence band around entry price.

        Args:
            entry_price: Entry price
            confidence: Confidence 0-100%

        Returns:
            Confidence band as percentage
        """
        # Higher confidence = tighter band
        if confidence >= 80:
            return 2.0  # ±2%
        elif confidence >= 60:
            return 3.5  # ±3.5%
        elif confidence >= 40:
            return 5.0  # ±5%
        else:
            return 7.5  # ±7.5%

    @staticmethod
    def _calculate_exit_price(entry_price: float, thesis: str) -> float:
        """Calculate target exit price.

        Args:
            entry_price: Entry price
            thesis: Investment thesis

        Returns:
            Target exit price
        """
        if thesis == "Bullish":
            # 20-30% upside target
            return entry_price * 1.25
        elif thesis == "Bearish":
            # 15-20% downside target
            return entry_price * 0.80
        else:
            # Neutral: 5-10% range
            return entry_price * 1.05

    @staticmethod
    def _calculate_stop_loss(entry_price: float, confidence: float) -> float:
        """Calculate stop loss level.

        Args:
            entry_price: Entry price
            confidence: Confidence 0-100%

        Returns:
            Stop loss price
        """
        # Higher confidence = wider stop (less likely to be hit)
        if confidence >= 80:
            stop_pct = 0.10  # 10% stop
        elif confidence >= 60:
            stop_pct = 0.08  # 8% stop
        else:
            stop_pct = 0.05  # 5% stop

        return entry_price * (1 - stop_pct)

    @staticmethod
    def _calculate_stop_loss_pct(entry_price: float, stop_loss_price: float) -> float:
        """Calculate stop loss as percentage below entry."""
        return ((entry_price - stop_loss_price) / entry_price) * 100

    @staticmethod
    def _calculate_take_profit_pct(exit_price: float, entry_price: float) -> float:
        """Calculate take profit as percentage above entry."""
        return ((exit_price - entry_price) / entry_price) * 100

    @staticmethod
    def _calculate_position_size(confidence: float, conviction: str) -> tuple:
        """Determine position size category and percentage.

        Args:
            confidence: Confidence 0-100%
            conviction: Conviction level (High/Medium/Low)

        Returns:
            (PositionSizeCategory, position_size_pct)
        """
        if conviction == "High" and confidence >= 80:
            return (PositionSizeCategory.FULL, 7.5)
        elif conviction == "High" and confidence >= 60:
            return (PositionSizeCategory.STANDARD, 4.0)
        elif conviction == "Medium" and confidence >= 60:
            return (PositionSizeCategory.STANDARD, 3.0)
        elif conviction == "Medium":
            return (PositionSizeCategory.REDUCED, 1.5)
        else:
            return (PositionSizeCategory.REDUCED, 0.5)

    @staticmethod
    def _calculate_quantity(
        position_pct: float, portfolio_size_thousands: int, entry_price: float
    ) -> Optional[int]:
        """Calculate suggested quantity.

        Args:
            position_pct: Position size as % of portfolio
            portfolio_size_thousands: Portfolio size in thousands PKR
            entry_price: Entry price per share

        Returns:
            Suggested quantity or None if too small
        """
        position_value = (position_pct / 100) * (portfolio_size_thousands * 1000)
        quantity = int(position_value / entry_price)
        return quantity if quantity > 0 else None

    @staticmethod
    def _build_scenario(
        name: str, base_price: float, confidence: float, probability: float, multiplier: float
    ) -> ScenarioProjection:
        """Build scenario projection.

        Args:
            name: Scenario name (Bull/Base/Bear)
            base_price: Base price for calculation
            confidence: Overall confidence
            probability: Base probability for scenario
            multiplier: Price multiplier (1.15 for bull, 0.85 for bear)

        Returns:
            ScenarioProjection
        """
        target = base_price * multiplier
        upside = ((target - base_price) / base_price) * 100
        # Adjust probability based on confidence
        adjusted_prob = probability if confidence >= 60 else probability * 0.8

        reasoning = {
            "Bull": "Strong fundamentals + positive catalysts drive valuation expansion",
            "Base": "Stable growth with modest multiple expansion",
            "Bear": "Macro headwinds or execution risks compress multiples",
        }.get(name, "Scenario analysis")

        return ScenarioProjection(
            name=name,
            target_price=target,
            probability_pct=min(adjusted_prob, 100),
            upside_pct=upside,
            reasoning=reasoning,
        )

    @staticmethod
    def _build_monitoring_triggers(
        evidence_pack: "EvidencePack", llm_result: "LLMAnalysisResult"
    ) -> List[str]:
        """Build list of monitoring triggers.

        Args:
            evidence_pack: Evidence pack with technical/fundamental data
            llm_result: LLM analysis result

        Returns:
            List of monitoring triggers
        """
        triggers = []

        # Technical triggers
        if evidence_pack.trend == "uptrend":
            triggers.append("Break below 20-day moving average")
            triggers.append("Trend strength drops below 30%")
        elif evidence_pack.trend == "downtrend":
            triggers.append("Break above 20-day moving average")
            triggers.append("Support level breaks")

        # Fundamental triggers
        if evidence_pack.revenue_growth_pct and evidence_pack.revenue_growth_pct > 10:
            triggers.append("Quarterly revenue growth drops below 5%")
        if evidence_pack.earnings_growth_pct and evidence_pack.earnings_growth_pct > 10:
            triggers.append("Earnings miss or warning")

        # Event triggers
        if llm_result.key_catalysts:
            triggers.append(f"Catalyst delay: {llm_result.key_catalysts[0]}")

        return triggers[:3]  # Top 3 triggers

    @staticmethod
    def _build_invalidation_events(
        llm_result: "LLMAnalysisResult", evidence_pack: "EvidencePack"
    ) -> List[str]:
        """Build list of thesis invalidation events.

        Args:
            llm_result: LLM analysis
            evidence_pack: Evidence pack

        Returns:
            List of invalidation triggers
        """
        invalidations = []

        # Risk-based invalidations
        if llm_result.key_risks:
            for risk in llm_result.key_risks[:2]:
                if "regulatory" in risk.lower():
                    invalidations.append("Major regulatory adverse ruling")
                elif "leverage" in risk.lower():
                    invalidations.append("Debt covenant breach")
                elif "market" in risk.lower():
                    invalidations.append("30%+ market downturn in 3 months")
                else:
                    invalidations.append(f"Realization of: {risk[:30]}")

        # Technical invalidations
        if evidence_pack.support_level:
            invalidations.append(
                f"Break below support level ({evidence_pack.support_level:.0f})"
            )

        return invalidations[:3]  # Top 3 invalidations
