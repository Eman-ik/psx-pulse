"""
Scenario Valuation Analysis

Sprint V3: Scenario-based valuation (bear/base/bull cases).

Features:
- Define earnings scenarios (conservative, base, optimistic)
- Apply valuation multiples to scenarios
- Generate implied price ranges
- Track scenario assumptions
- Compare scenarios to current valuation
"""

from decimal import Decimal
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

from .schema import Security


class ValuationScenario:
    """Single scenario valuation (bear/base/bull)."""

    def __init__(
        self,
        name: str,
        eps_assumption: Decimal,
        pe_multiple: Decimal,
        eps_growth_rate: Optional[Decimal] = None,
        description: Optional[str] = None
    ):
        """
        Initialize scenario.

        Args:
            name: Scenario name ("Bear", "Base", "Bull")
            eps_assumption: Expected EPS (TTM or forward)
            pe_multiple: Valuation multiple to apply
            eps_growth_rate: Expected growth rate (%)
            description: Scenario rationale
        """
        self.name = name
        self.eps_assumption = Decimal(eps_assumption)
        self.pe_multiple = Decimal(pe_multiple)
        self.eps_growth_rate = Decimal(eps_growth_rate) if eps_growth_rate else None
        self.description = description

    def calculate_implied_price(self) -> Decimal:
        """Calculate implied share price = EPS × Multiple."""
        return self.eps_assumption * self.pe_multiple

    def to_dict(self) -> Dict:
        """Convert scenario to dictionary."""
        return {
            "name": self.name,
            "eps_assumption": float(self.eps_assumption),
            "pe_multiple": float(self.pe_multiple),
            "implied_price": float(self.calculate_implied_price()),
            "eps_growth_rate": float(self.eps_growth_rate) if self.eps_growth_rate else None,
            "description": self.description,
        }


