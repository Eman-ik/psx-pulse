"""
Macro Foundation Engine - Sprint M8

Manage macroeconomic variables and their relationships to market sectors.
Track macro trends and identify macro-driven market movements.

Features:
- Macro series definition and tracking (GDP, inflation, rates, etc.)
- Macro observation recording (data points and dates)
- Sector macro exposure mapping
- Macro trend analysis and momentum
- Macro-sector correlation analysis
- Macro regime identification
- Macro driver impact assessment
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import date, timedelta
from enum import Enum


class MacroFrequency(str, Enum):
    """Data frequency for macro indicators."""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"


class MacroRegime(str, Enum):
    """Classification of macroeconomic regime."""
    STRONG_GROWTH = "STRONG_GROWTH"          # High growth, manageable inflation
    MODERATE_GROWTH = "MODERATE_GROWTH"      # Steady growth
    SLOW_GROWTH = "SLOW_GROWTH"              # Low growth, deflation risk
    STAGFLATION = "STAGFLATION"              # High inflation + low growth
    RECESSION = "RECESSION"                  # Contraction
    UNKNOWN = "UNKNOWN"                      # Insufficient data


class MacroFoundationEngine:
    """Manage macroeconomic indicators and their market impact."""

    # ════════════════════════════════════════════════════════════════════════════
    # MACRO SERIES MANAGEMENT
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_macro_series(
        series_code: str,
        series_name: str,
        category: str,
        frequency: MacroFrequency,
        unit: str = "%",
        description: Optional[str] = None,
    ) -> Dict:
        """
        Define a macro series.

        Args:
            series_code: Code for series (e.g., "GDP_PAK")
            series_name: Display name
            category: Category (Growth, Inflation, Rates, Employment, Trade, etc.)
            frequency: Data frequency
            unit: Unit of measurement (%, bps, index, etc.)
            description: Optional description

        Returns:
            Macro series definition
        """
        return {
            "series_code": series_code,
            "series_name": series_name,
            "category": category,
            "frequency": frequency,
            "unit": unit,
            "description": description,
            "created_at": date.today().isoformat(),
        }

    @staticmethod
    def record_macro_observation(
        series_code: str,
        observation_date: date,
        value: float,
        source: Optional[str] = None,
        confidence: float = 1.0,
    ) -> Dict:
        """
        Record a macro observation.

        Args:
            series_code: Series code
            observation_date: Date of observation
            value: Observation value
            source: Data source
            confidence: Confidence level (0-1)

        Returns:
            Recorded observation
        """
        return {
            "series_code": series_code,
            "observation_date": observation_date.isoformat(),
            "value": round(value, 4),
            "source": source,
            "confidence": round(confidence, 2),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # MACRO TREND ANALYSIS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def analyze_macro_trend(
        observations: List[Dict],
    ) -> Dict:
        """
        Analyze trend in macro variable.

        Args:
            observations: List of observations with 'value' and 'observation_date'

        Returns:
            Trend analysis
        """
        if len(observations) < 2:
            return {"error": "Insufficient data"}

        values = [obs["value"] for obs in observations]
        latest = values[-1]
        oldest = values[0]
        current_change = values[-1] - values[-2] if len(values) > 1 else 0

        # Calculate trend direction
        if len(values) >= 3:
            recent_avg = sum(values[-3:]) / 3
            older_avg = sum(values[:3]) / 3
            if recent_avg > older_avg * 1.02:
                trend = "IMPROVING"
            elif recent_avg < older_avg * 0.98:
                trend = "DETERIORATING"
            else:
                trend = "STABLE"
        else:
            trend = "INSUFFICIENT_DATA"

        return {
            "latest_value": round(latest, 4),
            "oldest_value": round(oldest, 4),
            "total_change": round(latest - oldest, 4),
            "change_pct": round((latest - oldest) / abs(oldest) * 100, 2) if oldest != 0 else 0,
            "current_period_change": round(current_change, 4),
            "trend": trend,
            "volatility": round(max(values) - min(values), 4) if values else 0,
        }

    @staticmethod
    def identify_macro_regime(
        growth_value: float,
        inflation_value: float,
        rate_value: Optional[float] = None,
    ) -> Dict:
        """
        Identify macroeconomic regime.

        Args:
            growth_value: Growth rate (%)
            inflation_value: Inflation rate (%)
            rate_value: Optional interest rate (%)

        Returns:
            Macro regime classification
        """
        if growth_value > 3.0 and inflation_value < 3.0:
            regime = MacroRegime.STRONG_GROWTH
            signal = "Healthy expansion with controlled inflation"
        elif growth_value > 1.0 and inflation_value < 4.0:
            regime = MacroRegime.MODERATE_GROWTH
            signal = "Steady growth conditions"
        elif growth_value < 1.0 and inflation_value < 2.0:
            regime = MacroRegime.SLOW_GROWTH
            signal = "Low growth with deflation risk"
        elif growth_value < 2.0 and inflation_value > 4.0:
            regime = MacroRegime.STAGFLATION
            signal = "Stagflationary pressures"
        elif growth_value < 0:
            regime = MacroRegime.RECESSION
            signal = "Economic contraction"
        else:
            regime = MacroRegime.UNKNOWN
            signal = "Regime unclear"

        return {
            "regime": regime,
            "growth_rate": round(growth_value, 2),
            "inflation_rate": round(inflation_value, 2),
            "interest_rate": round(rate_value, 2) if rate_value else None,
            "signal": signal,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # SECTOR MACRO EXPOSURE MAPPING
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def map_sector_macro_exposure(
        sector_name: str,
        macro_exposures: Dict[str, float],
    ) -> Dict:
        """
        Define sector's exposure to macro variables.

        Args:
            sector_name: Sector name (e.g., "Banking")
            macro_exposures: Dict of {macro_variable: sensitivity_score}
                            Sensitivity: -1 to +1 (negative = inverse, positive = direct)

        Returns:
            Sector macro exposure mapping
        """
        return {
            "sector_name": sector_name,
            "macro_exposures": {
                macro: round(exposure, 2)
                for macro, exposure in macro_exposures.items()
            },
            "total_exposure_magnitude": round(
                sum(abs(v) for v in macro_exposures.values()), 2
            ),
            "net_exposure": round(sum(macro_exposures.values()), 2),
        }

    @staticmethod
    def analyze_sector_macro_sensitivity(
        sector_exposures: Dict[str, float],
        macro_changes: Dict[str, float],
    ) -> Dict:
        """
        Calculate sector's expected move based on macro changes.

        Args:
            sector_exposures: Dict of {macro_variable: sensitivity}
            macro_changes: Dict of {macro_variable: change}

        Returns:
            Expected sector impact
        """
        expected_impact = 0
        impact_details = {}

        for macro_var, sensitivity in sector_exposures.items():
            change = macro_changes.get(macro_var, 0)
            impact = sensitivity * change
            expected_impact += impact

            impact_details[macro_var] = {
                "sensitivity": round(sensitivity, 2),
                "change": round(change, 2),
                "impact": round(impact, 2),
            }

        return {
            "expected_sector_impact": round(expected_impact, 2),
            "impact_direction": "POSITIVE" if expected_impact > 0 else "NEGATIVE" if expected_impact < 0 else "NEUTRAL",
            "impact_magnitude": abs(round(expected_impact, 2)),
            "impact_by_variable": impact_details,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # MACRO-DRIVEN ANALYSIS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def identify_macro_drivers(
        macro_changes: Dict[str, float],
        threshold: float = 0.5,
    ) -> List[Dict]:
        """
        Identify most significant macro drivers.

        Args:
            macro_changes: Dict of {macro_variable: change}
            threshold: Minimum absolute change to consider significant

        Returns:
            List of significant macro drivers
        """
        drivers = []

        for macro_var, change in macro_changes.items():
            if abs(change) > threshold:
                drivers.append({
                    "macro_variable": macro_var,
                    "change": round(change, 2),
                    "direction": "UP" if change > 0 else "DOWN",
                    "significance": "HIGH" if abs(change) > threshold * 2 else "MODERATE",
                })

        # Sort by absolute change
        drivers.sort(key=lambda x: abs(x["change"]), reverse=True)

        return drivers

    @staticmethod
    def calculate_macro_momentum(
        observations: List[Dict],
    ) -> Dict:
        """
        Calculate momentum of a macro variable.

        Args:
            observations: List of observations with 'value'

        Returns:
            Momentum metrics
        """
        if len(observations) < 3:
            return {"error": "Insufficient data"}

        values = [obs["value"] for obs in observations]

        # Split into periods
        mid_point = len(values) // 2
        first_half_avg = sum(values[:mid_point]) / len(values[:mid_point])
        second_half_avg = sum(values[mid_point:]) / len(values[mid_point:])

        momentum = second_half_avg - first_half_avg

        return {
            "first_period_avg": round(first_half_avg, 4),
            "second_period_avg": round(second_half_avg, 4),
            "momentum": round(momentum, 4),
            "accelerating": momentum > 0,
            "momentum_strength": "STRONG" if abs(momentum) > 1.0 else "MODERATE" if abs(momentum) > 0.5 else "WEAK",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # MACRO CORRELATION ANALYSIS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def analyze_sector_macro_correlation(
        sector_returns: List[float],
        macro_values: List[float],
    ) -> Dict:
        """
        Analyze correlation between sector and macro variable.

        Args:
            sector_returns: List of sector returns
            macro_values: List of macro values (aligned by date)

        Returns:
            Correlation analysis
        """
        if len(sector_returns) != len(macro_values) or len(sector_returns) < 2:
            return {"error": "Mismatched or insufficient data"}

        # Calculate correlation coefficient
        n = len(sector_returns)
        sector_mean = sum(sector_returns) / n
        macro_mean = sum(macro_values) / n

        covariance = sum(
            (sector_returns[i] - sector_mean) * (macro_values[i] - macro_mean)
            for i in range(n)
        ) / n

        sector_std = (sum((r - sector_mean) ** 2 for r in sector_returns) / n) ** 0.5
        macro_std = (sum((m - macro_mean) ** 2 for m in macro_values) / n) ** 0.5

        correlation = covariance / (sector_std * macro_std) if sector_std * macro_std > 0 else 0

        return {
            "correlation": round(correlation, 3),
            "relationship": "STRONG_POSITIVE" if correlation > 0.7 else "POSITIVE" if correlation > 0.3 else "WEAK" if correlation > -0.3 else "NEGATIVE" if correlation > -0.7 else "STRONG_NEGATIVE",
            "sector_avg_return": round(sector_mean, 2),
            "macro_avg_value": round(macro_mean, 4),
            "sector_volatility": round(sector_std, 2),
            "macro_volatility": round(macro_std, 4),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # MACRO FOUNDATION REPORT
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_macro_foundation_report(
        macro_data: Dict[str, List[Dict]],
        sector_exposures: Dict[str, Dict[str, float]],
        macro_changes: Dict[str, float],
    ) -> Dict:
        """
        Generate comprehensive macro foundation report.

        Args:
            macro_data: Dict of {series_code: observations_list}
            sector_exposures: Dict of {sector: {macro_var: sensitivity}}
            macro_changes: Dict of {macro_var: change}

        Returns:
            Comprehensive macro report
        """
        engine = MacroFoundationEngine()

        # Analyze macro trends
        macro_trends = {}
        for series_code, observations in macro_data.items():
            if observations:
                macro_trends[series_code] = engine.analyze_macro_trend(observations)

        # Identify macro drivers
        drivers = engine.identify_macro_drivers(macro_changes)

        # Analyze sector impacts
        sector_impacts = {}
        for sector, exposures in sector_exposures.items():
            impact = engine.analyze_sector_macro_sensitivity(exposures, macro_changes)
            sector_impacts[sector] = impact

        return {
            "date": date.today().isoformat(),
            "macro_trends": macro_trends,
            "macro_drivers": drivers,
            "sector_impacts": sector_impacts,
            "summary": {
                "total_macro_drivers": len(drivers),
                "positive_drivers": len([d for d in drivers if d["direction"] == "UP"]),
                "negative_drivers": len([d for d in drivers if d["direction"] == "DOWN"]),
                "most_affected_sector": max(
                    sector_impacts.items(),
                    key=lambda x: abs(x[1]["expected_sector_impact"])
                )[0] if sector_impacts else None,
            },
        }

    # ════════════════════════════════════════════════════════════════════════════
    # MACRO SCENARIO ANALYSIS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def run_macro_scenario(
        scenario_name: str,
        sector_exposures: Dict[str, Dict[str, float]],
        macro_changes: Dict[str, float],
    ) -> Dict:
        """
        Run scenario analysis on macro changes.

        Args:
            scenario_name: Name of scenario (e.g., "Rate Hike", "Recession")
            sector_exposures: Sector macro exposures
            macro_changes: Macro variable changes in this scenario

        Returns:
            Scenario impact analysis
        """
        engine = MacroFoundationEngine()

        sector_impacts = {}
        for sector, exposures in sector_exposures.items():
            impact = engine.analyze_sector_macro_sensitivity(exposures, macro_changes)
            sector_impacts[sector] = impact

        # Rank sectors by impact
        ranked_sectors = sorted(
            sector_impacts.items(),
            key=lambda x: abs(x[1]["expected_sector_impact"]),
            reverse=True
        )

        return {
            "scenario_name": scenario_name,
            "macro_assumptions": macro_changes,
            "sector_impacts": dict(ranked_sectors[:10]),
            "best_performers": [s[0] for s in ranked_sectors[:3] if s[1]["expected_sector_impact"] > 0],
            "worst_performers": [s[0] for s in ranked_sectors[:3] if s[1]["expected_sector_impact"] < 0],
        }
