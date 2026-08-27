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
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Announcement, MlSignalScore, PriceOHLCV, RatioDefinition, RatioValue, Security

logger = logging.getLogger(__name__)

MODEL_VERSION = 1

# How stale a security's most recent trade can be (in calendar days) before it's excluded from
# a scoring run -- catches delisted/suspended/merged names (e.g. FFBL post FFC-FFBL merger)
# that would otherwise get a signal computed from data that's no longer representative.
STALENESS_TOLERANCE_DAYS = 21

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
# Passed to the model's .fit()/.predict_proba() -- the sklearn pipeline's SimpleImputer handles
# NaN here. NOT the same list used to decide whether a row is eligible for training/scoring at
# all (see TECHNICAL_FEATURE_COLUMNS' use in walk_forward_predictions/SignalModel.rank): requiring
# fundamentals there would silently shrink the pooled universe down to the ~17 issuers with real
# fundamental coverage, defeating the reason this model is pooled broadly in the first place.
FEATURE_COLUMNS = TECHNICAL_FEATURE_COLUMNS + FUNDAMENTAL_FEATURE_COLUMNS


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
) -> pd.DataFrame:
    """Build backward-looking features and forward excess-return labels.

    fundamentals, if given, must have columns ["symbol", "known_as_of", *FUNDAMENTAL_FEATURE_
    COLUMNS] -- see load_fundamental_panel(). Joined via pd.merge_asof (direction="backward",
    grouped by symbol): each price bar gets the most recent fundamental row whose known_as_of
    is on or before that bar's own date, never a later one -- the actual point-in-time
    guarantee, not just a date-shaped column. A symbol with no fundamental coverage, or no
    fundamentals param at all, gets real NaN in these columns (see FEATURE_COLUMNS' module-
    level comment for how the rest of the pipeline handles that).
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

    if fundamentals is not None and not fundamentals.empty:
        result = pd.merge_asof(
            result.sort_values("date"),
            fundamentals.sort_values("known_as_of"),
            left_on="date", right_on="known_as_of", by="symbol", direction="backward",
        ).sort_values(["symbol", "date"]).reset_index(drop=True)
        for col in FUNDAMENTAL_FEATURE_COLUMNS:
            if col not in result.columns:
                result[col] = np.nan
    else:
        for col in FUNDAMENTAL_FEATURE_COLUMNS:
            result[col] = np.nan
    return result


def _base_model() -> Pipeline:
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
        model = _base_model().fit(train[FEATURE_COLUMNS], train["target"].astype(int))
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
    return ValidationMetrics(
        observations=len(y), accuracy=float(accuracy_score(y, predicted)),
        buy_precision=float(buy_precision), sell_precision=float(sell_precision),
        brier_score=float(brier_score_loss(y, p)), roc_auc=auc,
        positive_rate=positive_rate, beats_naive_baseline=float(buy_precision) > positive_rate,
    )


class SignalModel:
    def __init__(self, config: ModelConfig = ModelConfig(), fundamentals: pd.DataFrame | None = None):
        self.config = config
        self.fundamentals = fundamentals
        self.model: CalibratedClassifierCV | None = None
        self.metrics: ValidationMetrics | None = None

    def fit(self, prices: pd.DataFrame) -> "SignalModel":
        features = build_features(prices, self.config, self.fundamentals)
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
        fitted = _base_model().fit(train[FEATURE_COLUMNS], train["target"].astype(int))
        self.model = CalibratedClassifierCV(FrozenEstimator(fitted), method="sigmoid")
        self.model.fit(calibration[FEATURE_COLUMNS], calibration["target"].astype(int))
        return self

    def rank(self, prices: pd.DataFrame) -> list[dict]:
        if self.model is None or self.metrics is None:
            raise RuntimeError("Model must be fitted before ranking")
        features = build_features(prices, self.config, self.fundamentals)
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
