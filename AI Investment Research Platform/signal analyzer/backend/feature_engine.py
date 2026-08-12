from __future__ import annotations

import numpy as np
import pandas as pd

from .quant_engine import ModelConfig, build_features, validate_prices


PRICE_FEATURES = [
    "return_1d", "return_2d", "return_3d", "return_5d", "return_10d", "return_20d", "return_60d",
    "relative_return_5d", "relative_return_20d", "relative_return_60d",
    "distance_high_20d", "distance_high_60d", "distance_high_252d",
    "distance_low_20d", "distance_low_60d", "distance_low_252d",
    "skew_20d", "skew_60d", "kurtosis_20d", "kurtosis_60d",
    "gap_return", "overnight_return", "intraday_return",
]
MOMENTUM_FEATURES = [
    "rsi_7", "rsi_14_extended", "rsi_21", "roc_5", "roc_10", "roc_20",
    "ema_gap_5", "ema_gap_10", "ema_gap_20", "ema_gap_50", "ema_gap_100", "ema_gap_200",
    "macd", "macd_signal", "macd_histogram",
]
VOLATILITY_FEATURES = [
    "realized_vol_5d", "realized_vol_10d", "realized_vol_20d", "realized_vol_60d",
    "atr_7_pct", "atr_14_pct_extended", "high_low_range", "average_range_20d",
    "vol_ratio_5_20", "vol_ratio_20_60", "vol_expansion_5d",
    "downside_vol_20d", "upside_vol_20d", "volatility_percentile",
]
LIQUIDITY_FEATURES = [
    "log_volume", "volume_ratio_5d", "volume_ratio_20d", "volume_ratio_60d",
    "volume_acceleration", "pkr_volume", "log_pkr_volume", "obv_change_20d",
    "volume_momentum_5d", "traded_frequency_20d", "zero_volume_frequency_20d",
    "amihud_20d", "amihud_60d", "liquidity_percentile",
]
CROSS_SECTIONAL_FEATURES = [
    "return_5d_percentile", "return_20d_percentile", "rsi_14_percentile",
    "volume_percentile", "relative_strength_percentile",
]
RELATIVE_STRENGTH_FEATURES = [
    "market_relative_5d", "market_relative_10d", "market_relative_20d",
    "sector_relative_5d", "sector_relative_10d", "sector_relative_20d",
    "relative_momentum", "relative_volatility", "relative_volume",
    "sector_return_rank", "market_momentum_rank", "sector_momentum_rank",
    "sector_volume_rank", "market_volatility_rank",
]
TECHNICAL_STRUCTURE_FEATURES = [
    "distance_support_20d", "distance_support_60d", "distance_resistance_20d", "distance_resistance_60d",
    "breakout_20d", "breakout_60d", "breakdown_20d", "breakdown_60d",
    "ema_20_50_crossover", "ema_50_200_crossover", "above_ema20", "above_ema50", "above_ema200",
    "ema20_slope_5d", "ema50_slope_5d", "ema200_slope_5d", "trend_strength", "adx_14",
]
SECTOR_FEATURES = [
    "sector_return_1d", "sector_return_5d", "sector_return_20d", "sector_volatility_20d",
    "sector_momentum", "sector_relative_strength", "sector_breadth_1d",
    "stock_return_rank_in_sector", "stock_volume_rank_in_sector",
]
EXTENDED_FEATURE_COLUMNS = PRICE_FEATURES + MOMENTUM_FEATURES + VOLATILITY_FEATURES + LIQUIDITY_FEATURES + CROSS_SECTIONAL_FEATURES + RELATIVE_STRENGTH_FEATURES + TECHNICAL_STRUCTURE_FEATURES + SECTOR_FEATURES
TARGET_COLUMNS = ["target_5d_return", "target_5d_excess_return", "target_direction", "target_downside"]

