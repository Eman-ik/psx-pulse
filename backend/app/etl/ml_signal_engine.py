"""Walk-forward-validated calibrated ML signal engine.

Companion to app/etl/signal_engine.py, not a replacement -- that module is deliberately
rules-based, arguing (see its module docstring) that a ~5-company fertilizer-pilot universe is
too thin to validate a trained model honestly. This module resolves that objection by pooling
the classifier across the FULL PSX universe already in PriceOHLCV (~250 symbols, most with
deep 2005-onward history), not just the fertilizer names -- then simply stores the pooled
model's per-issuer output for whichever sector each issuer belongs to. Evidence class:
"predictive_model_output" (see app/db/models/evidence.py), same as the rules-based engine.

Core feature engineering / walk-forward validation / calibration logic (validate_prices,
build_features, walk_forward_predictions, validation_metrics, SignalModel) is ported near-
verbatim from a prototype quant research pipeline (`AI Investment Research Platform/signal
analyzer/backend/quant_engine.py`) that was proven out separately against Yahoo Finance data.
Only the DB-facing pieces below (load_price_panel, synthetic_benchmark, run_for_all_issuers)
are new.

Benchmark note: the pipeline requires a `benchmark_close` column to compute excess returns.
The DB's real index tables (KSE100/FERTIX/CEMENTIX) only go back to July 2024 (~500 trading
days) -- too shallow for this pipeline's 635-day walk-forward minimum. Instead, synthetic_
benchmark() builds an equal-weighted average-return benchmark directly from the same deep stock
panel (available back to 2005), exactly the approximation the prototype's own yahoo_research.py
uses when it lacks a clean index. This is explicitly NOT the real KSE-100 -- see its docstring.

Signal is never "SELL" -- see SignalModel.rank(): this classifier only estimates the
probability of clearing a positive-excess-return hurdle, so a low probability is evidence of
"no edge detected", not evidence of a negative return.

is_public always tracks settings.ml_signals_enabled at compute time (never hardcoded), same
non-negotiable compliance gate as signal_engine.py.

Fundamental features (2026-08-27): load_fundamental_panel() joins ratio_engine.py's already-
computed RatioValue rows (EPS/revenue/PAT growth, margins, ROE, debt/equity, P/E, etc.) into
the feature set -- see that function's own docstring for the point-in-time anchoring this
required (financial_fact/ratio_value have no real "when this became public" timestamp of
their own; this anchors each ratio to the issuer's actual results-announcement date instead).
Coverage is narrow (17 of ~250 pooled issuers as of 2026-08-27) and deliberately NOT required
for a row to enter training/scoring -- see TECHNICAL_FEATURE_COLUMNS vs FEATURE_COLUMNS below.

Market/sector-relative features (2026-08-27): load_market_index_panel()/load_sector_context_
panel() join real KSE-100 + FERTIX/CEMENTIX index returns in, distinct from TECHNICAL_FEATURE_
COLUMNS' relative_21d/relative_63d (which compare against the synthetic pooled-universe
benchmark, not a real index). See those functions' own docstrings for the real coverage
constraint (~500 trading days on file, sector limited to Fertilizer/Cement).

Classifier choice (2026-08-27): ModelConfig.classifier selects "logistic" (production
default) or "gbm" (HistGradientBoostingClassifier) -- see ModelConfig's own comment. "gbm"
is a real, promising walk-forward result (every metric improved over logistic on the
identical feature set) but is not yet the default: still below the qualification floor on
an untuned run. See model_governance.md for the numbers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import (
    Announcement,
    IndexOHLCV,
    Issuer,
    MarketIndex,
    MlSignalScore,
    PriceOHLCV,
    RatioDefinition,
    RatioValue,
    Sector,
    Security,
)

logger = logging.getLogger(__name__)

MODEL_VERSION = 1

# How stale a security's most recent trade can be (in calendar days) before it's excluded from
# a scoring run -- catches delisted/suspended/merged names (e.g. FFBL post FFC-FFBL merger)
# that would otherwise get a signal computed from data that's no longer representative.
STALENESS_TOLERANCE_DAYS = 21

# Same bar as D:/khronos/signal_qualification.py's Kronos gate -- this model had no
# significance test at all until 2026-08-27 (accuracy floor + naive-baseline only), a real
# parity gap with Kronos's own gate. Not stricter than Kronos's bar on principle: this is
# about bringing the two gates into alignment, not making one arbitrarily harder to clear
# than the other.
SIGNIFICANCE_P_VALUE = 0.10


def binomial_two_sided_p_value(hits: int, n: int, p: float) -> float:
    """Exact two-sided binomial test: P(X as or more extreme than `hits`) under X ~
    Binomial(n, p). Kronos's own gate (D:/khronos/build_validation_record.py) computes this
    via a hand-rolled exact PMF over math.comb, viable there because its n is always small
    (15-93 observations). This model's n can be tens of thousands (buy_mask over a 180k+-row
    pooled population) -- math.comb(n, k) for n in that range produces integers with
    thousands of digits, and mixing that with tiny floating-point probabilities overflows or
    loses precision. scipy.stats.binomtest is the numerically stable version of the exact
    same test; scipy is already a hard dependency of sklearn (used throughout this module),
    not a new one being pulled in just for this.

    p is the null-hypothesis probability -- here that's positive_rate (the walk-forward
    population's own base rate), not a fixed 0.5: the question isn't "is this better than a
    coin flip," it's "is this confident subset's precision distinguishable from what a
    random same-sized subset of THIS population would score by chance."
    """
    if n == 0:
        return 1.0
    return float(binomtest(hits, n, p, alternative="two-sided").pvalue)

REQUIRED_COLUMNS = {"date", "symbol", "open", "high", "low", "close", "volume", "benchmark_close"}
TECHNICAL_FEATURE_COLUMNS = [
    "return_5d", "return_21d", "return_63d", "relative_21d", "relative_63d",
    "ma_gap_20", "ma_gap_50", "rsi_14", "atr_pct", "volatility_21d",
    "volume_z_21d", "drawdown_63d", "breakout_63d",
]
# RatioDefinition.key values pulled from ratio_engine.py's already-computed suite -- picked for
# the widest real coverage within each category (growth/profitability/leverage/liquidity/
# valuation), not an exhaustive list of every ratio that engine can produce. Column names match
# the DB key exactly (see load_fundamental_panel), so no renaming step is needed.
FUNDAMENTAL_FEATURE_COLUMNS = [
    "eps_growth_yoy", "revenue_growth_yoy", "pat_growth_yoy", "net_profit_margin",
    "roe", "debt_to_equity", "current_ratio", "price_to_earnings", "dividend_payout_ratio",
]
# KSE100 = real broad-market index; sector = FERTIX/CEMENTIX, the only two sector indices this
# DB has (see load_sector_index_panel). Distinct from TECHNICAL_FEATURE_COLUMNS' relative_21d/
# relative_63d, which are already computed against the synthetic pooled-universe benchmark
# (see synthetic_benchmark()) -- these use the REAL index instead, and add a genuinely
# different comparison (sector-specific, not "vs. an equal-weighted average of the whole
# pool"). Real, narrower-than-fundamentals coverage constraint: KSE100/FERTIX/CEMENTIX only
# have ~500 trading days on file (2024-07 to 2026-07) versus decades of price history for
# many pooled symbols -- these columns are NaN outside that window for every symbol, and
# sector_* is additionally NaN for every symbol outside Fertilizer/Cement (33 of ~250 pooled
# issuers). See load_market_index_panel/load_sector_index_panel's own docstrings.
MARKET_FEATURE_COLUMNS = [
    "market_return_5d", "market_return_21d", "stock_minus_market_5d", "stock_minus_market_21d",
    "sector_return_5d", "sector_return_21d", "stock_minus_sector_5d", "stock_minus_sector_21d",
]
# Passed to the model's .fit()/.predict_proba() -- the sklearn pipeline's SimpleImputer handles
# NaN here. NOT the same list used to decide whether a row is eligible for training/scoring at
# all (see TECHNICAL_FEATURE_COLUMNS' use in walk_forward_predictions/SignalModel.rank): requiring
# fundamentals or market/sector features there would silently shrink the pooled universe down to
# whichever narrow slice has real coverage, defeating the reason this model is pooled broadly in
# the first place.
FEATURE_COLUMNS = TECHNICAL_FEATURE_COLUMNS + FUNDAMENTAL_FEATURE_COLUMNS + MARKET_FEATURE_COLUMNS


CLASSIFIERS = ("logistic", "gbm")


@dataclass(frozen=True)
class ModelConfig:
    horizon_days: int = 5
    excess_return_threshold: float = 0.0
    transaction_cost: float = 0.004
    min_train_days: int = 504
    test_days: int = 126
    embargo_days: int = 5
    buy_probability: float = 0.60
    sell_probability: float = 0.40
    minimum_validated_accuracy: float = 0.60
    minimum_observations: int = 30
    # "logistic" is still the production default -- "gbm" (HistGradientBoostingClassifier) is
    # a real, promising diagnostic result (2026-08-27: +3.18pp buy_precision, every metric
    # improved, holding the exact same feature set fixed) but still below
    # minimum_validated_accuracy on an untuned run, so switching the default would not
    # currently change any live signal outcome -- still gated to NO_SIGNAL either way. See
    # model_governance.md for the real numbers before treating "gbm" as anything more than
    # an option to keep validating, not a proven replacement.
    classifier: str = "logistic"

    def __post_init__(self) -> None:
        if self.classifier not in CLASSIFIERS:
            raise ValueError(f"classifier must be one of {CLASSIFIERS}, got {self.classifier!r}")


@dataclass
class ValidationMetrics:
    observations: int
    accuracy: float
    buy_precision: float
    sell_precision: float
    brier_score: float
    roc_auc: float | None
    positive_rate: float
    beats_naive_baseline: bool
    p_value_vs_naive_baseline: float
    significant_at_10pct: bool


# ─── Pure pandas/sklearn pipeline (ported from the prototype's quant_engine.py) ────────────────


def validate_prices(frame: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required price columns: {sorted(missing)}")
    out = frame.copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise")
    out["symbol"] = out["symbol"].astype(str).str.upper().str.strip()
    numeric = ["open", "high", "low", "close", "volume", "benchmark_close"]
    out[numeric] = out[numeric].apply(pd.to_numeric, errors="coerce")
    if out[numeric].isna().any().any():
        raise ValueError("OHLCV and benchmark values must be numeric and non-null")
    if (out[["open", "high", "low", "close", "benchmark_close"]] <= 0).any().any():
        raise ValueError("Prices must be positive")
    if (out["volume"] < 0).any():
        raise ValueError("Volume cannot be negative")
    if out.duplicated(["date", "symbol"]).any():
        raise ValueError("Duplicate date/symbol rows found")
    return out.sort_values(["symbol", "date"]).reset_index(drop=True)


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    return 100 - 100 / (1 + gain / loss.replace(0, np.nan))


def build_features(
    prices: pd.DataFrame,
    config: ModelConfig = ModelConfig(),
    fundamentals: pd.DataFrame | None = None,
    market_index: pd.DataFrame | None = None,
    sector_context: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build backward-looking features and forward excess-return labels.

    fundamentals, if given, must have columns ["symbol", "known_as_of", *FUNDAMENTAL_FEATURE_
    COLUMNS] -- see load_fundamental_panel(). Joined via pd.merge_asof (direction="backward",
    grouped by symbol): each price bar gets the most recent fundamental row whose known_as_of
    is on or before that bar's own date, never a later one -- the actual point-in-time
    guarantee, not just a date-shaped column. A symbol with no fundamental coverage, or no
    fundamentals param at all, gets real NaN in these columns (see FEATURE_COLUMNS' module-
    level comment for how the rest of the pipeline handles that).

    market_index (columns ["date", "market_return_5d", "market_return_21d"], see
    load_market_index_panel) and sector_context (columns ["symbol", "date",
    "sector_return_5d", "sector_return_21d"], see load_sector_context_panel) are joined by
    plain date (and symbol, for sector) -- an index close is same-day public information,
    unlike fundamentals, so no point-in-time lag is needed here.
    """
    df = validate_prices(prices)
    groups: list[pd.DataFrame] = []
    for _, g in df.groupby("symbol", sort=False):
        g = g.copy().sort_values("date")
        close, bench = g["close"], g["benchmark_close"]
        previous = close.shift(1)
        true_range = pd.concat([
            g["high"] - g["low"],
            (g["high"] - previous).abs(),
            (g["low"] - previous).abs(),
        ], axis=1).max(axis=1)
        returns = close.pct_change()
        for days in (5, 21, 63):
            g[f"return_{days}d"] = close.pct_change(days)
        g["relative_21d"] = g["return_21d"] - bench.pct_change(21)
        g["relative_63d"] = g["return_63d"] - bench.pct_change(63)
        g["ma_gap_20"] = close / close.rolling(20).mean() - 1
        g["ma_gap_50"] = close / close.rolling(50).mean() - 1
        g["rsi_14"] = _rsi(close) / 100
        g["atr_pct"] = true_range.rolling(14).mean() / close
        g["volatility_21d"] = returns.rolling(21).std() * np.sqrt(252)
        volume_mean = g["volume"].rolling(21).mean()
        volume_std = g["volume"].rolling(21).std().replace(0, np.nan)
        g["volume_z_21d"] = (g["volume"] - volume_mean) / volume_std
        g["drawdown_63d"] = close / close.rolling(63).max() - 1
        g["breakout_63d"] = close / close.shift(1).rolling(63).max() - 1
        stock_forward = close.shift(-config.horizon_days) / close - 1
        bench_forward = bench.shift(-config.horizon_days) / bench - 1
        g["forward_stock_return"] = stock_forward
        g["forward_benchmark_return"] = bench_forward
        g["forward_excess_return"] = stock_forward - bench_forward
        g["net_forward_excess_return"] = g["forward_excess_return"] - config.transaction_cost
        g["target"] = (g["forward_excess_return"] > config.excess_return_threshold).astype(float)
        g.loc[g["forward_excess_return"].isna(), "target"] = np.nan
        groups.append(g)
    result = pd.concat(groups, ignore_index=True).replace([np.inf, -np.inf], np.nan)
    # merge_asof (and, to be safe, the plain merges below too) require the "on" columns to
    # share an exact datetime64 unit (s/us/ns) -- real, reproduced failure: "date" (from a
    # plain SQL DATE column, no time-of-day) and a timestamp column from a separately-loaded
    # frame can get inferred to different units by pandas depending on the exact data,
    # causing a MergeError unrelated to the actual values. Cast once here rather than rely on
    # incidental dtype agreement between independently-loaded frames.
    result["date"] = result["date"].astype("datetime64[ns]")

    if fundamentals is not None and not fundamentals.empty:
        right = fundamentals.copy()
        right["known_as_of"] = right["known_as_of"].astype("datetime64[ns]")
        result = pd.merge_asof(
            result.sort_values("date"),
            right.sort_values("known_as_of"),
            left_on="date", right_on="known_as_of", by="symbol", direction="backward",
        ).sort_values(["symbol", "date"]).reset_index(drop=True)
        for col in FUNDAMENTAL_FEATURE_COLUMNS:
            if col not in result.columns:
                result[col] = np.nan
    else:
        for col in FUNDAMENTAL_FEATURE_COLUMNS:
            result[col] = np.nan

    if market_index is not None and not market_index.empty:
        mi = market_index.copy()
        mi["date"] = mi["date"].astype("datetime64[ns]")
        result = result.merge(mi, on="date", how="left")
    else:
        result["market_return_5d"] = np.nan
        result["market_return_21d"] = np.nan

    if sector_context is not None and not sector_context.empty:
        sc = sector_context.copy()
        sc["date"] = sc["date"].astype("datetime64[ns]")
        result = result.merge(sc, on=["symbol", "date"], how="left")
    else:
        result["sector_return_5d"] = np.nan
        result["sector_return_21d"] = np.nan

    result["stock_minus_market_5d"] = result["return_5d"] - result["market_return_5d"]
    result["stock_minus_market_21d"] = result["return_21d"] - result["market_return_21d"]
    result["stock_minus_sector_5d"] = result["return_5d"] - result["sector_return_5d"]
    result["stock_minus_sector_21d"] = result["return_21d"] - result["sector_return_21d"]

    return result


