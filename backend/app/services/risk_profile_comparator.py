"""Step 24: Risk Profile Comparator — Compare risk metrics across companies.

Risk analysis and scenario testing:
- Volatility vs peers
- Beta and correlation
- Downside scenarios (bear cases)
- Risk/reward ratios
- Maximum drawdown

Input: Historical prices + financial data
Output: RiskComparison (risk assessment)
"""

import logging
import statistics
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class DownsideScenario:
    """Downside scenario analysis."""

    scenario_name: str  # "Recession", "Sector Downturn", etc.
    probability_pct: float  # 0-100%
    impact_pct: float  # Negative percentage change expected


@dataclass
class RiskComparison:
    """Complete risk profile comparison."""

    ticker: str
    company_name: str

    # Volatility metrics
    volatility_pct: float  # Price volatility (annualized)
    beta: float  # vs market (1.0 = market)
    correlation_to_market: float  # -1 to 1

    # Drawdown metrics
    maximum_drawdown_pct: float  # Worst peak-to-trough
    average_drawdown_pct: float  # Average of all drawdowns

    # Scenario analysis
    downside_scenarios: List[DownsideScenario] = None
    worst_case_impact_pct: float = 0.0

    # Financial risk
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None
    current_ratio: Optional[float] = None

    # Risk rating
    risk_rating: str = "Medium"  # Low/Medium/High/Very High
    overall_risk_score: float = 50.0  # 0-100%

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "volatility_pct": round(self.volatility_pct, 1),
            "beta": round(self.beta, 2),
            "max_drawdown_pct": round(self.maximum_drawdown_pct, 1),
            "debt_to_equity": round(self.debt_to_equity, 2) if self.debt_to_equity else None,
            "interest_coverage": round(self.interest_coverage, 2) if self.interest_coverage else None,
            "risk_rating": self.risk_rating,
            "overall_risk_score": round(self.overall_risk_score, 1),
            "scenarios": [
                {
                    "scenario": s.scenario_name,
                    "probability": round(s.probability_pct, 1),
                    "impact": round(s.impact_pct, 1),
                }
                for s in (self.downside_scenarios or [])
            ],
        }