class ScenarioAnalyzer:
    """Analyze valuations across scenarios."""

    def __init__(self, session: Session):
        self.session = session

    def create_standard_scenarios(
        self,
        current_eps: Decimal,
        current_pe: Decimal,
        current_price: Decimal
    ) -> Dict[str, ValuationScenario]:
        """
        Create standard bear/base/bull scenarios.

        Scenarios:
        - Bear: -20% EPS, -1.0x multiple
        - Base: Current EPS, current multiple
        - Bull: +20% EPS, +1.0x multiple
        """
        bear_eps = current_eps * Decimal("0.8")  # 80% of current
        bear_multiple = current_pe - Decimal("1.0")
        bear = ValuationScenario(
            name="Bear",
            eps_assumption=bear_eps,
            pe_multiple=max(bear_multiple, Decimal("1.0")),  # Min 1.0x
            eps_growth_rate=Decimal("-20"),
            description="Conservative case: 20% lower earnings, lower multiple"
        )

        base = ValuationScenario(
            name="Base",
            eps_assumption=current_eps,
            pe_multiple=current_pe,
            eps_growth_rate=Decimal("0"),
            description="Base case: current earnings and multiple"
        )

        bull_eps = current_eps * Decimal("1.2")  # 120% of current
        bull_multiple = current_pe + Decimal("1.0")
        bull = ValuationScenario(
            name="Bull",
            eps_assumption=bull_eps,
            pe_multiple=bull_multiple,
            eps_growth_rate=Decimal("20"),
            description="Optimistic case: 20% higher earnings, higher multiple"
        )

        return {
            "bear": bear,
            "base": base,
            "bull": bull,
        }

    def create_custom_scenarios(
        self,
        scenarios_data: List[Dict]
    ) -> List[ValuationScenario]:
        """
        Create custom scenarios from data.

        Expected format:
        [
            {
                "name": "Bear",
                "eps_assumption": 15.0,
                "pe_multiple": 7.0,
                "eps_growth_rate": -20,
                "description": "..."
            },
            ...
        ]
        """
        scenarios = []
        for data in scenarios_data:
            scenario = ValuationScenario(
                name=data["name"],
                eps_assumption=Decimal(str(data["eps_assumption"])),
                pe_multiple=Decimal(str(data["pe_multiple"])),
                eps_growth_rate=data.get("eps_growth_rate"),
                description=data.get("description")
            )
            scenarios.append(scenario)
        return scenarios

    def analyze_scenarios(
        self,
        scenarios: Dict[str, ValuationScenario],
        current_price: Decimal
    ) -> Dict:
        """
        Analyze scenarios and compare to current price.

        Returns valuation range and implied return/loss.
        """
        results = {}

        for name, scenario in scenarios.items():
            implied_price = scenario.calculate_implied_price()
            upside_downside = (
                ((implied_price - current_price) / current_price) * 100
                if current_price > 0 else 0
            )

            results[name] = {
                "scenario": scenario.to_dict(),
                "implied_price": float(implied_price),
                "current_price": float(current_price),
                "upside_downside_pct": round(upside_downside, 2),
                "upside_downside_abs": float(implied_price - current_price),
            }

        # Calculate range
        prices = [v["implied_price"] for v in results.values()]
        results["summary"] = {
            "current_price": float(current_price),
            "fair_value_range": {
                "low": float(Decimal(str(min(prices)))),
                "high": float(Decimal(str(max(prices)))),
                "midpoint": float(Decimal(str(sum(prices) / len(prices)))),
            },
            "upside_scenario": max(results.keys(), key=lambda k: results[k]["upside_downside_pct"]),
            "downside_scenario": min(results.keys(), key=lambda k: results[k]["upside_downside_pct"]),
        }

        return results

    def scenario_sensitivity_analysis(
        self,
        base_eps: Decimal,
        base_multiple: Decimal,
        current_price: Decimal,
        eps_range: Tuple[Decimal, Decimal],
        multiple_range: Tuple[Decimal, Decimal]
    ) -> Dict:
        """
        Create sensitivity matrix for EPS × Multiple combinations.

        Shows how valuation changes with different EPS and multiple assumptions.
        """
        eps_low, eps_high = eps_range
        mult_low, mult_high = multiple_range

        # Create steps
        eps_steps = [
            eps_low,
            (eps_low + base_eps) / 2,
            base_eps,
            (base_eps + eps_high) / 2,
            eps_high,
        ]

        multiple_steps = [
            mult_low,
            (mult_low + base_multiple) / 2,
            base_multiple,
            (base_multiple + mult_high) / 2,
            mult_high,
        ]

        # Create matrix
        matrix = {}
        for eps in eps_steps:
            eps_key = f"EPS_{float(eps):.1f}"
            matrix[eps_key] = {}
            for multiple in multiple_steps:
                implied_price = eps * multiple
                mult_key = f"{float(multiple):.1f}x"
                upside = (
                    ((implied_price - current_price) / current_price) * 100
                    if current_price > 0 else 0
                )
                matrix[eps_key][mult_key] = {
                    "price": float(implied_price),
                    "upside_pct": round(upside, 1),
                }

        return {
            "base_eps": float(base_eps),
            "base_multiple": float(base_multiple),
            "current_price": float(current_price),
            "eps_range": (float(eps_low), float(eps_high)),
            "multiple_range": (float(mult_low), float(mult_high)),
            "sensitivity_matrix": matrix,
        }

    def generate_scenario_report(
        self,
        security_id: int,
        current_price: Decimal,
        current_eps: Decimal,
        current_multiple: Decimal
    ) -> Dict:
        """Generate complete scenario analysis report."""
        # Create scenarios
        scenarios = self.create_standard_scenarios(current_eps, current_multiple, current_price)

        # Analyze
        analysis = self.analyze_scenarios(scenarios, current_price)

        # Sensitivity
        sensitivity = self.scenario_sensitivity_analysis(
            current_eps,
            current_multiple,
            current_price,
            eps_range=(current_eps * Decimal("0.7"), current_eps * Decimal("1.3")),
            multiple_range=(current_multiple - Decimal("2.0"), current_multiple + Decimal("2.0"))
        )

        return {
            "security_id": security_id,
            "analysis_date": datetime.now().isoformat(),
            "current_price": float(current_price),
            "current_eps": float(current_eps),
            "current_pe": float(current_multiple),
            "scenario_analysis": analysis,
            "sensitivity_analysis": sensitivity,
        }


class NormalizedEarningsAnalyzer:
    """Analyze normalized vs reported earnings."""

    def __init__(self, session: Session):
        self.session = session

    def identify_one_offs(
        self,
        reported_eps: Decimal,
        one_off_items: List[Dict]
    ) -> Decimal:
        """
        Calculate impact of one-off items.

        One-off items format:
        [
            {"description": "Land sale", "eps_impact": 5.0, "type": "gain"},
            {"description": "Restructuring", "eps_impact": -2.0, "type": "charge"},
            ...
        ]
        """
        total_impact = Decimal("0")

        for item in one_off_items:
            impact = Decimal(str(item["eps_impact"]))
            total_impact += impact

        return total_impact

    def calculate_normalized_eps(
        self,
        reported_eps: Decimal,
        one_off_items: List[Dict]
    ) -> Decimal:
        """Calculate normalized EPS (removing one-off items)."""
        one_off_impact = self.identify_one_offs(reported_eps, one_off_items)
        normalized = reported_eps - one_off_impact
        return normalized

    def generate_normalization_report(
        self,
        reported_eps: Decimal,
        one_off_items: List[Dict],
        reported_pe: Decimal
    ) -> Dict:
        """Generate normalization analysis report."""
        total_impact = self.identify_one_offs(reported_eps, one_off_items)
        normalized_eps = self.calculate_normalized_eps(reported_eps, one_off_items)

        # Calculate multiples
        normalized_pe = reported_pe if normalized_eps == 0 else (
            (reported_eps / normalized_eps) * reported_pe
        )

        impact_pct = (
            (total_impact / reported_eps) * 100
            if reported_eps != 0 else 0
        )

        return {
            "reported_eps": float(reported_eps),
            "reported_pe": float(reported_pe),
            "one_off_items": one_off_items,
            "total_one_off_impact": float(total_impact),
            "impact_as_pct_of_earnings": round(impact_pct, 2),
            "normalized_eps": float(normalized_eps),
            "normalized_pe": float(normalized_pe) if normalized_eps != 0 else None,
            "interpretation": self._get_interpretation(impact_pct),
        }

    def _get_interpretation(self, impact_pct: float) -> str:
        """Interpret significance of one-offs."""
        if abs(impact_pct) < 3:
            return "Minimal impact - earnings quality intact"
        elif abs(impact_pct) < 10:
            return "Moderate impact - one-offs material but not dominant"
        elif impact_pct > 0:
            return "Significant positive impact - reported earnings inflated"
        else:
            return "Significant negative impact - true earnings better than reported"