def _base_model(config: ModelConfig = ModelConfig()) -> Pipeline:
    """"logistic" is still the production default; "gbm" is a real, promising diagnostic
    result (see ModelConfig.classifier's own comment) not yet promoted to default. Both
    still route through the same SimpleImputer -- HistGradientBoostingClassifier has its own
    native NaN handling, but keeping the imputer here makes the two pipelines an
    apples-to-apples comparison (same preprocessing, only the classifier differs), matching
    the diagnostic script this was promoted from.
    """
    if config.classifier == "gbm":
        return Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("model", HistGradientBoostingClassifier(
                max_iter=200, max_depth=4, learning_rate=0.05,
                class_weight="balanced", random_state=42,
            )),
        ])
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(C=0.35, class_weight="balanced", max_iter=2000)),
    ])


def walk_forward_predictions(features: pd.DataFrame, config: ModelConfig = ModelConfig()) -> pd.DataFrame:
    labelled = features.dropna(subset=TECHNICAL_FEATURE_COLUMNS + ["target"]).sort_values("date")
    dates = np.array(sorted(labelled["date"].unique()))
    if len(dates) < config.min_train_days + config.embargo_days + config.test_days:
        raise ValueError(
            f"Need at least {config.min_train_days + config.embargo_days + config.test_days} "
            f"trading dates; received {len(dates)}"
        )
    outputs: list[pd.DataFrame] = []
    cursor = config.min_train_days + config.embargo_days
    while cursor < len(dates):
        test_dates = dates[cursor: cursor + config.test_days]
        cutoff = dates[cursor - config.embargo_days]
        train = labelled[labelled["date"] < cutoff]
        test = labelled[labelled["date"].isin(test_dates)]
        if train["target"].nunique() < 2 or test.empty:
            cursor += config.test_days
            continue
        model = _base_model(config).fit(train[FEATURE_COLUMNS], train["target"].astype(int))
        fold = test[["date", "symbol", "target", "forward_excess_return", "net_forward_excess_return"]].copy()
        fold["probability"] = model.predict_proba(test[FEATURE_COLUMNS])[:, 1]
        outputs.append(fold)
        cursor += config.test_days
    if not outputs:
        raise ValueError("Walk-forward validation produced no eligible folds")
    return pd.concat(outputs, ignore_index=True)


