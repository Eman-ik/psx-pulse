"""
Screener Engine - Module 5: Discovery & Screening

Comprehensive stock discovery and screening system.
Combines Modules 1-4 into intelligent multi-criteria filtering.

Sprints S1-S6:
- S1: Screening Snapshot (daily pre-calculated metrics)
- S2: Universe + Liquidity Filters
- S3: Fundamental Filters
- S4: Valuation Filters
- S5: Technical Filters
- S6: Relative Strength Filters

Key Design:
- Transparent rule-based screening (no AI/black box)
- Sector-relative and historical-relative filtering
- Combined Boolean logic (AND/OR/NOT)
- Data quality constraints
- Change-based screening
"""

from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from enum import Enum
from dataclasses import dataclass


class FilterOperator(str, Enum):
    """Filter comparison operators."""
    GREATER_THAN = "gte"
    LESS_THAN = "lte"
    EQUALS = "eq"
    BETWEEN = "between"
    IN_LIST = "in"


class ScreeningCategory(str, Enum):
    """Screening filter categories."""
    UNIVERSE = "UNIVERSE"
    LIQUIDITY = "LIQUIDITY"
    FUNDAMENTAL = "FUNDAMENTAL"
    VALUATION = "VALUATION"
    TECHNICAL = "TECHNICAL"
    RELATIVE_STRENGTH = "RELATIVE_STRENGTH"
    EVENT = "EVENT"


@dataclass
class ScreeningSnapshot:
    """
    S1: Daily screening snapshot for a security.

    Pre-calculated metrics for fast querying.
    One record per security per day.
    """
    security_id: str
    date: str

    # Market data
    price: float
    market_cap: float
    volume_today: float
    avg_volume_20d: float
    avg_value_20d: float
    free_float_pct: float

    # Fundamentals (Module 1)
    revenue_growth_1y: Optional[float] = None
    revenue_cagr_3y: Optional[float] = None
    eps_growth_1y: Optional[float] = None
    eps_cagr_3y: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None
    net_margin: Optional[float] = None
    debt_equity: Optional[float] = None
    interest_coverage: Optional[float] = None
    fcf: Optional[float] = None
    fcf_margin: Optional[float] = None

    # Valuation (Module 2)
    pe: Optional[float] = None
    pb: Optional[float] = None
    ev_ebitda: Optional[float] = None
    dividend_yield: Optional[float] = None
    fcf_yield: Optional[float] = None

    # Technicals (Module 4)
    price_vs_sma20: Optional[float] = None
    price_vs_sma50: Optional[float] = None
    price_vs_sma200: Optional[float] = None
    rsi14: Optional[float] = None
    macd_state: Optional[str] = None
    volume_ratio: Optional[float] = None
    atr_pct: Optional[float] = None
    return_1m: Optional[float] = None
    return_3m: Optional[float] = None
    return_6m: Optional[float] = None

    # Market Context (Module 3)
    relative_strength_sector: Optional[float] = None
    relative_strength_market: Optional[float] = None

    # Metadata
    sector_id: str = ""
    market_regime: Optional[str] = None
    latest_event_type: Optional[str] = None
    data_quality_status: str = "VERIFIED"


