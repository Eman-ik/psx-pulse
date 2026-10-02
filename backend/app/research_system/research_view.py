"""Seven-domain research view built from stored data only.

Every domain reports a state, the inputs behind it, what would change it, and a confidence
that falls with missing or stale inputs. A domain without enough data is INSUFFICIENT_DATA or
UNAVAILABLE, never a default. There is deliberately no single score: the overall view is
INSUFFICIENT_EVIDENCE unless enough independent, current domains were actually assessed, and
disagreements between domains are listed instead of averaged away.
"""

from datetime import date

STALE_AFTER_MONTHS = 15
MIN_ASSESSED_DOMAINS = 3

# Thresholds for "meaningful change" between the two latest annual periods.
MARGIN_PP = 1.0        # percentage points of net margin or ROE
LIABILITIES_TO_EQUITY = 0.10
CURRENT_RATIO = 0.05

POSITIVE = {"IMPROVING", "POSITIVE", "HIGH"}
NEGATIVE = {"DETERIORATING", "NEGATIVE", "LOW"}
NOT_ASSESSED = {"INSUFFICIENT_DATA", "UNAVAILABLE"}


def _domain(key, label, state, confidence=None, *, stale=False, as_of=None, inputs=None, supports=None,
            could_change=None, reason=None):
    return {
        "key": key, "label": label, "state": state, "confidence": confidence, "stale": stale,
        "as_of": as_of.isoformat() if as_of else None, "inputs": inputs or [], "supports": supports or [],
        "could_change": could_change or [], "reason": reason,
    }


def months_old(period_end: date, today: date) -> int:
    return (today - period_end).days // 30


def _last_two(series: list[tuple[date, float]] | None):
    """The two latest points, only if they are consecutive fiscal years (no missing year between)."""
    s = sorted(series or [])
    if len(s) < 2 or not 340 <= (s[-1][0] - s[-2][0]).days <= 390:
        return None
    return s[-2], s[-1]


def financial_health(ratios: dict[str, list[tuple[date, float]]], today: date) -> dict:
    """Direction of four signals between the two latest annual periods. State needs 3 of 4."""
    rules = [
        ("net_profit_margin", "Net margin", MARGIN_PP, +1, "pp"),
        ("roe", "Return on equity", MARGIN_PP, +1, "pp"),
        ("debt_to_equity", "Total liabilities / equity", LIABILITIES_TO_EQUITY, -1, "x"),
        ("current_ratio", "Current ratio", CURRENT_RATIO, +1, "x"),
    ]
    score, available, inputs, supports = 0, 0, [], []
    pairs = {key: _last_two(ratios.get(key)) for key, *_ in rules}
    # Every signal must describe the same latest year; an older pair would mix eras.
    latest_period = max((pair[1][0] for pair in pairs.values() if pair), default=None)
    for key, label, threshold, good_direction, unit in rules:
        pair = pairs[key]
        if pair is None or pair[1][0] != latest_period:
            continue
        available += 1
        (p0, v0), (p1, v1) = pair
        delta = v1 - v0
        signal = 0 if abs(delta) < threshold else (1 if delta * good_direction > 0 else -1)
        score += signal
        inputs.append({"label": label, "period_end": p1.isoformat(), "value": round(v1, 2), "previous": round(v0, 2)})
        word = {1: "moved the favourable way", -1: "moved the unfavourable way", 0: "was little changed"}[signal]
        supports.append(f"{label} {word}: {v0:.2f} to {v1:.2f} ({p0.year} to {p1.year}).")
    if available < 3:
        return _domain("financial_health", "Financial health", "INSUFFICIENT_DATA",
                       reason=f"Needs three of four ratios over two annual periods; {available} available.")
    stale = months_old(latest_period, today) > STALE_AFTER_MONTHS
    state = "IMPROVING" if score >= 2 else "DETERIORATING" if score <= -2 else "STABLE"
    confidence = round(available / 4 * (0.5 if stale else 1.0), 2)
    if stale:
        supports.insert(0, f"Latest statements are {months_old(latest_period, today)} months old; "
                           "this reflects that period, not today.")
    return _domain("financial_health", "Financial health", state, confidence, stale=stale, as_of=latest_period,
                   inputs=inputs, supports=supports,
                   could_change=["Rule: score of +2 or more is IMPROVING, -2 or less DETERIORATING, otherwise STABLE. "
                                 "A new annual filing re-runs it."])


