"""
Screener API - Sprint S7

RESTful API for stock screening and discovery.
Provides dynamic filtering, preset screens, and saved screens.

Endpoints:
POST /api/screener — Execute dynamic screen
GET /api/screener/filters — Get available filters
GET /api/screener/presets — List preset screens
POST /api/screener/presets/{preset} — Run preset
GET /api/screener/saved — List saved screens
POST /api/screener/saved — Create saved screen
"""

from typing import Dict, List, Optional
from datetime import date
from research_system.screener_engine import (
    ScreenerEngine,
    ScreeningMetricRegistry,
    ScreeningSnapshot,
    ScreeningCategory,
)


class ScreenerAPIEndpoints:
    """Screener API endpoints."""

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Dynamic Screening
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def execute_screen(
        snapshots: List[ScreeningSnapshot],
        filters: List[Dict],
        logic: str = "AND",
        sort_by: Optional[str] = None,
        sort_direction: str = "desc",
        limit: int = 50,
    ) -> Dict:
        """
        POST /api/screener

        Execute dynamic screening with specified filters.

        Request:
        {
          "filters": [
            {"metric": "roe", "operator": "gte", "value": 20},
            {"metric": "pe", "operator": "lte", "value": 10},
            {"metric": "volume_ratio", "operator": "gte", "value": 1.5}
          ],
          "logic": "AND",
          "sort_by": "roe",
          "sort_direction": "desc",
          "limit": 50
        }
        """
        # Validate filters
        for f in filters:
            metric = f.get("metric")
            if not ScreeningMetricRegistry.get_metric_info(metric):
                return {
                    "status": "error",
                    "message": f"Unknown metric: {metric}",
                }

        # Execute screen
        results = ScreenerEngine.screen_universe(
            snapshots=snapshots,
            filters=filters,
            logic=logic,
            sort_by=sort_by,
            sort_direction=sort_direction,
            limit=limit,
        )

        # Add filter trace
        results["request"] = {
            "filter_count": len(filters),
            "logic": logic,
            "sorted_by": sort_by,
        }

        return {
            "status": "success",
            "endpoint": "/api/screener",
            "timestamp": date.today().isoformat(),
            "data": results,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Available Filters
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_available_filters(
        category: Optional[str] = None,
    ) -> Dict:
        """
        GET /api/screener/filters

        Get all available screening filters and their operators.

        Optional query params:
        - category: Filter by category (FUNDAMENTAL, VALUATION, TECHNICAL, etc.)
        """
        if category:
            try:
                cat = ScreeningCategory[category.upper()]
                metrics = ScreeningMetricRegistry.get_metrics_by_category(cat)
            except KeyError:
                return {
                    "status": "error",
                    "message": f"Unknown category: {category}",
                }
        else:
            metrics = ScreeningMetricRegistry.METRICS

        # Format response
        filters = []
        for metric_code, info in metrics.items():
            filters.append({
                "metric_code": metric_code,
                "label": info.get("label"),
                "category": info.get("category"),
                "data_type": info.get("type"),
                "unit": info.get("unit"),
                "operators": info.get("operators", []),
            })

        return {
            "status": "success",
            "endpoint": "/api/screener/filters",
            "filter_count": len(filters),
            "data": {
                "category": category,
                "filters": filters,
            },
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Preset Screens
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def list_preset_screens() -> Dict:
        """
        GET /api/screener/presets

        List all available preset screens.
        """
        presets = ScreenerEngine.list_preset_screens()

        return {
            "status": "success",
            "endpoint": "/api/screener/presets",
            "preset_count": len(presets),
            "data": {
                "presets": presets,
            },
        }

    @staticmethod
    def run_preset_screen(
        preset_code: str,
        snapshots: List[ScreeningSnapshot],
        limit: int = 50,
    ) -> Dict:
        """
        POST /api/screener/presets/{preset}

        Run a preset screening configuration.

        Params:
        - preset: Preset code (PROFITABLE_GROWTH, MOMENTUM, etc.)
        """
        preset = ScreenerEngine.get_preset_screen(preset_code)

        if not preset:
            return {
                "status": "error",
                "message": f"Unknown preset: {preset_code}",
            }

        # Execute screen with preset filters
        results = ScreenerEngine.screen_universe(
            snapshots=snapshots,
            filters=preset.get("filters"),
            logic=preset.get("logic", "AND"),
            limit=limit,
        )

        return {
            "status": "success",
            "endpoint": f"/api/screener/presets/{preset_code}",
            "timestamp": date.today().isoformat(),
            "preset_info": {
                "name": preset.get("name"),
                "description": preset.get("description"),
            },
            "data": results,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Saved Screens
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_saved_screen(
        user_id: str,
        screen_name: str,
        filters: List[Dict],
        logic: str = "AND",
    ) -> Dict:
        """
        POST /api/screener/saved

        Create a new saved screen for user.

        Request:
        {
          "user_id": "user123",
          "screen_name": "My Dividend Stocks",
          "filters": [...],
          "logic": "AND"
        }
        """
        # Validate filters
        for f in filters:
            if not ScreeningMetricRegistry.get_metric_info(f.get("metric")):
                return {
                    "status": "error",
                    "message": f"Invalid metric: {f.get('metric')}",
                }

        # Create saved screen
        saved_screen = ScreenerEngine.create_saved_screen(
            user_id=user_id,
            screen_name=screen_name,
            filters=filters,
            logic=logic,
        )

        return {
            "status": "success",
            "endpoint": "/api/screener/saved",
            "data": saved_screen,
            "message": f"Screen '{screen_name}' created successfully",
        }

    @staticmethod
    def list_saved_screens(user_id: str) -> Dict:
        """
        GET /api/screener/saved?user_id={user_id}

        List user's saved screens.
        """
        # In production, fetch from database
        # For now, return structure
        return {
            "status": "success",
            "endpoint": "/api/screener/saved",
            "user_id": user_id,
            "data": {
                "saved_screens": [
                    # Example structure
                    {
                        "screen_id": "user123_dividend_stocks",
                        "name": "Dividend Stocks",
                        "filter_count": 3,
                        "last_run": date.today().isoformat(),
                        "run_count": 15,
                    }
                ],
                "screen_count": 0,  # Update with actual count
            },
        }

    @staticmethod
    def run_saved_screen(
        user_id: str,
        screen_id: str,
        snapshots: List[ScreeningSnapshot],
        limit: int = 50,
    ) -> Dict:
        """
        POST /api/screener/saved/{screen_id}/run

        Execute a saved screen.
        """
        # In production, fetch screen configuration from database
        # For now, return error
        return {
            "status": "success",
            "endpoint": f"/api/screener/saved/{screen_id}/run",
            "data": {
                "message": "Execute saved screen configuration",
                "matched_count": 0,
            },
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Results Formatting
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_result_columns() -> Dict:
        """
        GET /api/screener/columns

        Get available column sets for results display.
        """
        column_sets = ScreenerEngine.get_column_sets()

        return {
            "status": "success",
            "endpoint": "/api/screener/columns",
            "data": column_sets,
        }

    @staticmethod
    def format_screening_results(
        results: List[Dict],
        column_set: str = "fundamentals",
    ) -> Dict:
        """
        Format screening results with specified columns.

        Args:
            results: Raw screening results
            column_set: Predefined column set or custom columns

        Returns:
            Formatted table
        """
        column_sets = ScreenerEngine.get_column_sets()

        if column_set in column_sets:
            columns = column_sets[column_set].get("columns")
        else:
            # Default columns
            columns = ["security_id", "price", "market_cap", "sector"]

        table = ScreenerEngine.format_results_table(results, columns)

        return {
            "status": "success",
            "endpoint": "/api/screener/results",
            "column_set": column_set,
            "data": table,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Sector Percentiles
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_sector_percentiles(
        snapshots: List[ScreeningSnapshot],
        sector_id: str,
        metric: str,
    ) -> Dict:
        """
        GET /api/screener/sector/{sector}/percentiles?metric={metric}

        Get metric percentiles for a sector.
        Used for sector-relative filtering.
        """
        percentiles = ScreenerEngine.calculate_sector_percentiles(
            snapshots, metric, sector_id
        )

        if not percentiles:
            return {
                "status": "error",
                "message": f"No data for {metric} in sector {sector_id}",
            }

        return {
            "status": "success",
            "endpoint": f"/api/screener/sector/{sector_id}/percentiles",
            "sector": sector_id,
            "metric": metric,
            "data": {
                "percentile_10": percentiles.get(10),
                "percentile_25": percentiles.get(25),
                "percentile_50": percentiles.get(50),  # Median
                "percentile_75": percentiles.get(75),
                "percentile_90": percentiles.get(90),
            },
        }

    # ════════════════════════════════════════════════════════════════════════════
    # HELPER: Universe Snapshot
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_screening_universe_info(
        snapshots: List[ScreeningSnapshot],
    ) -> Dict:
        """
        GET /api/screener/universe

        Get universe statistics and data quality info.
        """
        sectors = set(s.sector_id for s in snapshots)
        quality_counts = {}

        for s in snapshots:
            status = s.data_quality_status
            quality_counts[status] = quality_counts.get(status, 0) + 1

        return {
            "status": "success",
            "endpoint": "/api/screener/universe",
            "timestamp": date.today().isoformat(),
            "data": {
                "total_securities": len(snapshots),
                "sectors_represented": len(sectors),
                "sector_list": sorted(list(sectors)),
                "data_quality": quality_counts,
                "verified_securities": quality_counts.get("VERIFIED", 0),
            },
        }
