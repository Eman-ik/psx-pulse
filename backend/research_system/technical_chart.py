"""
Technical Chart UI - Sprint T8

Interactive chart component for technical analysis visualization.
Displays candlestick + volume + overlays.

Features:
- Candlestick rendering
- Volume bars
- Optional overlays: SMA, RSI, MACD, ATR, Bollinger Bands
- Multiple timeframes (1M, 3M, 6M, 1Y, 3Y, 5Y)
- Interactive controls
- Chart data export
"""

from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from enum import Enum


class Timeframe(str, Enum):
    """Available chart timeframes."""
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    THREE_YEARS = "3Y"
    FIVE_YEARS = "5Y"


class IndicatorOverlay(str, Enum):
    """Available indicator overlays."""
    SMA_20 = "SMA_20"
    SMA_50 = "SMA_50"
    SMA_200 = "SMA_200"
    EMA_20 = "EMA_20"
    RSI = "RSI"
    MACD = "MACD"
    ATR = "ATR"
    BOLLINGER_BANDS = "BBANDS"


class TechnicalChartUI:
    """Technical chart rendering engine."""

    # ════════════════════════════════════════════════════════════════════════════
    # CANDLESTICK RENDERING
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_candlestick(
        date_str: str,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
    ) -> Dict:
        """
        Create candlestick OHLCV data point.

        Args:
            date_str: ISO format date
            open/high/low/close: Price data
            volume: Trading volume

        Returns:
            Candlestick data point
        """
        color = "GREEN" if close_price >= open_price else "RED"
        body_top = max(open_price, close_price)
        body_bottom = min(open_price, close_price)
        wick_high = high_price
        wick_low = low_price

        return {
            "date": date_str,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume,
            "color": color,
            "body_top": round(body_top, 2),
            "body_bottom": round(body_bottom, 2),
            "wick_high": round(wick_high, 2),
            "wick_low": round(wick_low, 2),
            "body_height": round(abs(close_price - open_price), 2),
            "range": round(high_price - low_price, 2),
        }

    @staticmethod
    def create_candlestick_series(
        dates: List[str],
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
    ) -> List[Dict]:
        """
        Create series of candlesticks.

        Args:
            dates/opens/highs/lows/closes/volumes: OHLCV arrays

        Returns:
            List of candlestick data points
        """
        candlesticks = []

        for i in range(len(dates)):
            stick = TechnicalChartUI.create_candlestick(
                dates[i],
                opens[i],
                highs[i],
                lows[i],
                closes[i],
                volumes[i],
            )
            candlesticks.append(stick)

        return candlesticks

    # ════════════════════════════════════════════════════════════════════════════
    # VOLUME VISUALIZATION
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_volume_bars(
        dates: List[str],
        closes: List[float],
        volumes: List[float],
    ) -> List[Dict]:
        """
        Create volume bars with color coding.

        Volume bar color based on price movement:
        - Green if close > previous close
        - Red if close < previous close

        Args:
            dates: Date array
            closes: Close prices
            volumes: Volume array

        Returns:
            List of volume bar data points
        """
        volume_bars = []

        for i in range(len(dates)):
            prev_close = closes[i - 1] if i > 0 else closes[i]
            color = "GREEN" if closes[i] >= prev_close else "RED"

            volume_bars.append({
                "date": dates[i],
                "volume": volumes[i],
                "color": color,
                "height_pct": (volumes[i] / max(volumes)) * 100 if volumes else 0,
            })

        return volume_bars

    # ════════════════════════════════════════════════════════════════════════════
    # INDICATOR OVERLAY RENDERING
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_moving_average_overlay(
        dates: List[str],
        ma_values: List[Optional[float]],
        ma_type: str = "SMA",
        period: int = 20,
    ) -> Dict:
        """
        Create moving average overlay for chart.

        Args:
            dates: Date array
            ma_values: Moving average values
            ma_type: "SMA" or "EMA"
            period: MA period

        Returns:
            MA overlay data
        """
        return {
            "type": "MOVING_AVERAGE",
            "ma_type": ma_type,
            "period": period,
            "name": f"{ma_type}{period}",
            "color": {
                20: "#0066CC",
                50: "#FF9900",
                200: "#CC0000",
            }.get(period, "#333333"),
            "data_points": [
                {
                    "date": dates[i],
                    "value": round(ma_values[i], 2) if ma_values[i] is not None else None,
                }
                for i in range(len(dates))
            ],
            "visible_from_start": period in [20, 50, 200],
        }

    @staticmethod
    def create_bollinger_bands_overlay(
        dates: List[str],
        closes: List[float],
        sma_20: List[Optional[float]],
        period: int = 20,
        std_dev: float = 2.0,
    ) -> Dict:
        """
        Create Bollinger Bands overlay.

        Args:
            dates: Date array
            closes: Close prices
            sma_20: 20-day SMA values
            period: BB period
            std_dev: Standard deviation multiplier

        Returns:
            Bollinger Bands overlay data
        """
        # Simplified Bollinger Bands
        bands = []

        for i in range(len(closes)):
            if sma_20[i] is None:
                bands.append(None)
            else:
                # Simplified: use ATR-based bands
                mid = sma_20[i]
                width = mid * 0.02  # 2% band width
                bands.append({
                    "date": dates[i],
                    "middle": round(mid, 2),
                    "upper": round(mid + width, 2),
                    "lower": round(mid - width, 2),
                })

        return {
            "type": "BOLLINGER_BANDS",
            "period": period,
            "std_dev": std_dev,
            "name": f"BBANDS({period}, {std_dev})",
            "colors": {
                "middle": "#0066CC",
                "upper": "#FF9900",
                "lower": "#FF9900",
            },
            "data_points": bands,
        }

    @staticmethod
    def create_rsi_overlay(
        dates: List[str],
        rsi_values: List[Optional[float]],
    ) -> Dict:
        """
        Create RSI indicator panel.

        Args:
            dates: Date array
            rsi_values: RSI values

        Returns:
            RSI overlay data for separate panel
        """
        return {
            "type": "RSI",
            "name": "RSI (14)",
            "panel": "SEPARATE",
            "height": "25%",
            "scale": [0, 100],
            "zones": {
                "overbought": {"min": 70, "max": 100, "color": "#FFE6E6"},
                "oversold": {"min": 0, "max": 30, "color": "#E6F2FF"},
                "neutral": {"min": 30, "max": 70, "color": "#F0F0F0"},
            },
            "data_points": [
                {
                    "date": dates[i],
                    "value": round(rsi_values[i], 2) if rsi_values[i] is not None else None,
                }
                for i in range(len(dates))
            ],
        }

    @staticmethod
    def create_macd_overlay(
        dates: List[str],
        macd_lines: List[Tuple[Optional[float], Optional[float], Optional[float]]],
    ) -> Dict:
        """
        Create MACD indicator panel.

        Args:
            dates: Date array
            macd_lines: List of (macd, signal, histogram) tuples

        Returns:
            MACD overlay data for separate panel
        """
        return {
            "type": "MACD",
            "name": "MACD",
            "panel": "SEPARATE",
            "height": "25%",
            "components": {
                "macd_line": {"color": "#0066CC", "type": "line"},
                "signal_line": {"color": "#FF9900", "type": "line"},
                "histogram": {"color": "#333333", "type": "bar"},
            },
            "data_points": [
                {
                    "date": dates[i],
                    "macd": round(macd_lines[i][0], 4) if macd_lines[i][0] is not None else None,
                    "signal": round(macd_lines[i][1], 4) if macd_lines[i][1] is not None else None,
                    "histogram": round(macd_lines[i][2], 4) if macd_lines[i][2] is not None else None,
                }
                for i in range(len(dates))
            ],
        }

    # ════════════════════════════════════════════════════════════════════════════
    # CHART BUILDING
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def build_chart(
        security_id: str,
        timeframe: Timeframe,
        candlesticks: List[Dict],
        volume_bars: List[Dict],
        overlays: Optional[List[Dict]] = None,
        price_range: Optional[Tuple[float, float]] = None,
        volume_range: Optional[Tuple[float, float]] = None,
    ) -> Dict:
        """
        Build complete chart with all components.

        Args:
            security_id: Security identifier
            timeframe: Chart timeframe (1M, 3M, 6M, 1Y, etc.)
            candlesticks: Candlestick data
            volume_bars: Volume bar data
            overlays: Optional indicator overlays
            price_range: Optional price axis range
            volume_range: Optional volume axis range

        Returns:
            Complete chart specification
        """
        if not candlesticks:
            return {
                "status": "error",
                "message": "No chart data available",
            }

        # Auto-calculate ranges if not provided
        if price_range is None:
            prices = [c.get("high") for c in candlesticks if c.get("high")]
            if prices:
                min_price = min(prices) * 0.98
                max_price = max(prices) * 1.02
                price_range = (min_price, max_price)

        if volume_range is None and volume_bars:
            volumes = [v.get("volume") for v in volume_bars if v.get("volume")]
            if volumes:
                max_volume = max(volumes)
                volume_range = (0, max_volume)

        chart_spec = {
            "chart_id": f"{security_id}_{timeframe}_{date.today().isoformat()}",
            "security_id": security_id,
            "timeframe": timeframe,
            "type": "CANDLESTICK_CHART",
            "data_count": len(candlesticks),
            "date_range": {
                "start": candlesticks[0].get("date") if candlesticks else None,
                "end": candlesticks[-1].get("date") if candlesticks else None,
            },
            "price_axis": {
                "label": "Price",
                "min": price_range[0] if price_range else None,
                "max": price_range[1] if price_range else None,
                "auto_scale": price_range is None,
            },
            "volume_axis": {
                "label": "Volume",
                "min": volume_range[0] if volume_range else None,
                "max": volume_range[1] if volume_range else None,
            },
            "candles": candlesticks,
            "volume": volume_bars,
            "overlays": overlays or [],
        }

        return {
            "status": "success",
            "data": chart_spec,
        }

    # ════════════════════════════════════════════════════════════════════════════
    # CHART CONTROLS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_chart_controls() -> Dict:
        """
        Create chart control panel specification.

        Returns:
            Control panel with available options
        """
        return {
            "timeframe_selector": {
                "label": "Timeframe",
                "options": [tf.value for tf in Timeframe],
                "default": "1Y",
            },
            "indicator_toggles": {
                "label": "Indicators",
                "options": [
                    {"name": "SMA 20", "indicator": "SMA_20", "enabled": True},
                    {"name": "SMA 50", "indicator": "SMA_50", "enabled": True},
                    {"name": "SMA 200", "indicator": "SMA_200", "enabled": False},
                    {"name": "EMA 20", "indicator": "EMA_20", "enabled": False},
                    {"name": "RSI", "indicator": "RSI", "enabled": False},
                    {"name": "MACD", "indicator": "MACD", "enabled": False},
                    {"name": "ATR", "indicator": "ATR", "enabled": False},
                    {"name": "Bollinger Bands", "indicator": "BBANDS", "enabled": False},
                ],
            },
            "tools": {
                "labels": ["Zoom", "Pan", "Crosshair", "Measure"],
                "default_active": ["Zoom"],
            },
            "export_options": {
                "formats": ["PNG", "SVG", "PDF"],
                "include_data": True,
            },
        }

    # ════════════════════════════════════════════════════════════════════════════
    # TECHNICAL ANNOTATIONS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def add_support_resistance_lines(
        chart: Dict,
        support_levels: List[Dict],
        resistance_levels: List[Dict],
    ) -> Dict:
        """
        Add support/resistance level lines to chart.

        Args:
            chart: Chart specification
            support_levels: Support zone data
            resistance_levels: Resistance zone data

        Returns:
            Chart with added level lines
        """
        chart["annotations"] = chart.get("annotations", [])

        for support in support_levels:
            chart["annotations"].append({
                "type": "HORIZONTAL_LINE",
                "level": support.get("level"),
                "color": "#00AA00",
                "style": "DASHED",
                "label": f"Support ({support.get('strength')} touches)",
                "thickness": 1,
            })

        for resistance in resistance_levels:
            chart["annotations"].append({
                "type": "HORIZONTAL_LINE",
                "level": resistance.get("level"),
                "color": "#AA0000",
                "style": "DASHED",
                "label": f"Resistance ({resistance.get('strength')} touches)",
                "thickness": 1,
            })

        return chart

    @staticmethod
    def add_technical_events(
        chart: Dict,
        events: List[Dict],
    ) -> Dict:
        """
        Add technical event markers to chart.

        Args:
            chart: Chart specification
            events: Technical events (breakouts, crossovers, etc.)

        Returns:
            Chart with event markers
        """
        chart["events"] = chart.get("events", [])

        for event in events:
            marker_config = {
                "GOLDEN_CROSS": {"symbol": "▲", "color": "#00AA00", "size": 10},
                "DEATH_CROSS": {"symbol": "▼", "color": "#AA0000", "size": 10},
                "BREAKOUT_20D": {"symbol": "→", "color": "#0066CC", "size": 12},
                "BREAKDOWN_20D": {"symbol": "←", "color": "#FF6600", "size": 12},
            }

            config = marker_config.get(event.get("type"), {})

            chart["events"].append({
                "type": event.get("type"),
                "date": event.get("date"),
                "symbol": config.get("symbol", "•"),
                "color": config.get("color", "#333333"),
                "size": config.get("size", 8),
                "tooltip": f"{event.get('type')} on {event.get('date')}",
            })

        return chart

    # ════════════════════════════════════════════════════════════════════════════
    # CHART EXPORT
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def export_chart_data(
        chart: Dict,
        format: str = "JSON",
    ) -> Dict:
        """
        Export chart data in specified format.

        Args:
            chart: Chart specification
            format: Export format (JSON, CSV, etc.)

        Returns:
            Exportable chart data
        """
        if format == "JSON":
            return {
                "format": "JSON",
                "data": chart,
                "size_bytes": len(str(chart).encode()),
            }

        elif format == "CSV":
            # Convert to CSV-friendly format
            csv_data = "Date,Open,High,Low,Close,Volume\n"
            for candle in chart.get("candles", []):
                csv_data += f"{candle.get('date')},{candle.get('open')},{candle.get('high')},{candle.get('low')},{candle.get('close')},{candle.get('volume')}\n"

            return {
                "format": "CSV",
                "data": csv_data,
                "rows": len(chart.get("candles", [])),
            }

        return {
            "error": f"Format {format} not supported",
        }