SECTOR_MAP = {
    "FFC":"Fertilizer", "EFERT":"Fertilizer", "MARI":"Energy", "OGDC":"Energy", "PPL":"Energy", "POL":"Energy",
    "PSO":"Energy", "HUBC":"Power", "SYS":"Technology", "TRG":"Technology", "HBL":"Banking", "MCB":"Banking",
    "UBL":"Banking", "NBP":"Banking", "BAHL":"Banking", "LUCK":"Cement", "FCCL":"Cement", "DGKC":"Cement",
    "MLCF":"Cement", "MTL":"Automobile", "INDU":"Automobile", "NESTLE":"Consumer", "COLG":"Consumer", "ILP":"Textile",
}


def _rsi(close: pd.Series, window: int) -> pd.Series:
    change = close.diff()
    gain = change.clip(lower=0).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    loss = (-change.clip(upper=0)).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    return (100 - 100 / (1 + gain / loss.replace(0, np.nan))) / 100


def _rolling_semideviation(returns: pd.Series, window: int, upside: bool) -> pd.Series:
    selected = returns.where(returns > 0 if upside else returns < 0)
    return selected.rolling(window, min_periods=max(3, window // 3)).std() * np.sqrt(252)


def build_panel_dataset(prices: pd.DataFrame, config: ModelConfig = ModelConfig()) -> pd.DataFrame:
    """Create one stock-date row with backward-looking features and four 5D targets."""
    clean = validate_prices(prices)
    base = build_features(clean, config)
    groups: list[pd.DataFrame] = []
    for _, g in base.groupby("symbol", sort=False):
        g = g.sort_values("date").copy()
        close, open_, volume, benchmark = g["close"], g["open"], g["volume"], g["benchmark_close"]
        returns = close.pct_change()
        benchmark_returns = benchmark.pct_change()
        previous_close = close.shift(1)
        true_range = pd.concat([(g["high"] - g["low"]), (g["high"] - previous_close).abs(), (g["low"] - previous_close).abs()], axis=1).max(axis=1)
        for days in (1, 2, 3, 5, 10, 20, 60):
            g[f"return_{days}d"] = close.pct_change(days)
        for days in (5, 20, 60):
            g[f"relative_return_{days}d"] = close.pct_change(days) - benchmark.pct_change(days)
        for days in (20, 60, 252):
            g[f"distance_high_{days}d"] = close / close.rolling(days).max() - 1
            g[f"distance_low_{days}d"] = close / close.rolling(days).min() - 1
        g["skew_20d"], g["skew_60d"] = returns.rolling(20).skew(), returns.rolling(60).skew()
        g["kurtosis_20d"], g["kurtosis_60d"] = returns.rolling(20).kurt(), returns.rolling(60).kurt()
        g["gap_return"] = open_ / previous_close - 1
        g["overnight_return"] = g["gap_return"]
        g["intraday_return"] = close / open_ - 1
        for days in (7, 14, 21):
            name = "rsi_14_extended" if days == 14 else f"rsi_{days}"
            g[name] = _rsi(close, days)
        g["roc_5"], g["roc_10"], g["roc_20"] = close.pct_change(5), close.pct_change(10), close.pct_change(20)
        for days in (5, 10, 20, 50, 100, 200):
            g[f"ema_gap_{days}"] = close / close.ewm(span=days, adjust=False, min_periods=days).mean() - 1
        ema12, ema26 = close.ewm(span=12, adjust=False).mean(), close.ewm(span=26, adjust=False).mean()
        g["macd"] = (ema12 - ema26) / close
        g["macd_signal"] = (ema12 - ema26).ewm(span=9, adjust=False).mean() / close
        g["macd_histogram"] = g["macd"] - g["macd_signal"]
        ema20 = close.ewm(span=20, adjust=False, min_periods=20).mean()
        ema50 = close.ewm(span=50, adjust=False, min_periods=50).mean()
        ema200 = close.ewm(span=200, adjust=False, min_periods=200).mean()
        g["ema_20_50_crossover"] = ema20 / ema50 - 1
        g["ema_50_200_crossover"] = ema50 / ema200 - 1
        g["above_ema20"] = (close > ema20).astype(float)
        g["above_ema50"] = (close > ema50).astype(float)
        g["above_ema200"] = (close > ema200).astype(float)
        g["ema20_slope_5d"] = ema20.pct_change(5)
        g["ema50_slope_5d"] = ema50.pct_change(5)
        g["ema200_slope_5d"] = ema200.pct_change(5)
        for days in (5, 10, 20, 60):
            g[f"realized_vol_{days}d"] = returns.rolling(days).std() * np.sqrt(252)
        g["atr_7_pct"] = true_range.rolling(7).mean() / close
        g["atr_14_pct_extended"] = true_range.rolling(14).mean() / close
        prior_high_20, prior_high_60 = g["high"].shift(1).rolling(20).max(), g["high"].shift(1).rolling(60).max()
        prior_low_20, prior_low_60 = g["low"].shift(1).rolling(20).min(), g["low"].shift(1).rolling(60).min()
        g["distance_support_20d"], g["distance_support_60d"] = close / prior_low_20 - 1, close / prior_low_60 - 1
        g["distance_resistance_20d"], g["distance_resistance_60d"] = close / prior_high_20 - 1, close / prior_high_60 - 1
        g["breakout_20d"], g["breakout_60d"] = (close > prior_high_20).astype(float), (close > prior_high_60).astype(float)
        g["breakdown_20d"], g["breakdown_60d"] = (close < prior_low_20).astype(float), (close < prior_low_60).astype(float)
        g["trend_strength"] = (ema20 - ema50).abs() / true_range.rolling(14).mean().replace(0, np.nan)
        up_move, down_move = g["high"].diff(), -g["low"].diff()
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
        atr14 = true_range.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
        plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False, min_periods=14).mean() / atr14
        minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False, min_periods=14).mean() / atr14
        g["adx_14"] = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
        g["high_low_range"] = (g["high"] - g["low"]) / close
        g["average_range_20d"] = g["high_low_range"].rolling(20).mean()
        g["vol_ratio_5_20"] = g["realized_vol_5d"] / g["realized_vol_20d"].replace(0, np.nan)
        g["vol_ratio_20_60"] = g["realized_vol_20d"] / g["realized_vol_60d"].replace(0, np.nan)
        g["vol_expansion_5d"] = g["realized_vol_5d"] - g["realized_vol_20d"]
        g["downside_vol_20d"] = _rolling_semideviation(returns, 20, False)
        g["upside_vol_20d"] = _rolling_semideviation(returns, 20, True)
        g["log_volume"] = np.log1p(volume)
        for days in (5, 20, 60):
            g[f"volume_ratio_{days}d"] = volume / volume.rolling(days).mean().replace(0, np.nan)
        g["volume_acceleration"] = g["volume_ratio_5d"] - g["volume_ratio_20d"]
        g["pkr_volume"] = close * volume
        g["log_pkr_volume"] = np.log1p(g["pkr_volume"])
        direction = np.sign(close.diff()).fillna(0)
        obv = (direction * volume).cumsum()
        g["obv_change_20d"] = obv.diff(20) / volume.rolling(20).sum().replace(0, np.nan)
        g["volume_momentum_5d"] = volume.pct_change(5).replace([np.inf, -np.inf], np.nan)
        g["traded_frequency_20d"] = (volume > 0).rolling(20).mean()
        g["zero_volume_frequency_20d"] = (volume <= 0).rolling(20).mean()
        illiquidity = returns.abs() / g["pkr_volume"].replace(0, np.nan)
        g["amihud_20d"] = illiquidity.rolling(20, min_periods=5).mean()
        g["amihud_60d"] = illiquidity.rolling(60, min_periods=15).mean()
        g["target_5d_return"] = g["forward_stock_return"]
        g["target_5d_excess_return"] = g["forward_excess_return"]
        g["target_direction"] = g["target"]
        g["target_downside"] = (g["forward_stock_return"] < -0.05).astype(float)
        g.loc[g["forward_stock_return"].isna(), "target_downside"] = np.nan
        groups.append(g)
    panel = pd.concat(groups, ignore_index=True).replace([np.inf, -np.inf], np.nan)
    panel["sector"] = panel["symbol"].map(SECTOR_MAP).fillna("Unknown")
    # Percentiles are computed within the same date, never across future dates.
    percentile_sources = {
        "volatility_percentile": "realized_vol_20d", "liquidity_percentile": "pkr_volume",
        "return_5d_percentile": "return_5d", "return_20d_percentile": "return_20d",
        "rsi_14_percentile": "rsi_14_extended", "volume_percentile": "volume_ratio_20d",
        "relative_strength_percentile": "relative_return_20d",
    }
    for destination, source in percentile_sources.items():
        panel[destination] = panel.groupby("date")[source].rank(pct=True)
    for days in (5, 10, 20):
        market_return = panel.groupby("date")[f"return_{days}d"].transform("mean")
        sector_return = panel.groupby(["date", "sector"])[f"return_{days}d"].transform("mean")
        panel[f"market_relative_{days}d"] = panel[f"return_{days}d"] - market_return
        panel[f"sector_relative_{days}d"] = panel[f"return_{days}d"] - sector_return
    market_volatility = panel.groupby("date")["realized_vol_20d"].transform("mean")
    market_volume = panel.groupby("date")["volume_ratio_20d"].transform("mean")
    panel["relative_momentum"] = panel["market_relative_20d"] - panel["market_relative_5d"]
    panel["relative_volatility"] = panel["realized_vol_20d"] - market_volatility
    panel["relative_volume"] = panel["volume_ratio_20d"] - market_volume
    panel["sector_return_rank"] = panel.groupby(["date", "sector"])["return_20d"].rank(pct=True)
    panel["market_momentum_rank"] = panel.groupby("date")["return_20d"].rank(pct=True)
    panel["sector_momentum_rank"] = panel.groupby(["date", "sector"])["return_20d"].rank(pct=True)
    panel["sector_volume_rank"] = panel.groupby(["date", "sector"])["volume_ratio_20d"].rank(pct=True)
    panel["market_volatility_rank"] = panel.groupby("date")["realized_vol_20d"].rank(pct=True)
    for days in (1, 5, 20):
        panel[f"sector_return_{days}d"] = panel.groupby(["date", "sector"])[f"return_{days}d"].transform("mean")
    panel["sector_volatility_20d"] = panel.groupby(["date", "sector"])["realized_vol_20d"].transform("mean")
    panel["sector_momentum"] = panel["sector_return_20d"]
    panel["sector_relative_strength"] = panel["sector_return_20d"] - panel.groupby("date")["return_20d"].transform("mean")
    panel["sector_breadth_1d"] = (panel["return_1d"] > 0).groupby([panel["date"], panel["sector"]]).transform("mean")
    panel["stock_return_rank_in_sector"] = panel.groupby(["date", "sector"])["return_20d"].rank(pct=True)
    panel["stock_volume_rank_in_sector"] = panel.groupby(["date", "sector"])["volume_ratio_20d"].rank(pct=True)
    return panel.sort_values(["date", "symbol"]).reset_index(drop=True)


def feature_manifest() -> dict:
    return {
        "price_return": PRICE_FEATURES, "momentum": MOMENTUM_FEATURES,
        "volatility": VOLATILITY_FEATURES, "volume_liquidity": LIQUIDITY_FEATURES,
        "cross_sectional": CROSS_SECTIONAL_FEATURES, "relative_strength": RELATIVE_STRENGTH_FEATURES,
        "technical_structure": TECHNICAL_STRUCTURE_FEATURES,
        "sector": SECTOR_FEATURES,
        "unavailable_pending_licensed_data": [
            "turnover_to_market_cap", "bid_ask_spread", "free_float_liquidity",
            "sector_features", "point_in_time_fundamentals", "fama_french_factors",
        ],
    }
