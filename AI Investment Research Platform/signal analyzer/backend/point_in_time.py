from __future__ import annotations

import pandas as pd

REQUIRED_EXTERNAL_COLUMNS = {"ticker", "available_at"}


def validate_point_in_time_table(table: pd.DataFrame, value_columns: list[str]) -> pd.DataFrame:
    """Validate fundamentals/events/news/macro observations before as-of joining.

    `available_at` is the first timestamp at which the market could have known
    the value. Period-end dates must never be substituted for this field.
    """
    missing = REQUIRED_EXTERNAL_COLUMNS.union(value_columns) - set(table.columns)
    if missing:
        raise ValueError(f"Missing point-in-time columns: {sorted(missing)}")
    out = table.copy()
    out["available_at"] = pd.to_datetime(out["available_at"], errors="raise", utc=True)
    if out["available_at"].isna().any():
        raise ValueError("available_at cannot be null")
    if out.duplicated(["ticker", "available_at"]).any():
        raise ValueError("Duplicate ticker/available_at records require an explicit revision identifier")
    return out.sort_values(["ticker", "available_at"])


def asof_join_features(panel: pd.DataFrame, external: pd.DataFrame, value_columns: list[str]) -> pd.DataFrame:
    """Attach the most recent publicly available observation without look-ahead."""
    left = panel.copy(); left["date"] = pd.to_datetime(left["date"], utc=True)
    right = validate_point_in_time_table(external, value_columns)
    left = left.rename(columns={"symbol": "ticker"}).sort_values(["date", "ticker"])
    right = right.sort_values(["available_at", "ticker"])
    joined = pd.merge_asof(left, right, left_on="date", right_on="available_at", by="ticker", direction="backward")
    if (joined["available_at"] > joined["date"]).fillna(False).any():
        raise AssertionError("Point-in-time join leaked a future observation")
    return joined.rename(columns={"ticker": "symbol"})