def validation_metrics(predictions: pd.DataFrame) -> ValidationMetrics:
    y = predictions["target"].astype(int).to_numpy()
    p = predictions["probability"].to_numpy()
    predicted = (p >= 0.5).astype(int)
    auc = float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None
    buy_mask, sell_mask = p >= 0.6, p <= 0.4
    buy_precision = precision_score(y[buy_mask], np.ones(buy_mask.sum()), zero_division=0) if buy_mask.any() else 0.0
    sell_precision = precision_score(1 - y[sell_mask], np.ones(sell_mask.sum()), zero_division=0) if sell_mask.any() else 0.0
    # buy_precision alone is the same trap Kronos's walk-forward gate had (see
    # signal_qualification.py's beats_naive_baseline): a fixed 60% floor means nothing if
    # 60%+ of the whole walk-forward population already clears the excess-return hurdle --
    # a "confident" subset that just mirrors the population's own base rate has learned
    # nothing, no matter how high its raw precision looks. positive_rate is what a random,
    # size-matched subset of this exact population would score by construction; a real BUY
    # signal must concentrate true positives at a higher rate than that, not just clear an
    # arbitrary constant.
    positive_rate = float(y.mean()) if len(y) else 0.0
    # Significance test against positive_rate (not a fixed 0.5) -- see
    # binomial_two_sided_p_value's own docstring for why the null here is the population's
    # own base rate, and why this uses scipy rather than Kronos's hand-rolled exact PMF.
    n_buy = int(buy_mask.sum())
    buy_hits = int(y[buy_mask].sum()) if n_buy else 0
    p_value = binomial_two_sided_p_value(buy_hits, n_buy, positive_rate)
    return ValidationMetrics(
        observations=len(y), accuracy=float(accuracy_score(y, predicted)),
        buy_precision=float(buy_precision), sell_precision=float(sell_precision),
        brier_score=float(brier_score_loss(y, p)), roc_auc=auc,
        positive_rate=positive_rate, beats_naive_baseline=float(buy_precision) > positive_rate,
        p_value_vs_naive_baseline=p_value, significant_at_10pct=p_value < SIGNIFICANCE_P_VALUE,
    )