class ScreeningMetricRegistry:
    """Registry of all available screening metrics."""

    METRICS = {
        # Universe metrics
        "market_cap": {"category": ScreeningCategory.UNIVERSE, "label": "Market Cap", "type": "float", "unit": "PKR", "operators": ["gte", "lte", "between"]},
        "price": {"category": ScreeningCategory.UNIVERSE, "label": "Price", "type": "float", "unit": "PKR", "operators": ["gte", "lte", "between"]},
        "sector": {"category": ScreeningCategory.UNIVERSE, "label": "Sector", "type": "string", "operators": ["in"]},

        # Liquidity metrics
        "avg_volume_20d": {"category": ScreeningCategory.LIQUIDITY, "label": "Avg Volume 20D", "type": "float", "unit": "shares", "operators": ["gte", "lte"]},
        "avg_value_20d": {"category": ScreeningCategory.LIQUIDITY, "label": "Avg Value Traded 20D", "type": "float", "unit": "PKR", "operators": ["gte", "lte"]},
        "volume_ratio": {"category": ScreeningCategory.LIQUIDITY, "label": "Volume Ratio", "type": "float", "operators": ["gte", "lte"]},

        # Fundamental metrics
        "revenue_growth_1y": {"category": ScreeningCategory.FUNDAMENTAL, "label": "Revenue Growth 1Y", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "revenue_cagr_3y": {"category": ScreeningCategory.FUNDAMENTAL, "label": "Revenue CAGR 3Y", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "eps_growth_1y": {"category": ScreeningCategory.FUNDAMENTAL, "label": "EPS Growth 1Y", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "eps_cagr_3y": {"category": ScreeningCategory.FUNDAMENTAL, "label": "EPS CAGR 3Y", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "roe": {"category": ScreeningCategory.FUNDAMENTAL, "label": "ROE", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "roa": {"category": ScreeningCategory.FUNDAMENTAL, "label": "ROA", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "roic": {"category": ScreeningCategory.FUNDAMENTAL, "label": "ROIC", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "net_margin": {"category": ScreeningCategory.FUNDAMENTAL, "label": "Net Margin", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "debt_equity": {"category": ScreeningCategory.FUNDAMENTAL, "label": "Debt/Equity", "type": "float", "operators": ["gte", "lte"]},
        "interest_coverage": {"category": ScreeningCategory.FUNDAMENTAL, "label": "Interest Coverage", "type": "float", "operators": ["gte", "lte"]},
        "fcf": {"category": ScreeningCategory.FUNDAMENTAL, "label": "Free Cash Flow", "type": "float", "unit": "PKR", "operators": ["gte"]},
        "fcf_margin": {"category": ScreeningCategory.FUNDAMENTAL, "label": "FCF Margin", "type": "float", "unit": "%", "operators": ["gte", "lte"]},

        # Valuation metrics
        "pe": {"category": ScreeningCategory.VALUATION, "label": "P/E", "type": "float", "operators": ["gte", "lte"]},
        "pb": {"category": ScreeningCategory.VALUATION, "label": "P/B", "type": "float", "operators": ["gte", "lte"]},
        "ev_ebitda": {"category": ScreeningCategory.VALUATION, "label": "EV/EBITDA", "type": "float", "operators": ["gte", "lte"]},
        "dividend_yield": {"category": ScreeningCategory.VALUATION, "label": "Dividend Yield", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "fcf_yield": {"category": ScreeningCategory.VALUATION, "label": "FCF Yield", "type": "float", "unit": "%", "operators": ["gte", "lte"]},

        # Technical metrics
        "price_vs_sma20": {"category": ScreeningCategory.TECHNICAL, "label": "Price vs SMA20", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "price_vs_sma50": {"category": ScreeningCategory.TECHNICAL, "label": "Price vs SMA50", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "price_vs_sma200": {"category": ScreeningCategory.TECHNICAL, "label": "Price vs SMA200", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "rsi14": {"category": ScreeningCategory.TECHNICAL, "label": "RSI (14)", "type": "float", "operators": ["gte", "lte", "between"]},
        "volume_ratio": {"category": ScreeningCategory.TECHNICAL, "label": "Volume Ratio", "type": "float", "operators": ["gte", "lte"]},
        "atr_pct": {"category": ScreeningCategory.TECHNICAL, "label": "ATR %", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "return_1m": {"category": ScreeningCategory.TECHNICAL, "label": "1M Return", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "return_3m": {"category": ScreeningCategory.TECHNICAL, "label": "3M Return", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "return_6m": {"category": ScreeningCategory.TECHNICAL, "label": "6M Return", "type": "float", "unit": "%", "operators": ["gte", "lte"]},

        # Relative strength metrics
        "relative_strength_sector": {"category": ScreeningCategory.RELATIVE_STRENGTH, "label": "RS vs Sector", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
        "relative_strength_market": {"category": ScreeningCategory.RELATIVE_STRENGTH, "label": "RS vs Market", "type": "float", "unit": "%", "operators": ["gte", "lte"]},
    }

    @classmethod
    def get_metric_info(cls, metric_code: str) -> Optional[Dict]:
        """Get metric definition."""
        return cls.METRICS.get(metric_code)

    @classmethod
    def get_metrics_by_category(cls, category: ScreeningCategory) -> Dict:
        """Get all metrics in a category."""
        return {
            k: v for k, v in cls.METRICS.items()
            if v.get("category") == category
        }


class ScreenerEngine:
    """Main screening and discovery engine."""

    # ════════════════════════════════════════════════════════════════════════════
    # FILTER BUILDING
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def apply_filter(
        snapshot: ScreeningSnapshot,
        metric_code: str,
        operator: str,
        value: any,
        comparison_value: any = None,
    ) -> bool:
        """
        Apply single filter condition to snapshot.

        Args:
            snapshot: Screening snapshot
            metric_code: Metric to filter on
            operator: Filter operator (gte, lte, eq, between, in)
            value: Filter value
            comparison_value: For comparisons (e.g., sector median)

        Returns:
            True if snapshot matches filter
        """
        # Get metric value from snapshot
        metric_value = getattr(snapshot, metric_code, None)

        # Handle NULL/missing data
        if metric_value is None:
            return False

        # Apply operator
        if operator == "gte":
            return metric_value >= value
        elif operator == "lte":
            return metric_value <= value
        elif operator == "eq":
            return metric_value == value
        elif operator == "between":
            return value <= metric_value <= comparison_value
        elif operator == "in":
            return metric_value in value

        return False

    @staticmethod
    def apply_filter_set(
        snapshot: ScreeningSnapshot,
        filters: List[Dict],
        logic: str = "AND",
    ) -> Tuple[bool, List[str]]:
        """
        Apply multiple filters with Boolean logic.

        Args:
            snapshot: Screening snapshot
            filters: List of filter dicts
            logic: "AND" or "OR"

        Returns:
            (matched, matching_conditions)
        """
        matching_conditions = []
        results = []

        for f in filters:
            matched = ScreenerEngine.apply_filter(
                snapshot,
                f.get("metric"),
                f.get("operator"),
                f.get("value"),
                f.get("comparison_value"),
            )
            results.append(matched)

            if matched:
                matching_conditions.append(
                    f"{f.get('metric')} {f.get('operator')} {f.get('value')}"
                )

        if logic == "AND":
            final_result = all(results)
        elif logic == "OR":
            final_result = any(results)
        else:
            final_result = False

        return final_result, matching_conditions

    # ════════════════════════════════════════════════════════════════════════════
    # SCREENING EXECUTION
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def screen_universe(
        snapshots: List[ScreeningSnapshot],
        filters: List[Dict],
        logic: str = "AND",
        sort_by: Optional[str] = None,
        sort_direction: str = "desc",
        limit: Optional[int] = None,
    ) -> Dict:
        """
        Execute screening across universe.

        Args:
            snapshots: List of screening snapshots
            filters: Filter conditions
            logic: "AND" or "OR"
            sort_by: Metric to sort results by
            sort_direction: "asc" or "desc"
            limit: Maximum results to return

        Returns:
            Screening results with matched securities
        """
        matched_securities = []
        universe_size = len(snapshots)

        for snapshot in snapshots:
            matched, conditions = ScreenerEngine.apply_filter_set(
                snapshot, filters, logic
            )

            if matched:
                matched_securities.append({
                    "security_id": snapshot.security_id,
                    "price": snapshot.price,
                    "market_cap": snapshot.market_cap,
                    "sector": snapshot.sector_id,
                    "matching_conditions": conditions,
                    "data_quality": snapshot.data_quality_status,
                    "snapshot": snapshot,
                })

        # Sort results
        if sort_by:
            reverse = sort_direction == "desc"
            matched_securities.sort(
                key=lambda x: getattr(x["snapshot"], sort_by, 0),
                reverse=reverse,
            )

        # Apply limit
        if limit:
            matched_securities = matched_securities[:limit]

        return {
            "status": "success",
            "filter_logic": logic,
            "universe_size": universe_size,
            "matched_count": len(matched_securities),
            "results": matched_securities,
            "filter_summary": f"Found {len(matched_securities)} matches",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # SECTOR-RELATIVE SCREENING
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def calculate_sector_percentiles(
        snapshots: List[ScreeningSnapshot],
        metric_code: str,
        sector_id: str,
    ) -> Dict[int, float]:
        """
        Calculate metric percentiles for a sector.

        Args:
            snapshots: All screening snapshots
            metric_code: Metric to analyze
            sector_id: Sector to filter

        Returns:
            Dict of {percentile: value}
        """
        sector_values = [
            getattr(s, metric_code)
            for s in snapshots
            if s.sector_id == sector_id and getattr(s, metric_code) is not None
        ]

        if not sector_values:
            return {}

        sector_values.sort()

        return {
            p: sector_values[int(len(sector_values) * p / 100)]
            for p in [10, 25, 50, 75, 90]
        }

    @staticmethod
    def filter_relative_to_sector(
        snapshots: List[ScreeningSnapshot],
        metric_code: str,
        operator: str,
        percentile: int = 50,
    ) -> List[ScreeningSnapshot]:
        """
        Filter snapshots where metric is better than sector percentile.

        Args:
            snapshots: All screening snapshots
            metric_code: Metric to analyze
            operator: "above" or "below" sector level
            percentile: Sector percentile (50 = median)

        Returns:
            Filtered snapshots
        """
        results = []

        for snapshot in snapshots:
            metric_value = getattr(snapshot, metric_code)
            if metric_value is None:
                continue

            # Calculate sector percentiles
            percentiles = ScreenerEngine.calculate_sector_percentiles(
                snapshots, metric_code, snapshot.sector_id
            )

            percentile_value = percentiles.get(percentile)
            if percentile_value is None:
                continue

            if operator == "above" and metric_value > percentile_value:
                results.append(snapshot)
            elif operator == "below" and metric_value < percentile_value:
                results.append(snapshot)

        return results

    # ════════════════════════════════════════════════════════════════════════════
    # CHANGE-BASED SCREENING
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def detect_metric_change(
        current_value: float,
        previous_value: float,
        change_threshold_pct: float = 5.0,
    ) -> Dict:
        """
        Detect if metric changed significantly.

        Args:
            current_value: Current metric value
            previous_value: Previous metric value
            change_threshold_pct: Threshold for significance

        Returns:
            Change detection result
        """
        if previous_value == 0:
            return {"changed": False, "reason": "No previous value"}

        pct_change = ((current_value - previous_value) / abs(previous_value)) * 100

        return {
            "changed": abs(pct_change) > change_threshold_pct,
            "pct_change": round(pct_change, 2),
            "direction": "UP" if pct_change > 0 else "DOWN",
            "magnitude": "HIGH" if abs(pct_change) > 20 else "MODERATE" if abs(pct_change) > change_threshold_pct else "LOW",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # SCREENING PRESETS (S9)
    # ════════════════════════════════════════════════════════════════════════════

    PRESET_SCREENS = {
        "PROFITABLE_GROWTH": {
            "name": "Profitable Growth",
            "description": "Companies with strong revenue and EPS growth, high profitability",
            "filters": [
                {"metric": "revenue_growth_1y", "operator": "gte", "value": 10},
                {"metric": "eps_growth_1y", "operator": "gte", "value": 10},
                {"metric": "roe", "operator": "gte", "value": 15},
                {"metric": "net_margin", "operator": "gte", "value": 0},
            ],
            "logic": "AND",
        },
        "LOW_LEVERAGE": {
            "name": "Low Leverage",
            "description": "Conservative balance sheet with manageable debt",
            "filters": [
                {"metric": "debt_equity", "operator": "lte", "value": 0.5},
                {"metric": "interest_coverage", "operator": "gte", "value": 5},
                {"metric": "fcf", "operator": "gte", "value": 0},
            ],
            "logic": "AND",
        },
        "DIVIDEND_INCOME": {
            "name": "Dividend Income",
            "description": "Stable dividend payers with solid fundamentals",
            "filters": [
                {"metric": "dividend_yield", "operator": "gte", "value": 3},
                {"metric": "fcf", "operator": "gte", "value": 0},
            ],
            "logic": "AND",
        },
        "MOMENTUM": {
            "name": "Momentum",
            "description": "Technical strength with uptrend and positive momentum",
            "filters": [
                {"metric": "price_vs_sma50", "operator": "gte", "value": 0},
                {"metric": "price_vs_sma200", "operator": "gte", "value": 0},
                {"metric": "rsi14", "operator": "gte", "value": 50},
                {"metric": "volume_ratio", "operator": "gte", "value": 1.2},
            ],
            "logic": "AND",
        },
        "BREAKOUT_WATCH": {
            "name": "Breakout Watch",
            "description": "Potential breakout setups with volume confirmation",
            "filters": [
                {"metric": "price_vs_sma200", "operator": "gte", "value": 0},
                {"metric": "volume_ratio", "operator": "gte", "value": 1.5},
            ],
            "logic": "AND",
        },
    }

    @classmethod
    def get_preset_screen(cls, preset_code: str) -> Optional[Dict]:
        """Get preset screen definition."""
        return cls.PRESET_SCREENS.get(preset_code)

    @classmethod
    def list_preset_screens(cls) -> List[Dict]:
        """List all available preset screens."""
        return [
            {
                "code": code,
                "name": screen.get("name"),
                "description": screen.get("description"),
            }
            for code, screen in cls.PRESET_SCREENS.items()
        ]

    # ════════════════════════════════════════════════════════════════════════════
    # SAVED SCREENS (S10)
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_saved_screen(
        user_id: str,
        screen_name: str,
        filters: List[Dict],
        logic: str = "AND",
    ) -> Dict:
        """
        Create user-defined saved screen.

        Args:
            user_id: User identifier
            screen_name: Screen name
            filters: Filter configuration
            logic: Filter logic ("AND" or "OR")

        Returns:
            Saved screen record
        """
        return {
            "screen_id": f"{user_id}_{screen_name.replace(' ', '_')}_{date.today().isoformat()}",
            "user_id": user_id,
            "name": screen_name,
            "filters": filters,
            "logic": logic,
            "created_at": date.today().isoformat(),
            "updated_at": date.today().isoformat(),
            "run_count": 0,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # RESULT FORMATTING (S8)
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def format_results_table(
        results: List[Dict],
        columns: Optional[List[str]] = None,
    ) -> Dict:
        """
        Format screening results as table.

        Args:
            results: Screening results
            columns: Column selection (e.g., ["ticker", "price", "roe", "pe"])

        Returns:
            Formatted table data
        """
        if columns is None:
            columns = ["security_id", "price", "market_cap", "sector"]

        table_data = []

        for result in results:
            snapshot = result.get("snapshot")
            row = {}

            for col in columns:
                value = getattr(snapshot, col, None)
                row[col] = round(value, 2) if isinstance(value, float) else value

            table_data.append(row)

        return {
            "columns": columns,
            "rows": table_data,
            "row_count": len(table_data),
        }

    @staticmethod
    def get_column_sets() -> Dict:
        """Get predefined column sets for results display."""
        return {
            "fundamentals": {
                "name": "Fundamentals",
                "columns": ["security_id", "revenue_growth_1y", "eps_growth_1y", "roe", "roic", "net_margin", "debt_equity"],
            },
            "valuation": {
                "name": "Valuation",
                "columns": ["security_id", "price", "pe", "pb", "ev_ebitda", "dividend_yield", "fcf_yield"],
            },
            "technicals": {
                "name": "Technicals",
                "columns": ["security_id", "price", "rsi14", "price_vs_sma50", "price_vs_sma200", "volume_ratio", "return_1m"],
            },
            "market": {
                "name": "Market",
                "columns": ["security_id", "sector_id", "market_cap", "avg_volume_20d", "relative_strength_sector", "relative_strength_market"],
            },
        }