class QualityValuationMatrix:
    """Quality vs Valuation 2D framework."""

    def __init__(self, session: Session):
        self.session = session

    def calculate_quality_score(
        self,
        roe: Decimal,
        revenue_growth: Decimal,
        margin: Decimal,
        debt_to_equity: Decimal
    ) -> float:
        """
        Calculate quality score (0-100).

        Factors:
        - ROE: High is good (20%+ = high quality)
        - Revenue growth: High is good (10%+ = good)
        - Margins: High is good (20%+ = excellent)
        - Leverage: Low is good (D/E < 1.0 = good)
        """
        score = 0

        # ROE component (max 25 points)
        roe_float = float(roe)
        if roe_float >= 20:
            score += 25
        elif roe_float >= 15:
            score += 20
        elif roe_float >= 10:
            score += 15
        elif roe_float >= 5:
            score += 10
        else:
            score += 5

        # Revenue growth component (max 25 points)
        growth_float = float(revenue_growth)
        if growth_float >= 20:
            score += 25
        elif growth_float >= 15:
            score += 20
        elif growth_float >= 10:
            score += 15
        elif growth_float >= 5:
            score += 10
        else:
            score += 5

        # Margin component (max 25 points)
        margin_float = float(margin)
        if margin_float >= 20:
            score += 25
        elif margin_float >= 15:
            score += 20
        elif margin_float >= 10:
            score += 15
        elif margin_float >= 5:
            score += 10
        else:
            score += 5

        # Leverage component (max 25 points)
        de_float = float(debt_to_equity)
        if de_float <= 0.5:
            score += 25
        elif de_float <= 1.0:
            score += 20
        elif de_float <= 1.5:
            score += 15
        elif de_float <= 2.0:
            score += 10
        else:
            score += 5

        return float(score)

    def get_valuation_category(self, pe_ratio: Decimal) -> str:
        """Categorize valuation as cheap/fair/expensive."""
        pe_float = float(pe_ratio)
        if pe_float < 10:
            return "Cheap"
        elif pe_float < 15:
            return "Fair"
        else:
            return "Expensive"

    def generate_matrix_position(
        self,
        quality_score: float,
        valuation_pe: Decimal
    ) -> Dict:
        """
        Generate position in quality/valuation matrix.

        Returns quadrant and recommendation.
        """
        # Normalize quality score to 0-100
        quality_norm = quality_score / 100

        # Determine quadrants
        valuation_cat = self.get_valuation_category(valuation_pe)

        # Quality categories
        if quality_norm >= 0.75:
            quality_cat = "High"
            quality_level = 3
        elif quality_norm >= 0.50:
            quality_cat = "Medium"
            quality_level = 2
        else:
            quality_cat = "Low"
            quality_level = 1

        # Valuation levels
        if valuation_cat == "Cheap":
            valuation_level = 1
        elif valuation_cat == "Fair":
            valuation_level = 2
        else:
            valuation_level = 3

        # Generate position and recommendation
        quadrant = f"{quality_cat}_Quality_{valuation_cat}_Valuation"
        recommendation = self._get_recommendation(quality_level, valuation_level)

        return {
            "quality_score": quality_score,
            "quality_category": quality_cat,
            "valuation_category": valuation_cat,
            "valuation_pe": float(valuation_pe),
            "quadrant": quadrant,
            "recommendation": recommendation,
            "matrix_position": {
                "x": float(valuation_pe),  # X-axis: valuation
                "y": quality_score,         # Y-axis: quality
            },
        }

    def _get_recommendation(self, quality_level: int, valuation_level: int) -> str:
        """Get recommendation based on quality/valuation position."""
        matrix = {
            (3, 1): "Strong Buy - Quality company at cheap valuation",
            (3, 2): "Buy - Quality company at fair valuation",
            (3, 3): "Hold/Reduce - Quality company but expensive",
            (2, 1): "Buy - Fair quality at cheap valuation",
            (2, 2): "Hold - Fair quality at fair valuation",
            (2, 3): "Reduce - Fair quality but expensive",
            (1, 1): "Speculative - Low quality even if cheap",
            (1, 2): "Avoid - Low quality at fair valuation",
            (1, 3): "Avoid - Low quality at expensive valuation",
        }
        return matrix.get((quality_level, valuation_level), "Unknown")