class RiskProfileComparator:
    """Analyzes and compares risk profiles."""

    def __init__(self):
        """Initialize risk comparator."""
        self.logger = logging.getLogger(__name__)

    def analyze_risk(
        self,
        ticker: str,
        company_name: str,
        price_history: List[float],
        beta: Optional[float] = None,
        debt_to_equity: Optional[float] = None,
        interest_coverage: Optional[float] = None,
        current_ratio: Optional[float] = None,
    ) -> Optional[RiskComparison]:
        """Analyze risk profile.

        Args:
            ticker: Company ticker
            company_name: Company name
            price_history: Historical stock prices
            beta: Beta vs market (None = estimate from volatility)
            debt_to_equity: Debt-to-equity ratio
            interest_coverage: Interest coverage ratio
            current_ratio: Current ratio

        Returns:
            RiskComparison with risk assessment
        """
        try:
            if not price_history or len(price_history) < 2:
                return None

            analysis = RiskComparison(
                ticker=ticker,
                company_name=company_name,
                volatility_pct=0.0,
                beta=beta or 1.0,
                correlation_to_market=0.0,
                maximum_drawdown_pct=0.0,
                average_drawdown_pct=0.0,
                debt_to_equity=debt_to_equity,
                interest_coverage=interest_coverage,
                current_ratio=current_ratio,
            )

            # Calculate volatility
            returns = self._calculate_returns(price_history)
            if returns:
                analysis.volatility_pct = self._calculate_volatility(returns)

            # Calculate drawdowns
            drawdowns = self._calculate_drawdowns(price_history)
            if drawdowns:
                analysis.maximum_drawdown_pct = min(drawdowns)
                analysis.average_drawdown_pct = sum(drawdowns) / len(drawdowns)

            # Generate downside scenarios
            analysis.downside_scenarios = self._generate_downside_scenarios(
                analysis
            )

            # Calculate worst case
            analysis.worst_case_impact_pct = min(
                [s.impact_pct for s in analysis.downside_scenarios]
                if analysis.downside_scenarios
                else [0]
            )

            # Determine risk rating
            analysis.risk_rating = self._determine_risk_rating(analysis)

            # Calculate overall risk score
            analysis.overall_risk_score = self._calculate_risk_score(
                analysis
            )

            self.logger.info(
                f"Analyzed risk for {ticker}: volatility {analysis.volatility_pct:.1f}%, "
                f"max drawdown {analysis.maximum_drawdown_pct:.1f}%, "
                f"rating {analysis.risk_rating}"
            )
            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing risk: {e}")
            return None

    @staticmethod
    def _calculate_returns(price_history: List[float]) -> List[float]:
        """Calculate period returns."""
        returns = []
        for i in range(1, len(price_history)):
            if price_history[i - 1] > 0:
                ret = (price_history[i] - price_history[i - 1]) / price_history[i - 1]
                returns.append(ret)
        return returns

    @staticmethod
    def _calculate_volatility(returns: List[float]) -> float:
        """Calculate annualized volatility."""
        if len(returns) < 2:
            return 0.0

        mean_return = statistics.mean(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (
            len(returns) - 1
        )
        stdev = variance ** 0.5

        # Annualize (assume 252 trading days)
        annualized = stdev * (252 ** 0.5) * 100

        return annualized

    @staticmethod
    def _calculate_drawdowns(price_history: List[float]) -> List[float]:
        """Calculate drawdowns from peak."""
        drawdowns = []
        peak = price_history[0]

        for price in price_history[1:]:
            if price > peak:
                peak = price
            drawdown = (price - peak) / peak if peak > 0 else 0
            drawdowns.append(drawdown)

        return drawdowns

    @staticmethod
    def _generate_downside_scenarios(
        analysis: "RiskComparison",
    ) -> List[DownsideScenario]:
        """Generate potential downside scenarios."""
        scenarios = []

        # Recession scenario (30% probability, -20% impact)
        scenarios.append(
            DownsideScenario(
                scenario_name="Recession",
                probability_pct=30.0,
                impact_pct=-20.0,
            )
        )

        # Sector downturn (40% probability, varies)
        sector_impact = -15.0
        scenarios.append(
            DownsideScenario(
                scenario_name="Sector Downturn",
                probability_pct=40.0,
                impact_pct=sector_impact,
            )
        )

        # Company-specific (20% probability, worse of drawdown)
        company_impact = min(-10.0, analysis.maximum_drawdown_pct)
        scenarios.append(
            DownsideScenario(
                scenario_name="Company-Specific Risk",
                probability_pct=20.0,
                impact_pct=company_impact,
            )
        )

        return scenarios

    @staticmethod
    def _determine_risk_rating(analysis: RiskComparison) -> str:
        """Determine risk rating."""
        risk_score = 0

        # Volatility contribution
        if analysis.volatility_pct > 40:
            risk_score += 30
        elif analysis.volatility_pct > 25:
            risk_score += 20
        elif analysis.volatility_pct > 15:
            risk_score += 10

        # Drawdown contribution
        if analysis.maximum_drawdown_pct < -30:
            risk_score += 25
        elif analysis.maximum_drawdown_pct < -20:
            risk_score += 15
        elif analysis.maximum_drawdown_pct < -10:
            risk_score += 10

        # Financial risk (leverage)
        if analysis.debt_to_equity and analysis.debt_to_equity > 2:
            risk_score += 25
        elif analysis.debt_to_equity and analysis.debt_to_equity > 1:
            risk_score += 15

        # Interest coverage
        if (
            analysis.interest_coverage
            and analysis.interest_coverage < 2
        ):
            risk_score += 20

        if risk_score >= 60:
            return "Very High"
        elif risk_score >= 40:
            return "High"
        elif risk_score >= 20:
            return "Medium"
        else:
            return "Low"

    @staticmethod
    def _calculate_risk_score(analysis: RiskComparison) -> float:
        """Calculate overall risk score (0-100%)."""
        score = 0.0

        # Volatility (0-30 points)
        score += min(30, analysis.volatility_pct)

        # Drawdown (0-30 points)
        score += min(30, abs(analysis.maximum_drawdown_pct) * 100)

        # Leverage (0-20 points)
        if analysis.debt_to_equity:
            score += min(20, analysis.debt_to_equity * 10)

        # Interest coverage (0-20 points)
        if analysis.interest_coverage:
            if analysis.interest_coverage < 1:
                score += 20
            else:
                score += max(0, 20 - (analysis.interest_coverage * 5))

        return min(100, score)