class SignalModel:
    def __init__(
        self,
        config: ModelConfig = ModelConfig(),
        fundamentals: pd.DataFrame | None = None,
        market_index: pd.DataFrame | None = None,
        sector_context: pd.DataFrame | None = None,
    ):
        self.config = config
        self.fundamentals = fundamentals
        self.market_index = market_index
        self.sector_context = sector_context
        self.model: CalibratedClassifierCV | None = None
        self.metrics: ValidationMetrics | None = None

    def fit(self, prices: pd.DataFrame) -> "SignalModel":
        features = build_features(prices, self.config, self.fundamentals, self.market_index, self.sector_context)
        predictions = walk_forward_predictions(features, self.config)
        self.metrics = validation_metrics(predictions)
        labelled = features.dropna(subset=TECHNICAL_FEATURE_COLUMNS + ["target"])
        # Calibration uses a later, disjoint time block; the embargo prevents overlapping
        # forward-return labels from leaking into calibration.
        dates = np.array(sorted(labelled["date"].unique()))
        calibration_start = int(len(dates) * 0.8)
        train_end = calibration_start - self.config.embargo_days
        train = labelled[labelled["date"].isin(dates[:train_end])]
        calibration = labelled[labelled["date"].isin(dates[calibration_start:])]
        if train["target"].nunique() < 2 or calibration["target"].nunique() < 2:
            raise ValueError("Training and calibration periods must contain both target classes")
        fitted = _base_model(self.config).fit(train[FEATURE_COLUMNS], train["target"].astype(int))
        self.model = CalibratedClassifierCV(FrozenEstimator(fitted), method="sigmoid")
        self.model.fit(calibration[FEATURE_COLUMNS], calibration["target"].astype(int))
        return self

    def rank(self, prices: pd.DataFrame) -> list[dict]:
        if self.model is None or self.metrics is None:
            raise RuntimeError("Model must be fitted before ranking")
        features = build_features(prices, self.config, self.fundamentals, self.market_index, self.sector_context)
        latest = features.dropna(subset=TECHNICAL_FEATURE_COLUMNS).sort_values("date").groupby("symbol").tail(1).copy()
        latest["probability"] = self.model.predict_proba(latest[FEATURE_COLUMNS])[:, 1]
        eligible = self.metrics.observations >= self.config.minimum_observations
        # This classifier estimates only the probability of clearing the positive excess-return
        # hurdle. A low probability is not evidence of a negative return, so SELL is withheld
        # until a separate downside model is fitted and validated.
        validated_accuracy = self.metrics.buy_precision
        qualified = (
            eligible
            and validated_accuracy >= self.config.minimum_validated_accuracy
            and self.metrics.beats_naive_baseline
            and self.metrics.significant_at_10pct
        )
        records = []
        for row in latest.itertuples():
            probability = float(row.probability)
            signal = "NO SIGNAL"
            if qualified:
                if probability >= self.config.buy_probability:
                    signal = "BUY"
                else:
                    signal = "HOLD"
            records.append({
                "symbol": row.symbol, "as_of": row.date.date().isoformat(), "price": round(float(row.close), 2),
                "signal": signal, "outperformance_probability": round(probability, 4),
                "validation_observations": self.metrics.observations,
                "validation_accuracy": round(self.metrics.accuracy, 4),
                "validation_buy_precision": round(self.metrics.buy_precision, 4),
                "validation_sell_precision": round(self.metrics.sell_precision, 4),
                "validation_brier_score": round(self.metrics.brier_score, 4),
                "validation_roc_auc": round(self.metrics.roc_auc, 4) if self.metrics.roc_auc is not None else None,
                "validation_positive_rate": round(self.metrics.positive_rate, 4),
                "beats_naive_baseline": self.metrics.beats_naive_baseline,
                "validation_p_value": round(self.metrics.p_value_vs_naive_baseline, 6),
                "significant_at_10pct": self.metrics.significant_at_10pct,
            })
        return sorted(records, key=lambda x: x["outperformance_probability"], reverse=True)


