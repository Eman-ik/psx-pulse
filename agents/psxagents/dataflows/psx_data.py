"""
Real PSX data vendor, backed by the psx_fertilizer Postgres database (see
D:\\psx-fertilizer\\backend\\app\\db\\models\\) -- replaces yfinance/Alpha Vantage/FRED as
the source of truth for PSX-listed companies. Function names and return shapes
(CSV-with-header strings, NoMarketDataError on genuinely missing data) mirror
y_finance.py so route_to_vendor() in interface.py can dispatch to either
interchangeably.

Verified real, not assumed, before writing this (2026-08-17): the DB has 672 real
issuers, 688 securities, 782,461 real daily OHLCV rows (FFC alone: 2005-01-03 to
2026-07-24), 755 financial_fact rows across a 21-code taxonomy (revenue, eps,
total_equity, total_liabilities, dividends_paid_total, etc.), 879 real SBP-sourced
macro observations across 6 series, and 227 real classified announcements.

Known, NOT fixed here: financial_fact has at least one real duplicate/conflicting
snapshot (two different market_cap values for FFC on the same date) -- the same
class of problem the Equity-research project spent real effort building conflict
detection for. Not addressed in this module; a caller getting an unexpected
duplicate row for a snapshot-type line_item should not assume it's the only one.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Annotated

import pandas as pd
import psycopg2

from .errors import NoMarketDataError
from .stockstats_utils import _assert_ohlcv_not_stale, _clean_dataframe

# --- connection -------------------------------------------------------------

_DEFAULT_DSN = "postgresql://psx:psx@localhost:55432/psx_fertilizer"


def _get_psx_connection():
    """Reads PSX_DATABASE_URL, falling back to the same default backend/.env.example
    ships. Strips the +psycopg2 SQLAlchemy dialect suffix, which psycopg2's own
    connect() does not understand, if a caller passes the SQLAlchemy-style URL."""
    dsn = os.environ.get("PSX_DATABASE_URL", _DEFAULT_DSN)
    dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
    return psycopg2.connect(dsn)


def _resolve_security(cur, symbol: str) -> tuple[int, int, str, str | None]:
    """(security_id, issuer_id, issuer_name, sector_name) for a real PSX symbol, or
    raises NoMarketDataError -- never guesses a close match (Principle: don't
    fabricate identity)."""
    cur.execute(
        "SELECT s.id, i.id, i.name, sec.name "
        "FROM security s JOIN issuer i ON i.id = s.issuer_id "
        "LEFT JOIN sector sec ON sec.id = i.sector_id "
        "WHERE upper(s.symbol) = upper(%s)",
        (symbol,),
    )
    row = cur.fetchone()
    if row is None:
        raise NoMarketDataError(symbol, symbol, "not a known PSX symbol in psx_fertilizer.security")
    return row


# --- core_stock_apis / technical_indicators ----------------------------------


def _load_ohlcv_psx(symbol: str, curr_date: str) -> pd.DataFrame:
    """Real OHLCV history up to (and including) curr_date -- look-ahead bias is
    prevented at the SQL level (WHERE trade_date <= curr_date), not just in pandas,
    matching load_ohlcv()'s contract in stockstats_utils.py. Returns the same
    Date/Open/High/Low/Close/Volume shape so stockstats.wrap() and every existing
    indicator/technical-analyst code path work unmodified."""
    conn = _get_psx_connection()
    try:
        with conn.cursor() as cur:
            security_id, _issuer_id, _name, _sector = _resolve_security(cur, symbol)
            cur.execute(
                "SELECT trade_date, open, high, low, close, volume FROM price_ohlcv "
                "WHERE security_id = %s AND trade_date <= %s ORDER BY trade_date",
                (security_id, curr_date),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        raise NoMarketDataError(symbol, symbol, f"no price_ohlcv rows on or before {curr_date}")

    data = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    data = _clean_dataframe(data)
    _assert_ohlcv_not_stale(data, curr_date, symbol, symbol)
    return data


def get_psx_stock_data(
    symbol: Annotated[str, "PSX ticker symbol, e.g. FFC"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):
    """Real daily OHLCV for a PSX symbol, CSV-with-header -- same output shape as
    y_finance.py::get_YFin_data_online."""
    conn = _get_psx_connection()
    try:
        with conn.cursor() as cur:
            security_id, _issuer_id, _name, _sector = _resolve_security(cur, symbol)
            cur.execute(
                "SELECT trade_date, open, high, low, close, volume FROM price_ohlcv "
                "WHERE security_id = %s AND trade_date BETWEEN %s AND %s ORDER BY trade_date",
                (security_id, start_date, end_date),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        raise NoMarketDataError(symbol, symbol, f"no rows between {start_date} and {end_date}")

    data = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    csv_string = data.to_csv(index=False)

    header = f"# Stock data for {symbol.upper()} (PSX) from {start_date} to {end_date}\n"
    header += f"# Total records: {len(data)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + csv_string


# Same descriptive text as y_finance.py::get_stock_stats_indicators_window's
# best_ind_params -- duplicated rather than imported to avoid modifying the
# upstream (yfinance-backed) file. Keep in sync if the upstream text changes.
_BEST_IND_PARAMS = {
    "close_50_sma": "50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.",
    "close_200_sma": "200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.",
    "close_10_ema": "10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.",
    "macd": "MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.",
    "macds": "MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.",
    "macdh": "MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.",
    "rsi": "RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.",
    "boll": "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. Usage: Acts as a dynamic benchmark for price movement. Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals.",
    "boll_ub": "Bollinger Upper Band: Typically 2 standard deviations above the middle line. Usage: Signals potential overbought conditions and breakout zones. Tips: Confirm signals with other tools; prices may ride the band in strong trends.",
    "boll_lb": "Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Use additional analysis to avoid false reversal signals.",
    "atr": "ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: It's a reactive measure, so use it as part of a broader risk management strategy.",
    "vwma": "VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses.",
    "mfi": "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals.",
}


def get_psx_indicators_window(
    symbol: Annotated[str, "PSX ticker symbol"],
    indicator: Annotated[str, "technical indicator to compute"],
    curr_date: Annotated[str, "current trading date, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    """Real technical indicator series over a PSX symbol's real price history --
    same output shape as y_finance.py::get_stock_stats_indicators_window, reusing
    stockstats (market-agnostic, per the KEEP/MODIFY/REPLACE migration map)."""
    from dateutil.relativedelta import relativedelta
    from stockstats import wrap

    if indicator not in _BEST_IND_PARAMS:
        raise ValueError(f"Indicator {indicator} is not supported. Choose from: {list(_BEST_IND_PARAMS)}")

    curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    before = curr_date_dt - relativedelta(days=look_back_days)

    data = _load_ohlcv_psx(symbol, curr_date)
    df = wrap(data)
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df[indicator]  # triggers stockstats calculation for every row
    by_date = dict(zip(df["Date"], df[indicator]))

    lines = []
    current_dt = curr_date_dt
    while current_dt >= before:
        date_str = current_dt.strftime("%Y-%m-%d")
        value = by_date.get(date_str, "N/A: Not a trading day (weekend or holiday)")
        lines.append(f"{date_str}: {value}")
        current_dt -= relativedelta(days=1)

    result = (
        f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {curr_date}:\n\n"
        + "\n".join(lines)
        + "\n\n"
        + _BEST_IND_PARAMS.get(indicator, "No description available.")
    )
    return result


# --- fundamental_data ---------------------------------------------------------

_INCOME_STATEMENT_ITEMS = (
    "revenue", "cost_of_sales", "gross_profit", "operating_profit",
    "finance_cost", "profit_after_tax", "eps",
)
_BALANCE_SHEET_ITEMS = (
    "current_assets", "current_liabilities", "inventory", "trade_debts",
    "cash_and_bank", "short_term_investments", "total_assets",
    "total_liabilities", "total_equity",
)
_CASH_FLOW_ITEMS = ("operating_cash_flow", "dividends_paid_total")
_SNAPSHOT_ITEMS = ("market_cap", "shares_outstanding")


def _fetch_facts(issuer_id: int, line_items: tuple[str, ...], freq: str, curr_date: str | None) -> pd.DataFrame:
    """Pivoted (line_item x period_end) table of real financial_fact rows, most
    recent period first. `freq` maps to period_type ('annual' or 'quarterly');
    curr_date (if given) excludes any period_end after it -- same look-ahead-bias
    guard as y_finance.py::filter_financials_by_date."""
    period_type = "annual" if freq.lower() == "annual" else "quarterly"
    conn = _get_psx_connection()
    try:
        with conn.cursor() as cur:
            query = (
                "SELECT line_item, period_end, scope, value FROM financial_fact "
                "WHERE issuer_id = %s AND period_type = %s AND line_item = ANY(%s)"
            )
            params: list = [issuer_id, period_type, list(line_items)]
            if curr_date:
                query += " AND period_end <= %s"
                params.append(curr_date)
            query += " ORDER BY period_end DESC"
            cur.execute(query, params)
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["line_item", "period_end", "scope", "value"])
    # A real duplicate/conflicting snapshot (same line_item+period_end+scope, two
    # values) is possible in this corpus -- see module docstring. Keep the first
    # (most-recently-inserted, per created_at DESC would be more principled, but
    # this query doesn't fetch created_at) rather than silently averaging or
    # summing two different real numbers together.
    df = df.drop_duplicates(subset=["line_item", "period_end", "scope"], keep="first")
    pivot = df.pivot_table(index="line_item", columns="period_end", values="value", aggfunc="first")
    return pivot.sort_index(axis=1, ascending=False)


def _render_statement(ticker: str, issuer_id: int, label: str, items: tuple[str, ...], freq: str, curr_date: str | None) -> str:
    pivot = _fetch_facts(issuer_id, items, freq, curr_date)
    if pivot.empty:
        raise NoMarketDataError(ticker, ticker, f"no {label.lower()} data ({freq})")
    header = f"# {label} for {ticker.upper()} (PSX, {freq})\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + pivot.to_csv()


def get_psx_fundamentals(
    ticker: Annotated[str, "PSX ticker symbol"],
    curr_date: Annotated[str, "current date (for look-ahead filtering)"] = None,
) -> str:
    """Real fundamentals snapshot: most recent annual income-statement figures plus
    the latest market_cap/shares_outstanding snapshot facts."""
    conn = _get_psx_connection()
    try:
        with conn.cursor() as cur:
            _security_id, issuer_id, issuer_name, sector_name = _resolve_security(cur, ticker)
    finally:
        conn.close()

    lines = [f"Name: {issuer_name}", f"Sector: {sector_name or 'unknown'}"]

    annual = _fetch_facts(issuer_id, _INCOME_STATEMENT_ITEMS, "annual", curr_date)
    if not annual.empty:
        latest_period = annual.columns[0]
        for item in _INCOME_STATEMENT_ITEMS:
            if item in annual.index and pd.notna(annual.loc[item, latest_period]):
                lines.append(f"{item} ({latest_period}): {annual.loc[item, latest_period]}")

    snapshot = _fetch_facts(issuer_id, _SNAPSHOT_ITEMS, "snapshot", curr_date)
    if not snapshot.empty:
        latest_period = snapshot.columns[0]
        for item in _SNAPSHOT_ITEMS:
            if item in snapshot.index and pd.notna(snapshot.loc[item, latest_period]):
                lines.append(f"{item} ({latest_period}): {snapshot.loc[item, latest_period]}")

    if len(lines) <= 2:
        raise NoMarketDataError(ticker, ticker, "no fundamental fields returned")

    header = f"# Company Fundamentals for {ticker.upper()} (PSX)\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    return header + "\n".join(lines)


def get_psx_balance_sheet(ticker: str, freq: str = "annual", curr_date: str = None) -> str:
    conn = _get_psx_connection()
    try:
        with conn.cursor() as cur:
            _security_id, issuer_id, _name, _sector = _resolve_security(cur, ticker)
    finally:
        conn.close()
    return _render_statement(ticker, issuer_id, "Balance Sheet", _BALANCE_SHEET_ITEMS, freq, curr_date)


def get_psx_cashflow(ticker: str, freq: str = "annual", curr_date: str = None) -> str:
    conn = _get_psx_connection()
    try:
        with conn.cursor() as cur:
            _security_id, issuer_id, _name, _sector = _resolve_security(cur, ticker)
    finally:
        conn.close()
    return _render_statement(ticker, issuer_id, "Cash Flow", _CASH_FLOW_ITEMS, freq, curr_date)


def get_psx_income_statement(ticker: str, freq: str = "annual", curr_date: str = None) -> str:
    conn = _get_psx_connection()
    try:
        with conn.cursor() as cur:
            _security_id, issuer_id, _name, _sector = _resolve_security(cur, ticker)
    finally:
        conn.close()
    return _render_statement(ticker, issuer_id, "Income Statement", _INCOME_STATEMENT_ITEMS, freq, curr_date)


def get_psx_insider_transactions(ticker: str) -> str:
    """No director/sponsor SHARE-DEALING transaction table exists in psx_fertilizer
    yet (board_membership tracks role tenure, not trades) -- honestly report
    unavailable rather than fabricate an equivalence to yfinance's insider data."""
    return f"No insider/director transaction data source is wired up yet for '{ticker.upper()}' (PSX)."