def earnings_quality(ocf_to_pat: list[tuple[date, float]] | None, today: date) -> dict:
    s = sorted(ocf_to_pat or [])
    if not s:
        return _domain("earnings_quality", "Earnings quality", "INSUFFICIENT_DATA",
                       reason="No operating cash flow figures on file for this company.")
    period, value = s[-1]
    state = "HIGH" if value >= 100 else "MIXED" if value >= 70 else "LOW"
    stale = months_old(period, today) > STALE_AFTER_MONTHS
    confidence = round((1.0 if len(s) >= 2 else 0.5) * (0.5 if stale else 1.0), 2)
    return _domain("earnings_quality", "Earnings quality", state, confidence, stale=stale, as_of=period,
                   inputs=[{"label": "Operating cash flow / profit after tax", "period_end": period.isoformat(),
                            "value": round(value, 1)}],
                   supports=[f"Cash flow was {value:.0f}% of reported profit in {period.year}."],
                   could_change=["Rule: 100% or more is HIGH, 70-100% MIXED, below 70% LOW."])


def technical_condition(signal: dict | None, prices_stale: bool) -> dict:
    if signal is None:
        return _domain("technical_condition", "Technical condition", "UNAVAILABLE",
                       reason="No price on the latest market date for this security.")
    flags = [signal.get("above_20dma"), signal.get("above_50dma"), signal.get("above_200dma")]
    known = [f for f in flags if f is not None]
    if len(known) < 2:
        return _domain("technical_condition", "Technical condition", "UNAVAILABLE",
                       reason=f"Only {signal.get('bars_available')} closes on file; at least two moving averages needed.")
    above = sum(known)
    state = "POSITIVE" if above == len(known) else "NEGATIVE" if above == 0 else "NEUTRAL"
    supports = [f"Close is above {above} of {len(known)} computable moving averages."]
    if signal.get("rsi") is not None:
        supports.append(f"RSI(14) is {signal['rsi']:.1f}.")
    if not signal.get("lookback_complete"):
        supports.append(f"Only {signal['lookback_days']} days of history on file.")
    return _domain("technical_condition", "Technical condition", state, round(len(known) / 3 * (0.5 if prices_stale else 1), 2),
                   stale=prices_stale, inputs=[{"label": "Moving averages computable", "value": len(known)}],
                   supports=supports,
                   could_change=["Rule: above all computable averages is POSITIVE, below all NEGATIVE, otherwise NEUTRAL."])


def not_assessed(key: str, label: str, reason: str) -> dict:
    return _domain(key, label, "INSUFFICIENT_DATA", reason=reason)


def data_confidence(checks: dict[str, tuple[bool, str]]) -> dict:
    passed = sum(ok for ok, _ in checks.values())
    core = checks["prices_current"][0] and checks["statements"][0]
    level = "HIGH" if core and passed >= 4 else "MEDIUM" if passed >= 3 else "LOW"
    return {"level": level, "passed": passed, "total": len(checks),
            "checks": [{"key": k, "passed": ok, "detail": d} for k, (ok, d) in checks.items()],
            "rule": "HIGH: current prices and 3+ annual statements plus at least 4 of 5 checks; MEDIUM: 3 of 5; otherwise LOW."}


def overall_view(domains: list[dict], confidence: dict) -> dict:
    assessed = [d for d in domains if d["state"] not in NOT_ASSESSED and not d["stale"]]
    if confidence["level"] == "LOW" or len(assessed) < MIN_ASSESSED_DOMAINS:
        return {"state": "INSUFFICIENT_EVIDENCE", "assessed_domains": len(assessed), "disagreements": [],
                "reason": f"{len(assessed)} current domains assessed; {MIN_ASSESSED_DOMAINS} needed and data confidence "
                          f"must not be LOW (it is {confidence['level']}). No overall view is given."}
    pos = [d["label"] for d in assessed if d["state"] in POSITIVE]
    neg = [d["label"] for d in assessed if d["state"] in NEGATIVE]
    state = "FAVORABLE" if not neg and len(pos) >= 2 else "UNFAVORABLE" if not pos and len(neg) >= 2 else "MIXED"
    disagreements = [f"{p} is favourable while {n} is not." for p in pos for n in neg]
    return {"state": state, "assessed_domains": len(assessed), "disagreements": disagreements,
            "reason": f"{len(pos)} favourable, {len(neg)} unfavourable among {len(assessed)} assessed domains."}