def synthetic_market(symbols: Iterable[str] = ("MARI", "SYS", "FFC", "HBL", "LUCK", "OGDC"), days: int = 720, seed: int = 42) -> pd.DataFrame:
    """Deterministic development/test data. Never presented as live market data."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    benchmark_returns = rng.normal(0.00035, 0.011, days)
    benchmark = 100_000 * np.cumprod(1 + benchmark_returns)
    rows = []
    for index, symbol in enumerate(symbols):
        factor = (index - 2.5) * 0.00008
        returns = 0.65 * benchmark_returns + rng.normal(0.00025 + factor, 0.014 + index * 0.0004, days)
        close = (80 + index * 35) * np.cumprod(1 + returns)
        open_ = close * (1 + rng.normal(0, 0.004, days))
        spread = np.abs(rng.normal(0.01, 0.004, days))
        volume = rng.lognormal(14.2 + index * 0.08, 0.45, days).astype(int)
        for i, day in enumerate(dates):
            rows.append({
                "date": day, "symbol": symbol, "open": open_[i],
                "high": max(open_[i], close[i]) * (1 + spread[i]), "low": min(open_[i], close[i]) * (1 - spread[i]),
                "close": close[i], "volume": volume[i], "benchmark_close": benchmark[i],
            })
    return pd.DataFrame(rows)


# ─── DB-facing orchestration (new) ──────────────────────────────────────────────────────────


def load_price_panel(db: Session, config: ModelConfig = ModelConfig(), as_of: date | None = None) -> pd.DataFrame:
    """Loads date/symbol/OHLCV rows for every active, sufficiently-covered, non-stale security.

    "Sufficiently covered" = at least enough distinct trade dates for one walk-forward fold
    (min_train_days + embargo_days + test_days). "Non-stale" = last trade within
    STALENESS_TOLERANCE_DAYS of as_of, which excludes delisted/suspended/merged names (e.g.
    FFBL after the FFC-FFBL merger) whose price series simply stopped updating.

    Drops rows with open <= 0 (real, confirmed pattern: 46 of 208,113 rows across 9 mostly-
    illiquid small-cap symbols as of 2026-08-27, e.g. AHCL/ALAC/AMBL -- a thin-trading-day
    scraping artifact where high/low/close are real but no open was reported and psxdata
    defaulted it to 0, not a genuine zero price). validate_prices() downstream requires every
    OHLC column strictly positive and would otherwise reject the *entire* panel over 0.02% of
    rows. Same "skip, don't guess" convention as app/ingestion/psx_prices.py's OHLC handling --
    dropped, not imputed, since there's no reliable way to know what the open actually was.
    """
    as_of = as_of or date.today()
    min_bars = config.min_train_days + config.embargo_days + config.test_days
    stale_cutoff = as_of - timedelta(days=STALENESS_TOLERANCE_DAYS)

    eligible_security_ids = select(PriceOHLCV.security_id).group_by(PriceOHLCV.security_id).having(
        func.count(PriceOHLCV.id) >= min_bars,
        func.max(PriceOHLCV.trade_date) >= stale_cutoff,
    )

    query = (
        select(
            PriceOHLCV.trade_date.label("date"),
            Security.symbol.label("symbol"),
            PriceOHLCV.open, PriceOHLCV.high, PriceOHLCV.low, PriceOHLCV.close, PriceOHLCV.volume,
        )
        .join(Security, Security.id == PriceOHLCV.security_id)
        .where(Security.is_active.is_(True), PriceOHLCV.security_id.in_(eligible_security_ids))
        .order_by(Security.symbol, PriceOHLCV.trade_date)
    )
    frame = pd.read_sql(query, db.connection())
    if frame.empty:
        return frame
    numeric_cols = ["open", "high", "low", "close"]
    frame[numeric_cols] = frame[numeric_cols].astype(float)
    frame["volume"] = frame["volume"].fillna(0).astype(float)

    bad_open = frame["open"] <= 0
    if bad_open.any():
        logger.warning(
            "Dropping %d row(s) with open<=0 (scraping artifact, not a real price): %s",
            int(bad_open.sum()), sorted(frame.loc[bad_open, "symbol"].unique().tolist()),
        )
        frame = frame.loc[~bad_open].reset_index(drop=True)
    return frame


def load_fundamental_panel(db: Session) -> pd.DataFrame:
    """Point-in-time-safe fundamental ratios, one row per issuer per reporting period,
    resolved to a real symbol.

    Neither financial_fact nor ratio_value carries a genuine "when this became public"
    timestamp -- period_end is when the reporting PERIOD ended, not when the figure was
    released, and both tables' created_at/calculated_at are just this app's own ingestion
    time (confirmed: every financial_fact row was created on one of two dates, 2026-07-26
    or 2026-07-30, regardless of which fiscal year it covers -- a one-off backfill, not an
    ongoing feed). Using either as "known as of" would leak future information into a
    walk-forward feature -- exactly what this whole pipeline's walk-forward discipline
    exists to prevent elsewhere.

    Anchored instead to the issuer's own real "results" announcement (Announcement.category
    == "results", a genuinely per-event-timestamped row) published on or after that ratio's
    period_end -- the earliest such announcement is the actual date the figure became
    public. A ratio/period with no matching results announcement is dropped, not guessed at
    (same "skip, don't guess" convention as app/ingestion/psx_prices.py's OHLC handling) --
    there is no regulatory-filing-deadline shortcut applied here.

    Coverage is narrow by construction (17 of ~250 pooled issuers as of 2026-08-27, see
    FUNDAMENTAL_FEATURE_COLUMNS) -- every other symbol simply gets no rows here, which
    build_features()'s merge_asof then leaves as real NaN, not zero or a guess.
    """
    ratio_rows = db.execute(
        select(RatioValue.issuer_id, RatioValue.period_end, RatioDefinition.key, RatioValue.value)
        .join(RatioDefinition, RatioDefinition.id == RatioValue.ratio_definition_id)
        .where(RatioDefinition.key.in_(FUNDAMENTAL_FEATURE_COLUMNS))
    ).all()
    empty = pd.DataFrame(columns=["symbol", "known_as_of", *FUNDAMENTAL_FEATURE_COLUMNS])
    if not ratio_rows:
        return empty

    ratios = pd.DataFrame(ratio_rows, columns=["issuer_id", "period_end", "key", "value"])
    ratios["period_end"] = pd.to_datetime(ratios["period_end"])
    ratios["value"] = ratios["value"].astype(float)

    announcement_rows = db.execute(
        select(Announcement.issuer_id, Announcement.published_at)
        .where(Announcement.category == "results", Announcement.issuer_id.is_not(None))
    ).all()
    if not announcement_rows:
        return empty
    announcements = pd.DataFrame(announcement_rows, columns=["issuer_id", "published_at"])
    announcements["published_at"] = pd.to_datetime(announcements["published_at"]).dt.tz_localize(None)

    anchors = []
    for issuer_id, period_end in ratios[["issuer_id", "period_end"]].drop_duplicates().itertuples(index=False):
        candidates = announcements.loc[
            (announcements["issuer_id"] == issuer_id) & (announcements["published_at"] >= period_end),
            "published_at",
        ]
        if candidates.empty:
            continue
        anchors.append({"issuer_id": issuer_id, "period_end": period_end, "known_as_of": candidates.min()})
    if not anchors:
        return empty

    wide = (
        ratios.merge(pd.DataFrame(anchors), on=["issuer_id", "period_end"], how="inner")
        .pivot_table(index=["issuer_id", "known_as_of"], columns="key", values="value", aggfunc="last")
        .reset_index()
    )
    for col in FUNDAMENTAL_FEATURE_COLUMNS:
        if col not in wide.columns:
            wide[col] = np.nan

    issuer_symbols = pd.DataFrame(
        db.execute(select(Security.issuer_id, Security.symbol).where(Security.is_active.is_(True))).all(),
        columns=["issuer_id", "symbol"],
    )
    wide = wide.merge(issuer_symbols, on="issuer_id", how="inner")
    return wide[["symbol", "known_as_of", *FUNDAMENTAL_FEATURE_COLUMNS]].sort_values(["symbol", "known_as_of"])


# Only these two sectors have a real index on file (see load_sector_index_panel) -- every
# other sector gets real NaN for sector_* features, not a guess.
_SECTOR_INDEX_CODE = {"Fertilizer": "FERTIX", "Cement": "CEMENTIX"}


def load_market_index_panel(db: Session) -> pd.DataFrame:
    """Real KSE-100 index returns, one row per trading date -- applies to every symbol on a
    given date (unlike fundamentals, an index close is same-day public information, so no
    point-in-time anchoring/lag is needed here, just a plain date join).

    Real coverage constraint, not a bug: KSE-100 only has ~500 trading days on file (2024-07
    to 2026-07) versus decades of price history for many pooled symbols -- market_return_5d/
    21d are real NaN for every symbol on every date outside that window. build_features()'s
    merge leaves that as-is; the model pipeline's imputer handles it the same way it already
    handles fundamentals' narrower issuer coverage.
    """
    rows = db.execute(
        select(IndexOHLCV.trade_date, IndexOHLCV.close)
        .join(MarketIndex, MarketIndex.id == IndexOHLCV.market_index_id)
        .where(MarketIndex.code == "KSE100")
        .order_by(IndexOHLCV.trade_date)
    ).all()
    if not rows:
        return pd.DataFrame(columns=["date", "market_return_5d", "market_return_21d"])
    df = pd.DataFrame(rows, columns=["date", "close"])
    df["date"] = pd.to_datetime(df["date"])
    df["close"] = df["close"].astype(float)
    df["market_return_5d"] = df["close"].pct_change(5)
    df["market_return_21d"] = df["close"].pct_change(21)
    return df[["date", "market_return_5d", "market_return_21d"]]


def load_sector_index_panel(db: Session) -> pd.DataFrame:
    """Real FERTIX/CEMENTIX sector-index returns, one row per (sector, trading date) --
    the only two sector indices this DB has on file. Deliberately distinct from
    TECHNICAL_FEATURE_COLUMNS' relative_21d/relative_63d, which compare against the
    synthetic pooled-universe benchmark (see synthetic_benchmark()) -- an equal-weighted
    average of the WHOLE ~250-symbol pool across every sector, not this stock's own sector.
    A fertilizer name's true relative strength against its actual peers can look very
    different from its relative strength against banks/textiles/insurance/etc mixed together.

    Same same-day-public-information reasoning as load_market_index_panel: no point-in-time
    lag needed, just a date+sector join. Same real coverage constraint too (~500 trading
    days), plus a second one: only issuers in Sector "Fertilizer" or "Cement" (33 of ~250
    pooled issuers) get anything here at all -- every other symbol/sector gets real NaN.
    """
    rows = db.execute(
        select(IndexOHLCV.trade_date, MarketIndex.code, IndexOHLCV.close)
        .join(MarketIndex, MarketIndex.id == IndexOHLCV.market_index_id)
        .where(MarketIndex.code.in_(_SECTOR_INDEX_CODE.values()))
        .order_by(MarketIndex.code, IndexOHLCV.trade_date)
    ).all()
    if not rows:
        return pd.DataFrame(columns=["date", "sector", "sector_return_5d", "sector_return_21d"])
    df = pd.DataFrame(rows, columns=["date", "code", "close"])
    df["date"] = pd.to_datetime(df["date"])
    df["close"] = df["close"].astype(float)
    code_to_sector = {v: k for k, v in _SECTOR_INDEX_CODE.items()}
    df["sector"] = df["code"].map(code_to_sector)
    groups = []
    for _, g in df.groupby("code", sort=False):
        g = g.sort_values("date").copy()
        g["sector_return_5d"] = g["close"].pct_change(5)
        g["sector_return_21d"] = g["close"].pct_change(21)
        groups.append(g)
    out = pd.concat(groups, ignore_index=True)
    return out[["date", "sector", "sector_return_5d", "sector_return_21d"]]


def load_symbol_sector_map(db: Session) -> pd.DataFrame:
    """symbol -> sector name, restricted to the two sectors with a real index on file (see
    _SECTOR_INDEX_CODE) -- every symbol outside Fertilizer/Cement is simply absent, not
    mapped to a placeholder."""
    rows = db.execute(
        select(Security.symbol, Sector.name)
        .join(Issuer, Issuer.id == Security.issuer_id)
        .join(Sector, Sector.id == Issuer.sector_id)
        .where(Security.is_active.is_(True), Sector.name.in_(_SECTOR_INDEX_CODE.keys()))
    ).all()
    return pd.DataFrame(rows, columns=["symbol", "sector"])


def load_sector_context_panel(db: Session) -> pd.DataFrame:
    """load_sector_index_panel() expanded from (sector, date) to (symbol, date) via
    load_symbol_sector_map(), so build_features() can merge it the same simple way it merges
    market_index -- a plain (symbol, date) join, no point-in-time lag needed."""
    sector_index = load_sector_index_panel(db)
    symbol_sector = load_symbol_sector_map(db)
    empty = pd.DataFrame(columns=["symbol", "date", "sector_return_5d", "sector_return_21d"])
    if sector_index.empty or symbol_sector.empty:
        return empty
    merged = symbol_sector.merge(sector_index, on="sector", how="inner")
    return merged[["symbol", "date", "sector_return_5d", "sector_return_21d"]]


def synthetic_benchmark(panel: pd.DataFrame, base_level: float = 100_000.0) -> pd.Series:
    """Equal-weighted average daily return across the full loaded universe, as a substitute for
    a licensed market-wide index. NOT the real KSE-100 -- see module docstring.
    """
    daily = panel.pivot_table(index="date", columns="symbol", values="close", aggfunc="last")
    returns = daily.sort_index().pct_change()
    market_return = returns.mean(axis=1, skipna=True).fillna(0.0)
    benchmark = base_level * (1 + market_return).cumprod()
    return benchmark.rename("benchmark_close")


def attach_benchmark(panel: pd.DataFrame) -> pd.DataFrame:
    benchmark = synthetic_benchmark(panel)
    return panel.merge(benchmark, left_on="date", right_index=True, how="left")


def run_for_all_issuers(db: Session, as_of: date | None = None) -> dict[str, dict]:
    as_of = as_of or date.today()
    config = ModelConfig()
    settings = get_settings()

    panel = load_price_panel(db, config=config, as_of=as_of)
    if panel.empty:
        logger.warning("No securities met the history/staleness thresholds; nothing to score.")
        return {}
    logger.info("Loaded price panel: %d symbols, %d rows", panel["symbol"].nunique(), len(panel))

    priced = attach_benchmark(panel)
    fundamentals = load_fundamental_panel(db)
    logger.info(
        "Loaded fundamental panel: %d symbols with point-in-time-anchored ratios",
        fundamentals["symbol"].nunique() if not fundamentals.empty else 0,
    )

    model = SignalModel(config, fundamentals=fundamentals)
    try:
        model.fit(priced)
    except ValueError as exc:
        logger.warning("Walk-forward validation could not fit a pooled model: %s", exc)
        return {}

    rankings = model.rank(priced)

    # model.fit()/model.rank() are pure CPU-bound pandas/sklearn work on the already-loaded
    # DataFrames above -- no DB call happens for however long walk-forward training + ranking
    # takes (minutes, for the full pool). The session's connection sits open but idle that
    # whole time, and pool_pre_ping only re-validates a connection AT CHECKOUT -- it never
    # gets a chance to catch this one going stale mid-session. Real, reproduced failure
    # (2026-08-27): the very next query after this gap died with "could not receive data from
    # server" -- confirming the connection is genuinely dead, not just slow. db.close() alone
    # isn't enough here: it tries to gracefully ROLLBACK over that same dead socket first and
    # raises when that also fails. invalidate() is SQLAlchemy's purpose-built answer for
    # exactly this ("a Session that may be transmitting connection errors at the DBAPI
    # level," per its own docs) -- discards the connection outright instead of trying to use
    # it, so the next db.execute() below gets a genuinely fresh, pre_ping-validated one.
    db.invalidate()

    symbols = [r["symbol"] for r in rankings]
    symbol_to_issuer = dict(
        db.execute(select(Security.symbol, Security.issuer_id).where(Security.symbol.in_(symbols))).all()
    )

    results: dict[str, dict] = {}
    for record in rankings:
        issuer_id = symbol_to_issuer.get(record["symbol"])
        if issuer_id is None:
            continue
        row_as_of = date.fromisoformat(record["as_of"])

        existing = db.execute(
            select(MlSignalScore).where(MlSignalScore.issuer_id == issuer_id, MlSignalScore.as_of_date == row_as_of)
        ).scalar_one_or_none()
        if existing is not None:
            db.delete(existing)
            db.flush()

        score = MlSignalScore(
            issuer_id=issuer_id,
            as_of_date=row_as_of,
            model_version=MODEL_VERSION,
            signal=record["signal"],
            outperformance_probability=record["outperformance_probability"],
            validation_observations=record["validation_observations"],
            validation_accuracy=record["validation_accuracy"],
            validation_buy_precision=record["validation_buy_precision"],
            validation_sell_precision=record["validation_sell_precision"],
            validation_brier_score=record["validation_brier_score"],
            validation_roc_auc=record["validation_roc_auc"],
            validation_positive_rate=record["validation_positive_rate"],
            beats_naive_baseline=record["beats_naive_baseline"],
            validation_p_value=record["validation_p_value"],
            significant_at_10pct=record["significant_at_10pct"],
            is_public=settings.ml_signals_enabled,
        )
        db.add(score)
        results[record["symbol"]] = {
            "signal": score.signal,
            "outperformance_probability": score.outperformance_probability,
            "validation_accuracy": score.validation_accuracy,
            "validation_buy_precision": score.validation_buy_precision,
            "validation_positive_rate": score.validation_positive_rate,
            "beats_naive_baseline": score.beats_naive_baseline,
            "validation_p_value": score.validation_p_value,
            "significant_at_10pct": score.significant_at_10pct,
            "validation_observations": score.validation_observations,
            "is_public": score.is_public,
        }

    db.commit()
    return results


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    _settings = get_settings()
    if _settings.ml_signals_enabled:
        logger.warning(
            "ML_SIGNALS_ENABLED is true -- rows computed now will be marked is_public=True. "
            "Only proceed if the compliance review documented in docs/rights_matrix.template.md "
            "has actually happened."
        )

    with SessionLocal() as session:
        outcome = run_for_all_issuers(session)
        if not outcome:
            print("No signals produced -- see warnings above.")
        for symbol, result in outcome.items():
            print(f"{symbol}: {result}")