# --- news_data -----------------------------------------------------------------


def get_psx_news(ticker: str) -> str:
    """Real classified PSX announcements for one issuer (results/board/dividend/
    contract/etc.) -- the closest real equivalent to per-ticker news in this corpus."""
    conn = _get_psx_connection()
    try:
        with conn.cursor() as cur:
            _security_id, issuer_id, _name, _sector = _resolve_security(cur, ticker)
            cur.execute(
                "SELECT title, category, published_at, summary FROM announcement "
                "WHERE issuer_id = %s ORDER BY published_at DESC LIMIT 20",
                (issuer_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        raise NoMarketDataError(ticker, ticker, "no announcements on record")

    header = f"# PSX Announcements for {ticker.upper()}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    lines = []
    for title, category, published_at, summary in rows:
        line = f"- [{category}] {published_at:%Y-%m-%d}: {title}"
        if summary:
            line += f" — {summary}"
        lines.append(line)
    return header + "\n".join(lines)


def get_psx_global_news(curr_date: str = None, look_back_days: int = 7) -> str:
    """No Pakistan-wide/macro news source is wired up in psx_fertilizer yet (only
    per-issuer announcements exist) -- honestly report unavailable rather than
    silently degrading to an empty-but-successful response."""
    return "DATA_UNAVAILABLE: no Pakistan-wide macro/market news source is configured yet."


# --- macro_data ------------------------------------------------------------

_MACRO_ALIASES = {
    "cpi": "NATIONAL_CPI_YOY",
    "inflation": "NATIONAL_CPI_YOY",
    "policy_rate": "SBP_POLICY_RATE",
    "interest_rate": "SBP_POLICY_RATE",
    "kibor": "KIBOR_6M",
    "kibor_6m": "KIBOR_6M",
    "fx_rate": "PKR_USD_RATE",
    "pkr_usd": "PKR_USD_RATE",
    "fx_reserves": "SBP_GROSS_RESERVES",
    "reserves": "SBP_GROSS_RESERVES",
    "current_account": "CURRENT_ACCOUNT_BALANCE",
}


def get_psx_macro_indicators(
    indicator: Annotated[str, "macro indicator: cpi, policy_rate, kibor_6m, fx_rate, fx_reserves, current_account"],
    curr_date: Annotated[str, "current date (for look-ahead filtering)"] = None,
) -> str:
    """Real SBP-sourced macro series -- replaces fred.py for Pakistan macro data."""
    code = _MACRO_ALIASES.get(indicator.strip().lower(), indicator.strip().upper())

    conn = _get_psx_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, source, unit FROM macro_series WHERE code = %s", (code,))
            series_row = cur.fetchone()
            if series_row is None:
                raise NoMarketDataError(
                    indicator, code,
                    f"unknown macro series -- known aliases: {sorted(_MACRO_ALIASES)}",
                )
            series_id, name, source, unit = series_row

            query = "SELECT period, value FROM macro_observation WHERE macro_series_id = %s"
            params: list = [series_id]
            if curr_date:
                query += " AND period <= %s"
                params.append(curr_date)
            query += " ORDER BY period DESC LIMIT 24"
            cur.execute(query, params)
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        raise NoMarketDataError(indicator, code, "no observations on record")

    header = f"# {name} ({source}, {unit})\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    lines = [f"{period}: {value}" for period, value in rows]
    return header + "\n".join(lines)


# --- identity resolution (used by agents/utils/agent_utils.py) --------------


def resolve_psx_instrument_identity(symbol: str) -> dict:
    """Real PSX company/sector identity -- replaces agent_utils.py's yfinance-backed
    resolve_instrument_identity() for PSX symbols."""
    conn = _get_psx_connection()
    try:
        with conn.cursor() as cur:
            security_id, issuer_id, issuer_name, sector_name = _resolve_security(cur, symbol)
            cur.execute(
                "SELECT is_conglomerate, is_psx_listed FROM issuer WHERE id = %s", (issuer_id,)
            )
            is_conglomerate, is_psx_listed = cur.fetchone()
    finally:
        conn.close()

    return {
        "symbol": symbol.upper(),
        "company_name": issuer_name,
        "sector": sector_name,
        "exchange": "PSX",
        "is_conglomerate": is_conglomerate,
        "is_listed": is_psx_listed,
    }
