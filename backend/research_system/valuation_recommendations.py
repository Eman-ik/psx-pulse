"""
Fair Value Recommendations & Price Targets

Sprint V5: Generate actionable price targets with support/resistance levels,
investment ratings, and risk/reward analysis.

Features:
- Weighted fair value from multiple valuation methods
- Support/target/resistance price levels
- Buy/Hold/Sell recommendations
- Sensitivity analysis
- Risk/reward assessment
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Session

from .schema import Security, ValuationSnapshot


class InvestmentRating(str, Enum):
    """Investment rating classification."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class FairValueRecommendations:
    """Generate investment recommendations and price targets."""

    def __init__(self, session: Session):
        self.session = session

    def generate_fair_value_targets(
        self,
        ticker: str,
        methods: Dict[str, Dict],
        support_margin: Decimal = Decimal("12"),
        resistance_margin: Decimal = Decimal("10"),
    ) -> Dict:
        """
        Generate fair value and support/resistance levels from multiple methods.

        Args:
            ticker: Company ticker
            methods: Dict of valuation methods with weights and values
                    {
                        "ddm": {"weight": 0.30, "value": Decimal("52.0")},
                        "dcf": {"weight": 0.30, "value": Decimal("55.5")},
                        ...
                    }
            support_margin: Percentage below fair value for support level (%)
            resistance_margin: Percentage above fair value for resistance level (%)

        Returns:
            Dict with fair value, targets, and confidence level
        """
        if not methods:
            raise ValueError("At least one valuation method required")

        # Validate weights sum to 1.0
        total_weight = sum(m["weight"] for m in methods.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        # Calculate weighted fair value
        weighted_fair_value = Decimal(0)
        method_contributions = {}

        for method_name, method_data in methods.items():
            value = Decimal(str(method_data["value"]))
            weight = Decimal(str(method_data["weight"]))
            contribution = value * weight
            weighted_fair_value += contribution
            method_contributions[method_name] = {
                "value": float(value),
                "weight": float(weight),
                "contribution": float(contribution),
            }

        fair_value = weighted_fair_value.quantize(Decimal("0.01"))

        # Calculate support and resistance
        support_pct = (Decimal(100) - support_margin) / Decimal(100)
        resistance_pct = (Decimal(100) + resistance_margin) / Decimal(100)

        support = (fair_value * support_pct).quantize(Decimal("0.01"))
        resistance = (fair_value * resistance_pct).quantize(Decimal("0.01"))

        # Confidence based on method agreement
        values = [Decimal(str(m["value"])) for m in methods.values()]
        dispersion = self._calculate_dispersion(values)

        if dispersion < 0.05:  # < 5% spread
            confidence = "HIGH"
        elif dispersion < 0.10:  # < 10% spread
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        # Valuation range (conservative/base/optimistic)
        conservative = min(values)
        optimistic = max(values)
        valuation_range = {
            "conservative": float(conservative),
            "base_case": float(fair_value),
            "optimistic": float(optimistic),
        }

        return {
            "ticker": ticker,
            "fair_value": float(fair_value),
            "support": float(support),
            "target": float(fair_value),
            "resistance": float(resistance),
            "support_margin_pct": float(support_margin),
            "resistance_margin_pct": float(resistance_margin),
            "weighted_methods": method_contributions,
            "confidence": confidence,
            "method_dispersion_pct": round(dispersion * 100, 2),
            "valuation_range": valuation_range,
        }

    def get_investment_recommendation(
        self,
        ticker: str,
        current_price: Decimal,
        fair_value_targets: Dict,
        margin_of_safety: Decimal = Decimal("15"),
    ) -> Dict:
        """
        Generate Buy/Hold/Sell recommendation based on current price vs targets.

        Args:
            ticker: Company ticker
            current_price: Current stock price (PKR)
            fair_value_targets: Output from generate_fair_value_targets()
            margin_of_safety: Minimum upside required to buy (%)

        Returns:
            Investment recommendation with rating and justification
        """
        fair_value = Decimal(str(fair_value_targets["fair_value"]))
        support = Decimal(str(fair_value_targets["support"]))
        resistance = Decimal(str(fair_value_targets["resistance"]))

        current = Decimal(str(current_price))

        # Calculate upside/downside
        upside_pct = ((fair_value - current) / current * Decimal(100)).quantize(Decimal("0.01"))
        downside_pct = ((current - support) / current * Decimal(100)).quantize(Decimal("0.01"))

        # Calculate risk/reward ratio
        if downside_pct > 0:
            risk_reward = abs(upside_pct) / downside_pct
        else:
            risk_reward = 0

        # Determine rating
        if upside_pct >= margin_of_safety:
            rating = InvestmentRating.BUY
            if upside_pct >= margin_of_safety * Decimal("1.5"):
                rating = InvestmentRating.STRONG_BUY
            summary = f"Stock trading below fair value; attractive entry at {upside_pct}% upside to base case"

        elif upside_pct >= 0:
            rating = InvestmentRating.HOLD
            summary = f"Stock trading near fair value ({upside_pct:.1f}% upside); hold existing positions"

        elif abs(upside_pct) < margin_of_safety * Decimal("0.5"):
            rating = InvestmentRating.HOLD
            summary = f"Stock trading slightly above fair value; hold for dividend income"

        elif abs(upside_pct) >= margin_of_safety * Decimal("1.5"):
            rating = InvestmentRating.STRONG_SELL
            summary = f"Stock significantly overvalued; exit positions ({abs(upside_pct):.1f}% downside)"

        else:
            rating = InvestmentRating.SELL
            summary = f"Stock trading above fair value; reduce positions ({abs(upside_pct):.1f}% downside)"

        return {
            "ticker": ticker,
            "current_price": float(current),
            "fair_value": float(fair_value),
            "support": float(support),
            "resistance": float(resistance),
            "rating": rating.value,
            "upside_downside_pct": float(upside_pct),
            "upside_downside_abs": float(fair_value - current),
            "risk_reward_ratio": round(risk_reward, 2),
            "summary": summary,
            "target_price": float(fair_value),
            "price_target_summary": {
                "resistance": float(resistance),
                "fair_value": float(fair_value),
                "support": float(support),
            },
        }

    def generate_price_target_sensitivity(
        self,
        ticker: str,
        base_case_assumptions: Dict[str, Decimal],
        sensitivity_ranges: Dict[str, Tuple[Decimal, Decimal]],
        base_fair_value: Decimal,
        method_func=None,
    ) -> Dict:
        """
        Perform sensitivity analysis on price targets.

        Shows how valuation changes with different assumptions about key variables.

        Args:
            ticker: Company ticker
            base_case_assumptions: Base case assumption values
                                  {"terminal_growth": 3%, "discount_rate": 10%, ...}
            sensitivity_ranges: Range for sensitivity analysis
                               {"terminal_growth": (2%, 4%), ...}
            base_fair_value: Base case fair value (PKR)
            method_func: Optional custom function to calculate value from assumptions

        Returns:
            Sensitivity analysis matrix and interpretation
        """
        if not sensitivity_ranges:
            raise ValueError("At least one sensitivity variable required")

        base_value = float(base_fair_value)

        # Get the first two sensitivity variables for 2D matrix
        vars_to_analyze = list(sensitivity_ranges.keys())[:2]

        if len(vars_to_analyze) < 2:
            vars_to_analyze.append(list(sensitivity_ranges.keys())[0])

        var1, var2 = vars_to_analyze[0], vars_to_analyze[1]
        var1_range = sensitivity_ranges[var1]
        var2_range = sensitivity_ranges[var2]

        # Create sensitivity matrix
        sensitivity_matrix = {}

        # Generate value points for matrix
        var1_values = [
            var1_range[0] + (var1_range[1] - var1_range[0]) * i / 4
            for i in range(5)
        ]
        var2_values = [
            var2_range[0] + (var2_range[1] - var2_range[0]) * i / 4
            for i in range(5)
        ]

        # Create matrix (simplified: calculate sensitivity with linear assumptions)
        matrix = []
        for v2 in var2_values:
            row = []
            for v1 in var1_values:
                # Simple sensitivity: change base value proportionally
                # In production, this would call the actual valuation method
                adjustment1 = (float(v1 - base_case_assumptions[var1]) / float(
                    base_case_assumptions[var1]
                )) if base_case_assumptions[var1] != 0 else 0
                adjustment2 = (float(v2 - base_case_assumptions[var2]) / float(
                    base_case_assumptions[var2]
                )) if base_case_assumptions[var2] != 0 else 0

                # Simple formula: base * (1 + avg adjustment)
                adjusted_value = base_value * (1 + (adjustment1 + adjustment2) / 2)
                row.append(round(adjusted_value, 2))
            matrix.append(row)

        # Calculate percentile position of base case
        all_values = [v for row in matrix for v in row]
        base_percentile = (
            sum(1 for v in all_values if v <= base_value) / len(all_values) * 100
        )

        # Calculate range
        min_value = min(all_values)
        max_value = max(all_values)

        return {
            "ticker": ticker,
            "base_case_value": base_value,
            "base_case_assumptions": {k: float(v) for k, v in base_case_assumptions.items()},
            "sensitivity_variable_1": var1,
            "sensitivity_variable_2": var2,
            "sensitivity_variable_1_range": (float(var1_range[0]), float(var1_range[1])),
            "sensitivity_variable_2_range": (float(var2_range[0]), float(var2_range[1])),
            "sensitivity_matrix": matrix,
            "value_range": {
                "minimum": min_value,
                "maximum": max_value,
                "range": max_value - min_value,
            },
            "base_case_percentile": round(base_percentile, 1),
            "interpretation": self._interpret_sensitivity(base_percentile, min_value, max_value, base_value),
        }

    def compare_valuations(
        self,
        ticker: str,
        historical_targets: List[Dict],
        current_fair_value: Decimal,
        current_price: Decimal,
    ) -> Dict:
        """
        Compare current valuation to historical targets.

        Args:
            ticker: Company ticker
            historical_targets: List of past fair value targets with dates
            current_fair_value: Current calculated fair value
            current_price: Current stock price

        Returns:
            Comparison analysis and trends
        """
        if not historical_targets:
            return {"error": "No historical targets provided"}

        target_values = [t["fair_value"] for t in historical_targets]
        avg_historical = sum(target_values) / len(target_values)
        min_historical = min(target_values)
        max_historical = max(target_values)

        current_fv = float(current_fair_value)

        # Trend
        if len(target_values) >= 2:
            recent_targets = target_values[-3:]
            recent_avg = sum(recent_targets) / len(recent_targets)
            historical_avg = sum(target_values[:-3]) / (len(target_values) - 3) if len(
                target_values
            ) > 3 else recent_avg
            trend = "increasing" if recent_avg > historical_avg else "decreasing"
            trend_magnitude = abs(recent_avg - historical_avg) / historical_avg * 100
        else:
            trend = "insufficient_data"
            trend_magnitude = 0

        return {
            "ticker": ticker,
            "current_fair_value": current_fv,
            "current_price": float(current_price),
            "historical_average": round(avg_historical, 2),
            "historical_range": {
                "minimum": min_historical,
                "maximum": max_historical,
                "range": max_historical - min_historical,
            },
            "current_vs_historical_avg": round(current_fv - avg_historical, 2),
            "current_percentile": round(
                (sum(1 for t in target_values if t <= current_fv) / len(target_values) * 100),
                1,
            ),
            "trend": trend,
            "trend_magnitude_pct": round(trend_magnitude, 2),
            "interpretation": self._interpret_valuation_trend(current_fv, avg_historical, trend),
        }

    @staticmethod
    def _calculate_dispersion(values: List[Decimal]) -> float:
        """Calculate coefficient of variation (std dev / mean)."""
        if not values or len(values) < 2:
            return 0

        mean = sum(values) / len(values)
        if mean == 0:
            return 0

        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance.sqrt()
        return float(std_dev / mean)

    @staticmethod
    def _interpret_sensitivity(percentile: float, min_val: float, max_val: float, base: float) -> str:
        """Generate interpretation of sensitivity analysis."""
        if percentile < 25:
            return f"Base case value ({base}) is in the lower quartile of sensitivity range ({min_val}-{max_val}); downside risk if assumptions worse"
        elif percentile < 50:
            return f"Base case value is below median; conservative estimate with reasonable margin of safety"
        elif percentile < 75:
            return f"Base case value is above median; optimistic relative to sensitivity range"
        else:
            return f"Base case value is in upper quartile; assumes favorable conditions"

    @staticmethod
    def _interpret_valuation_trend(current: float, historical_avg: float, trend: str) -> str:
        """Generate interpretation of valuation trend."""
        diff_pct = abs(current - historical_avg) / historical_avg * 100

        if trend == "increasing":
            if diff_pct > 10:
                return f"Fair value increasing significantly; valuation metrics deteriorating"
            else:
                return f"Fair value increasing modestly; gradual deterioration in relative valuation"
        elif trend == "decreasing":
            if diff_pct > 10:
                return f"Fair value decreasing significantly; valuation becoming more attractive"
            else:
                return f"Fair value decreasing modestly; gradual improvement in valuation"
        else:
            return f"Insufficient trend data; current value {diff_pct:.1f}% vs historical average"
