"""
Technical Analysis API - Sprint T7

API endpoints for technical analysis data.
Serves technical snapshots, components, and chart data.

Endpoints:
GET /api/securities/{ticker}/technicals — Complete snapshot
GET /api/securities/{ticker}/technicals/trend — Trend analysis
GET /api/securities/{ticker}/technicals/momentum — Momentum metrics
GET /api/securities/{ticker}/technicals/volatility — Volatility analysis
GET /api/securities/{ticker}/technicals/levels — Support/Resistance
GET /api/securities/{ticker}/technicals/events — Technical events
GET /api/securities/{ticker}/chart — Chart data with OHLCV
"""

from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from research_system.technical_analysis import TechnicalAnalysisEngine


class TechnicalAPIEndpoints:
    """Technical Analysis API endpoints."""

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Complete Technical Snapshot
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_technical_snapshot(
        security_id: str,
        current_price: float,
        prices: List[float],
        highs: List[float],
        lows: List[float],
        volumes: List[float],
        rs_vs_sector: float,
        rs_vs_market: float,
    ) -> Dict:
        """
        GET /api/securities/{ticker}/technicals

        Complete technical analysis snapshot.
        """
        snapshot = TechnicalAnalysisEngine.create_technical_snapshot(
            security_id=security_id,
            current_price=current_price,
            prices=prices,
            highs=highs,
            lows=lows,
            volumes=volumes,
            rs_vs_sector=rs_vs_sector,
            rs_vs_market=rs_vs_market,
        )

        return {
            "status": "success",
            "data": snapshot,
            "endpoint": "/technicals",
            "timestamp": date.today().isoformat(),
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Trend Analysis
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_trend_analysis(
        current_price: float,
        prices: List[float],
    ) -> Dict:
        """
        GET /api/securities/{ticker}/technicals/trend

        Detailed trend analysis across timeframes.
        """
        mas = TechnicalAnalysisEngine.calculate_moving_averages(prices)
        sma_20 = mas.get(20)
        sma_50 = mas.get(50)
        sma_100 = mas.get(100)
        sma_200 = mas.get(200)

        # Calculate slopes
        sma_20_slope = TechnicalAnalysisEngine.calculate_ma_slope(
            [TechnicalAnalysisEngine.calculate_sma(prices[:i+1], 20) for i in range(len(prices))]
        )
        sma_50_slope = TechnicalAnalysisEngine.calculate_ma_slope(
            [TechnicalAnalysisEngine.calculate_sma(prices[:i+1], 50) for i in range(len(prices))]
        )
        sma_200_slope = TechnicalAnalysisEngine.calculate_ma_slope(
            [TechnicalAnalysisEngine.calculate_sma(prices[:i+1], 200) for i in range(len(prices))]
        )

        # Classify trends
        trend_short = TechnicalAnalysisEngine.classify_trend_short_term(
            current_price, sma_20, sma_20_slope
        )
        trend_medium = TechnicalAnalysisEngine.classify_trend_medium_term(
            current_price, sma_50, sma_50_slope
        )
        trend_long = TechnicalAnalysisEngine.classify_trend_long_term(
            current_price, sma_200, sma_200_slope
        )
        trend_overall = TechnicalAnalysisEngine.classify_overall_trend(
            trend_short, trend_medium, trend_long, sma_20, sma_50, sma_200
        )

        return {
            "status": "success",
            "data": {
                "current_price": round(current_price, 2),
                "short_term": {
                    "trend": trend_short,
                    "sma_20": sma_20,
                    "sma_20_slope": sma_20_slope,
                    "interpretation": f"Price {'above' if current_price > (sma_20 or 0) else 'below'} 20DMA",
                },
                "medium_term": {
                    "trend": trend_medium,
                    "sma_50": sma_50,
                    "sma_50_slope": sma_50_slope,
                    "interpretation": f"Price {'above' if current_price > (sma_50 or 0) else 'below'} 50DMA",
                },
                "long_term": {
                    "trend": trend_long,
                    "sma_200": sma_200,
                    "sma_200_slope": sma_200_slope,
                    "interpretation": f"Price {'above' if current_price > (sma_200 or 0) else 'below'} 200DMA",
                },
                "overall": {
                    "trend": trend_overall,
                    "ma_alignment": f"20:{sma_20} > 50:{sma_50} > 200:{sma_200}" if sma_20 and sma_50 and sma_200 else "Insufficient data",
                },
            },
            "endpoint": "/technicals/trend",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Momentum Analysis
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_momentum_analysis(
        prices: List[float],
    ) -> Dict:
        """
        GET /api/securities/{ticker}/technicals/momentum

        Comprehensive momentum metrics (RSI, MACD, ROC).
        """
        metrics = TechnicalAnalysisEngine.calculate_momentum_metrics(prices)
        rsi = metrics.get("rsi_14")
        macd = metrics.get("macd", {})

        rsi_state = TechnicalAnalysisEngine.classify_rsi_state(rsi)

        return {
            "status": "success",
            "data": {
                "rsi": {
                    "value": rsi,
                    "state": rsi_state,
                    "zones": {
                        "oversold": "< 30",
                        "weak": "30-50",
                        "positive": "50-70",
                        "overbought": "> 70",
                    },
                    "current_zone": (
                        "oversold" if rsi and rsi < 30 else
                        "weak" if rsi and rsi < 50 else
                        "positive" if rsi and rsi < 70 else
                        "overbought" if rsi else "unknown"
                    ),
                },
                "macd": {
                    "line": macd.get("macd"),
                    "signal": macd.get("signal"),
                    "histogram": macd.get("histogram"),
                    "state": macd.get("state"),
                },
                "roc": {
                    "roc_5d_pct": metrics.get("roc_5d"),
                    "roc_20d_pct": metrics.get("roc_20d"),
                    "roc_60d_pct": metrics.get("roc_60d"),
                },
                "interpretation": f"Momentum is {rsi_state.lower()}",
            },
            "endpoint": "/technicals/momentum",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Volatility Analysis
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_volatility_analysis(
        current_price: float,
        highs: List[float],
        lows: List[float],
        prices: List[float],
    ) -> Dict:
        """
        GET /api/securities/{ticker}/technicals/volatility

        ATR, realized volatility, and volatility metrics.
        """
        atr = TechnicalAnalysisEngine.calculate_atr(highs, lows, prices, 14)
        atr_pct = TechnicalAnalysisEngine.calculate_volatility_pct(atr, current_price)

        # Calculate returns for realized volatility
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1] * 100
            returns.append(ret)

        realized_vol_20 = TechnicalAnalysisEngine.calculate_realized_volatility(returns, 20)
        realized_vol_60 = TechnicalAnalysisEngine.calculate_realized_volatility(returns, 60)

        return {
            "status": "success",
            "data": {
                "atr": {
                    "value": atr,
                    "pct_of_price": atr_pct,
                    "interpretation": f"Typical daily range: {atr_pct}% of price",
                },
                "realized_volatility": {
                    "vol_20d": realized_vol_20,
                    "vol_60d": realized_vol_60,
                },
                "volatility_assessment": (
                    "LOW" if atr_pct and atr_pct < 2 else
                    "MODERATE" if atr_pct and atr_pct < 4 else
                    "HIGH" if atr_pct and atr_pct < 7 else
                    "VERY_HIGH"
                ),
            },
            "endpoint": "/technicals/volatility",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Support & Resistance Levels
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_levels_analysis(
        highs: List[float],
        lows: List[float],
        current_price: float,
    ) -> Dict:
        """
        GET /api/securities/{ticker}/technicals/levels

        Support and resistance zones with strength ratings.
        """
        levels = TechnicalAnalysisEngine.identify_support_resistance_levels(highs, lows)

        support_zones = levels.get("support_zones", [])
        resistance_zones = levels.get("resistance_zones", [])

        # Find nearest support/resistance
        nearest_support = None
        nearest_resistance = None

        for level in support_zones:
            if level["level"] < current_price:
                if nearest_support is None or level["level"] > nearest_support["level"]:
                    nearest_support = level

        for level in resistance_zones:
            if level["level"] > current_price:
                if nearest_resistance is None or level["level"] < nearest_resistance["level"]:
                    nearest_resistance = level

        return {
            "status": "success",
            "data": {
                "current_price": round(current_price, 2),
                "support_zones": support_zones,
                "resistance_zones": resistance_zones,
                "nearest_support": nearest_support,
                "nearest_resistance": nearest_resistance,
                "interpretation": (
                    f"Support at {nearest_support['level'] if nearest_support else 'None'} | "
                    f"Resistance at {nearest_resistance['level'] if nearest_resistance else 'None'}"
                ),
            },
            "endpoint": "/technicals/levels",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Technical Events
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_technical_events(
        current_price: float,
        current_volume: float,
        prices: List[float],
        volumes: List[float],
        highs: List[float],
        lows: List[float],
    ) -> Dict:
        """
        GET /api/securities/{ticker}/technicals/events

        Recent technical events (crossovers, breakouts, extremes).
        """
        events = []

        # Moving average crossover
        if len(prices) >= 50:
            sma_20_prev = TechnicalAnalysisEngine.calculate_sma(prices[-51:-1], 20)
            sma_20_curr = TechnicalAnalysisEngine.calculate_sma(prices[-50:], 20)
            sma_50_prev = TechnicalAnalysisEngine.calculate_sma(prices[-51:-1], 50)
            sma_50_curr = TechnicalAnalysisEngine.calculate_sma(prices[-50:], 50)

            cross = TechnicalAnalysisEngine.detect_moving_average_cross(
                sma_20_prev, sma_20_curr, sma_50_prev, sma_50_curr
            )
            if cross:
                events.append({
                    "type": cross,
                    "date": date.today().isoformat(),
                    "severity": "HIGH",
                })

        # Breakout
        high_20d = max(highs[-20:]) if len(highs) >= 20 else max(highs)
        low_20d = min(lows[-20:]) if len(lows) >= 20 else min(lows)
        avg_vol_20d = TechnicalAnalysisEngine.calculate_average_volume(volumes[-20:], min(20, len(volumes))) if volumes else 0

        breakout = TechnicalAnalysisEngine.detect_breakout(
            current_price, current_volume, high_20d, avg_vol_20d or 1
        )
        if breakout:
            events.append({
                "type": str(breakout),
                "date": date.today().isoformat(),
                "severity": "HIGH",
            })

        breakdown = TechnicalAnalysisEngine.detect_breakdown(
            current_price, current_volume, low_20d, avg_vol_20d or 1
        )
        if breakdown:
            events.append({
                "type": str(breakdown),
                "date": date.today().isoformat(),
                "severity": "HIGH",
            })

        # 52-week highs/lows
        if len(highs) >= 252:
            high_52w = max(highs[-252:])
            low_52w = min(lows[-252:])

            if current_price >= high_52w * 0.99:
                events.append({
                    "type": "52W_HIGH_NEAR",
                    "date": date.today().isoformat(),
                    "severity": "MEDIUM",
                })

            if current_price <= low_52w * 1.01:
                events.append({
                    "type": "52W_LOW_NEAR",
                    "date": date.today().isoformat(),
                    "severity": "MEDIUM",
                })

        return {
            "status": "success",
            "data": {
                "recent_events": events,
                "event_count": len(events),
                "last_event": events[0] if events else None,
            },
            "endpoint": "/technicals/events",
        }

    # ════════════════════════════════════════════════════════════════════════════
    # ENDPOINT: Chart Data
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_chart_data(
        security_id: str,
        dates: List[str],
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        include_indicators: bool = True,
    ) -> Dict:
        """
        GET /api/securities/{ticker}/chart

        OHLCV data with optional technical indicators for charting.
        """
        if not dates or not closes:
            return {
                "status": "error",
                "message": "Insufficient data",
            }

        # Build candlestick data
        candlesticks = []
        for i in range(len(dates)):
            candlesticks.append({
                "date": dates[i],
                "open": round(opens[i], 2) if i < len(opens) else None,
                "high": round(highs[i], 2),
                "low": round(lows[i], 2),
                "close": round(closes[i], 2),
                "volume": volumes[i] if i < len(volumes) else 0,
            })

        chart_data = {
            "candlesticks": candlesticks,
        }

        # Add indicators if requested
        if include_indicators and len(closes) >= 200:
            mas = TechnicalAnalysisEngine.calculate_moving_averages(closes)
            atr = TechnicalAnalysisEngine.calculate_atr(highs, lows, closes, 14)
            rsi = TechnicalAnalysisEngine.calculate_rsi(closes, 14)

            chart_data["indicators"] = {
                "moving_averages": {
                    "sma_20": [TechnicalAnalysisEngine.calculate_sma(closes[:i+1], 20) for i in range(len(closes))],
                    "sma_50": [TechnicalAnalysisEngine.calculate_sma(closes[:i+1], 50) for i in range(len(closes))],
                    "sma_200": [TechnicalAnalysisEngine.calculate_sma(closes[:i+1], 200) for i in range(len(closes))],
                },
                "atr": atr,
                "rsi": rsi,
            }

        return {
            "status": "success",
            "data": chart_data,
            "endpoint": "/chart",
            "timeframe": "1D",
            "security_id": security_id,
        }
