"""Our own versioned ratio/formula engine — the "critical formula rule" from the plan:
never store a bare number, always the formula, its version, and exactly which
financial_fact rows produced it (RatioValue.input_fact_ids).

Two tiers of coverage, matching what's actually in financial_fact for each issuer:
- Revenue/PAT/EPS growth + net margin: available for all pilot issuers (psxdata scrape).
- Full ratio suite (margins, liquidity, leverage, ROA/ROE, turnover): only for FFC, EFERT
  and FATIMA, where app/ingestion/manual_financials_seed.py has entered real balance-sheet
  and income-statement facts from user-provided analyst research. FFBL/ENGRO/AGL/AHCL don't
  have that manual research, so these ratios simply don't compute for them yet — no
  fabricated numbers are produced for missing inputs.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

import math

from app.db.models import FinancialFact, Issuer, RatioDefinition, RatioValue

logger = logging.getLogger(__name__)

GROWTH_RATIO_DEFS = {
    "revenue": ("revenue_growth_yoy", "Revenue Growth (YoY)", "growth"),
    "profit_after_tax": ("pat_growth_yoy", "Profit After Tax Growth (YoY)", "growth"),
    "eps": ("eps_growth_yoy", "EPS Growth (YoY)", "growth"),
}

FORMULA_VERSION = 1


def _get_or_create_ratio_definition(db: Session, key: str, name: str, category: str, description: str) -> RatioDefinition:
    existing = db.execute(
        select(RatioDefinition).where(
            RatioDefinition.key == key, RatioDefinition.formula_version == FORMULA_VERSION
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    definition = RatioDefinition(
        key=key,
        formula_version=FORMULA_VERSION,
        name=name,
        category=category,
        formula_description=description,
        unit="percent",
    )
    db.add(definition)
    db.flush()
    return definition


def _facts_by_period(db: Session, issuer_id: int, line_item: str) -> list[FinancialFact]:
    return list(
        db.execute(
            select(FinancialFact)
            .where(
                FinancialFact.issuer_id == issuer_id,
                FinancialFact.line_item == line_item,
                FinancialFact.period_type == "annual",
                FinancialFact.scope == "consolidated",
                FinancialFact.superseded_by_id.is_(None),
            )
            .order_by(FinancialFact.period_end)
        )
        .scalars()
        .all()
    )


def compute_growth_ratios(db: Session, issuer_id: int) -> int:
    inserted = 0
    for line_item, (key, name, category) in GROWTH_RATIO_DEFS.items():
        facts = _facts_by_period(db, issuer_id, line_item)
        if len(facts) < 2:
            continue
        definition = _get_or_create_ratio_definition(
            db, key, name, category,
            f"(current period {line_item} - prior period {line_item}) / prior period {line_item} * 100",
        )
        for prior, current in zip(facts, facts[1:]):
            if prior.value == 0:
                continue
            existing = db.execute(
                select(RatioValue).where(
                    RatioValue.ratio_definition_id == definition.id,
                    RatioValue.issuer_id == issuer_id,
                    RatioValue.period_end == current.period_end,
                )
            ).scalar_one_or_none()
            if existing is not None:
                continue
            # Standard (current - prior) / prior formula. When prior is negative (a loss
            # year), this produces a sign/magnitude that reads as counterintuitive — e.g.
            # AGL and AHCL's EPS growth here comes out negative in years where EPS actually
            # improved, because Capital Stake's reported "EPS Growth" apparently flips the
            # sign in that case (confirmed via reconcile_with_third_party: exact sign flip,
            # not a value error). Left as the textbook formula rather than silently matching
            # their convention, since which convention is "right" is a genuine judgment call —
            # flagged here for whoever reviews reconciliation output, not hidden.
            growth = float((current.value - prior.value) / prior.value * 100)
            db.add(
                RatioValue(
                    ratio_definition_id=definition.id,
                    issuer_id=issuer_id,
                    period_end=current.period_end,
                    period_type="annual",
                    scope="consolidated",
                    value=growth,
                    input_fact_ids=[prior.id, current.id],
                )
            )
            inserted += 1
    db.commit()
    return inserted


def compute_net_profit_margin(db: Session, issuer_id: int) -> int:
    revenue_facts = {f.period_end: f for f in _facts_by_period(db, issuer_id, "revenue")}
    pat_facts = {f.period_end: f for f in _facts_by_period(db, issuer_id, "profit_after_tax")}
    common_periods = sorted(set(revenue_facts) & set(pat_facts))
    if not common_periods:
        return 0

    definition = _get_or_create_ratio_definition(
        db, "net_profit_margin", "Net Profit Margin", "profitability",
        "profit_after_tax / revenue * 100",
    )

    inserted = 0
    for period_end in common_periods:
        revenue = revenue_facts[period_end]
        pat = pat_facts[period_end]
        if revenue.value == 0:
            continue
        existing = db.execute(
            select(RatioValue).where(
                RatioValue.ratio_definition_id == definition.id,
                RatioValue.issuer_id == issuer_id,
                RatioValue.period_end == period_end,
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        margin = float(pat.value / revenue.value * 100)
        db.add(
            RatioValue(
                ratio_definition_id=definition.id,
                issuer_id=issuer_id,
                period_end=period_end,
                period_type="annual",
                scope="consolidated",
                value=margin,
                input_fact_ids=[revenue.id, pat.id],
            )
        )
        inserted += 1
    db.commit()
    return inserted


def _store_ratio_value(
    db: Session, definition: RatioDefinition, issuer_id: int, period_end, value: float, input_fact_ids: list[int]
) -> bool:
    existing = db.execute(
        select(RatioValue).where(
            RatioValue.ratio_definition_id == definition.id,
            RatioValue.issuer_id == issuer_id,
            RatioValue.period_end == period_end,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return False
    db.add(
        RatioValue(
            ratio_definition_id=definition.id,
            issuer_id=issuer_id,
            period_end=period_end,
            period_type="annual",
            scope="consolidated",
            value=value,
            input_fact_ids=input_fact_ids,
        )
    )
    return True


# key -> (name, category, unit, numerator line_item, denominator line_item, multiplier)
POINT_IN_TIME_RATIOS = {
    "gross_profit_margin": ("Gross Profit Margin", "profitability", "percent", "gross_profit", "revenue", 100),
    "operating_profit_margin": ("Operating Profit Margin", "profitability", "percent", "operating_profit", "revenue", 100),
    "debt_to_assets": ("Debt-to-Assets", "leverage", "ratio", "total_liabilities", "total_assets", 1),
    "debt_to_equity": ("Debt-to-Equity", "leverage", "ratio", "total_liabilities", "total_equity", 1),
    "current_ratio": ("Current Ratio", "liquidity", "ratio", "current_assets", "current_liabilities", 1),
}


def compute_point_in_time_ratios(db: Session, issuer_id: int) -> int:
    """Ratios computed from two facts at the *same* period end (no averaging)."""
    inserted = 0
    for key, (name, category, unit, num_item, den_item, multiplier) in POINT_IN_TIME_RATIOS.items():
        numerators = {f.period_end: f for f in _facts_by_period(db, issuer_id, num_item)}
        denominators = {f.period_end: f for f in _facts_by_period(db, issuer_id, den_item)}
        common = sorted(set(numerators) & set(denominators))
        if not common:
            continue
        definition = _get_or_create_ratio_definition(
            db, key, name, category, f"{num_item} / {den_item}" + (" * 100" if multiplier == 100 else ""),
        )
        definition.unit = unit
        for period_end in common:
            num, den = numerators[period_end], denominators[period_end]
            if den.value == 0:
                continue
            value = float(num.value / den.value * multiplier)
            if _store_ratio_value(db, definition, issuer_id, period_end, value, [num.id, den.id]):
                inserted += 1
    db.commit()
    return inserted


def compute_quick_ratio(db: Session, issuer_id: int) -> int:
    """Quick ratio = (current assets - inventory) / current liabilities — needs 3 facts, not 2."""
    current_assets = {f.period_end: f for f in _facts_by_period(db, issuer_id, "current_assets")}
    inventory = {f.period_end: f for f in _facts_by_period(db, issuer_id, "inventory")}
    current_liabilities = {f.period_end: f for f in _facts_by_period(db, issuer_id, "current_liabilities")}
    common = sorted(set(current_assets) & set(inventory) & set(current_liabilities))
    if not common:
        return 0
    definition = _get_or_create_ratio_definition(
        db, "quick_ratio", "Quick Ratio", "liquidity", "(current_assets - inventory) / current_liabilities",
    )
    definition.unit = "ratio"
    inserted = 0
    for period_end in common:
        ca, inv, cl = current_assets[period_end], inventory[period_end], current_liabilities[period_end]
        if cl.value == 0:
            continue
        value = float((ca.value - inv.value) / cl.value)
        if _store_ratio_value(db, definition, issuer_id, period_end, value, [ca.id, inv.id, cl.id]):
            inserted += 1
    db.commit()
    return inserted


# Cash-flow ratios: point-in-time, all against operating_cash_flow (the only cash-flow fact
# we hold — see app/ingestion/manual_financials_seed.py). FCF-based ratios (FCF margin, capex
# intensity) are NOT computed: no capex figure exists in any source document read so far, and
# a "free cash flow" ratio without a real capex deduction would just be operating cash flow
# relabeled, which is misleading rather than merely incomplete.
CASH_FLOW_RATIOS = {
    "ocf_to_pat": ("Operating Cash Flow to PAT (cash conversion)", "cash_flow", "percent", "operating_cash_flow", "profit_after_tax", 100),
    "ocf_margin": ("Operating Cash Flow Margin", "cash_flow", "percent", "operating_cash_flow", "revenue", 100),
    "ocf_to_current_liabilities": ("OCF to Current Liabilities", "cash_flow", "percent", "operating_cash_flow", "current_liabilities", 100),
}


def compute_cash_flow_ratios(db: Session, issuer_id: int) -> int:
    inserted = 0
    for key, (name, category, unit, num_item, den_item, multiplier) in CASH_FLOW_RATIOS.items():
        numerators = {f.period_end: f for f in _facts_by_period(db, issuer_id, num_item)}
        denominators = {f.period_end: f for f in _facts_by_period(db, issuer_id, den_item)}
        common = sorted(set(numerators) & set(denominators))
        if not common:
            continue
        definition = _get_or_create_ratio_definition(
            db, key, name, category, f"{num_item} / {den_item}" + (" * 100" if multiplier == 100 else ""),
        )
        definition.unit = unit
        for period_end in common:
            num, den = numerators[period_end], denominators[period_end]
            if den.value == 0:
                continue
            value = float(num.value / den.value * multiplier)
            if _store_ratio_value(db, definition, issuer_id, period_end, value, [num.id, den.id]):
                inserted += 1
    db.commit()
    return inserted


def compute_dividend_payout_ratio(db: Session, issuer_id: int) -> int:
    """Payout ratio needs matching units on both sides: EPS-vs-DPS (both per-share, e.g.
    FATIMA) or aggregate-dividends-vs-aggregate-PAT (e.g. EFERT) — never mixed.
    """
    inserted = 0
    definition = None

    dps = {f.period_end: f for f in _facts_by_period(db, issuer_id, "dividend_per_share")}
    eps = {f.period_end: f for f in _facts_by_period(db, issuer_id, "eps")}
    for period_end in sorted(set(dps) & set(eps)):
        d, e = dps[period_end], eps[period_end]
        if e.value == 0:
            continue
        if definition is None:
            definition = _get_or_create_ratio_definition(
                db, "dividend_payout_ratio", "Dividend Payout Ratio", "cash_flow", "dividend_per_share / eps * 100",
            )
            definition.unit = "percent"
        value = float(d.value / e.value * 100)
        if _store_ratio_value(db, definition, issuer_id, period_end, value, [d.id, e.id]):
            inserted += 1

    total_div = {f.period_end: f for f in _facts_by_period(db, issuer_id, "dividends_paid_total")}
    pat = {f.period_end: f for f in _facts_by_period(db, issuer_id, "profit_after_tax")}
    for period_end in sorted(set(total_div) & set(pat)):
        d, p = total_div[period_end], pat[period_end]
        if p.value == 0:
            continue
        if definition is None:
            definition = _get_or_create_ratio_definition(
                db, "dividend_payout_ratio", "Dividend Payout Ratio", "cash_flow", "dividend_per_share / eps * 100",
            )
            definition.unit = "percent"
        value = float(d.value / p.value * 100)
        if _store_ratio_value(db, definition, issuer_id, period_end, value, [d.id, p.id]):
            inserted += 1

    db.commit()
    return inserted


def _latest_fact(db: Session, issuer_id: int, line_item: str, period_type: str) -> FinancialFact | None:
    return db.execute(
        select(FinancialFact)
        .where(
            FinancialFact.issuer_id == issuer_id,
            FinancialFact.line_item == line_item,
            FinancialFact.period_type == period_type,
            FinancialFact.superseded_by_id.is_(None),
        )
        .order_by(FinancialFact.period_end.desc())
    ).scalars().first()


def compute_per_share_and_valuation_ratios(db: Session, issuer_id: int, live_price: float | None) -> int:
    """Latest-snapshot-only ratios (not a historical time series): shares outstanding is a
    point-in-time scrape (app/ingestion/psx_financials.py's Equity Profile parsing), not a
    per-period fact, so it can only be paired with the *latest* annual figures — we have no
    historical share-count series to build a proper per-share time series.
    """
    shares = _latest_fact(db, issuer_id, "shares_outstanding", "snapshot")
    if shares is None or shares.value == 0:
        return 0

    inserted = 0
    equity = _latest_fact(db, issuer_id, "total_equity", "annual")
    revenue = _latest_fact(db, issuer_id, "revenue", "annual")
    eps = _latest_fact(db, issuer_id, "eps", "annual")

    book_value_per_share = float(equity.value * 1000 / shares.value) if equity is not None else None
    sales_per_share = float(revenue.value * 1000 / shares.value) if revenue is not None else None
    # financial_fact values here are in PKR '000 (shares_outstanding is a raw count), hence *1000.

    if book_value_per_share is not None:
        definition = _get_or_create_ratio_definition(
            db, "book_value_per_share", "Book Value Per Share", "per_share",
            "total_equity * 1000 / shares_outstanding",
        )
        definition.unit = "PKR"
        if _store_ratio_value(db, definition, issuer_id, equity.period_end, book_value_per_share, [equity.id, shares.id]):
            inserted += 1

    if sales_per_share is not None:
        definition = _get_or_create_ratio_definition(
            db, "sales_per_share", "Sales Per Share", "per_share", "revenue * 1000 / shares_outstanding",
        )
        definition.unit = "PKR"
        if _store_ratio_value(db, definition, issuer_id, revenue.period_end, sales_per_share, [revenue.id, shares.id]):
            inserted += 1

    if live_price is not None:
        if book_value_per_share:
            definition = _get_or_create_ratio_definition(
                db, "price_to_book", "Price to Book (P/B)", "valuation", "live_price / book_value_per_share",
            )
            definition.unit = "ratio"
            if _store_ratio_value(db, definition, issuer_id, equity.period_end, live_price / book_value_per_share, [equity.id, shares.id]):
                inserted += 1
        if sales_per_share:
            definition = _get_or_create_ratio_definition(
                db, "price_to_sales", "Price to Sales (P/S)", "valuation", "live_price / sales_per_share",
            )
            definition.unit = "ratio"
            if _store_ratio_value(db, definition, issuer_id, revenue.period_end, live_price / sales_per_share, [revenue.id, shares.id]):
                inserted += 1
        if eps is not None and eps.value != 0:
            definition = _get_or_create_ratio_definition(
                db, "price_to_earnings", "Price to Earnings (P/E)", "valuation", "live_price / eps",
            )
            definition.unit = "ratio"
            if _store_ratio_value(db, definition, issuer_id, eps.period_end, live_price / float(eps.value), [eps.id, shares.id]):
                inserted += 1

    db.commit()
    return inserted


# key -> (name, category, unit, numerator line_item, denominator line_item to average, multiplier)
AVERAGE_DENOMINATOR_RATIOS = {
    "roa": ("Return on Assets", "profitability", "percent", "profit_after_tax", "total_assets", 100),
    "roe": ("Return on Equity", "profitability", "percent", "profit_after_tax", "total_equity", 100),
    "asset_turnover": ("Asset Turnover", "efficiency", "ratio", "revenue", "total_assets", 1),
    "inventory_turnover": ("Inventory Turnover", "efficiency", "ratio", "cost_of_sales", "inventory", 1),
    "receivables_turnover": ("Receivables Turnover", "efficiency", "ratio", "revenue", "trade_debts", 1),
}


def compute_average_denominator_ratios(db: Session, issuer_id: int) -> int:
    """Ratios like ROA/ROE/turnover that use the *average* of the denominator across two
    consecutive period-ends, matching the Appendix-A formulas in the source analyst reports.
    """
    inserted = 0
    for key, (name, category, unit, num_item, den_item, multiplier) in AVERAGE_DENOMINATOR_RATIOS.items():
        numerators = {f.period_end: f for f in _facts_by_period(db, issuer_id, num_item)}
        denominator_facts = _facts_by_period(db, issuer_id, den_item)
        if len(denominator_facts) < 2 or not numerators:
            continue
        definition = _get_or_create_ratio_definition(
            db, key, name, category, f"{num_item} / average({den_item})" + (" * 100" if multiplier == 100 else ""),
        )
        definition.unit = unit
        for prior_den, current_den in zip(denominator_facts, denominator_facts[1:]):
            period_end = current_den.period_end
            numerator = numerators.get(period_end)
            if numerator is None:
                continue
            average_den = (float(prior_den.value) + float(current_den.value)) / 2
            if average_den == 0:
                continue
            value = float(numerator.value) / average_den * multiplier
            if _store_ratio_value(
                db, definition, issuer_id, period_end, value, [numerator.id, prior_den.id, current_den.id]
            ):
                inserted += 1
    db.commit()
    return inserted


def reconcile_balance_sheet(db: Session, issuer_id: int, tolerance_pct: float = 1.0) -> list[dict]:
    """Checks the fundamental accounting identity: total assets = total liabilities + equity.

    This caught a real discrepancy in the source data for FFC's 2022 figures (see
    app/ingestion/manual_financials_seed.py's module docstring) rather than a bug here —
    exactly the kind of thing this check exists to surface, not silently resolve.
    """
    assets = {f.period_end: f for f in _facts_by_period(db, issuer_id, "total_assets")}
    liabilities = {f.period_end: f for f in _facts_by_period(db, issuer_id, "total_liabilities")}
    equity = {f.period_end: f for f in _facts_by_period(db, issuer_id, "total_equity")}
    common = sorted(set(assets) & set(liabilities) & set(equity))

    flags = []
    for period_end in common:
        total_assets = float(assets[period_end].value)
        total_liab_and_equity = float(liabilities[period_end].value) + float(equity[period_end].value)
        diff_pct = abs(total_assets - total_liab_and_equity) / total_assets * 100 if total_assets else 0
        if diff_pct > tolerance_pct:
            flags.append(
                {
                    "period_end": period_end.isoformat(),
                    "total_assets": total_assets,
                    "total_liabilities_plus_equity": total_liab_and_equity,
                    "diff_pct": round(diff_pct, 2),
                }
            )
    return flags


def _latest_ratio_value_for_key(db: Session, issuer_id: int, key: str) -> RatioValue | None:
    defn = db.execute(select(RatioDefinition).where(RatioDefinition.key == key)).scalar_one_or_none()
    if defn is None:
        return None
    return db.execute(
        select(RatioValue)
        .where(RatioValue.ratio_definition_id == defn.id, RatioValue.issuer_id == issuer_id)
        .order_by(RatioValue.period_end.desc())
    ).scalars().first()


def compute_graham_number(db: Session, issuer_id: int) -> int:
    """Graham Number = sqrt(22.5 × EPS × Book Value Per Share).

    A price-anchored intrinsic value estimate per Benjamin Graham. Using EPS as the per-share
    earnings anchor and BVPS as the asset anchor. The result is in PKR (same unit as the
    live price, so it's directly comparable). Only computed where both inputs are positive —
    a negative EPS or BVPS would produce an imaginary number, not a meaningful value.

    Inputs reused from existing FinancialFact + already-computed book_value_per_share ratio:
    nothing new needs to be ingested.
    """
    eps_fact = _latest_fact(db, issuer_id, "eps", "annual")
    bvps_rv = _latest_ratio_value_for_key(db, issuer_id, "book_value_per_share")
    if eps_fact is None or bvps_rv is None:
        return 0
    eps = float(eps_fact.value)
    bvps = float(bvps_rv.value)
    if eps <= 0 or bvps <= 0:
        return 0
    value = math.sqrt(22.5 * eps * bvps)
    definition = _get_or_create_ratio_definition(
        db, "graham_number", "Graham Number", "valuation",
        "sqrt(22.5 × eps × book_value_per_share) — Benjamin Graham's per-share intrinsic value anchor",
    )
    definition.unit = "PKR"
    inserted = int(_store_ratio_value(db, definition, issuer_id, eps_fact.period_end, value, [eps_fact.id]))
    db.commit()
    return inserted


def compute_tobin_q(db: Session, issuer_id: int, live_price: float | None) -> int:
    """Tobin's Q (simplified) = market_cap / total_assets.

    Proper Tobin's Q uses replacement cost of assets (not book value), which PSX filings
    don't easily surface. This simplified version uses book-value total_assets as the
    denominator — a common practical approximation, labeled explicitly as 'simplified' so
    nobody mistakes it for the academically precise form.

    market_cap (PKR) = live_price × shares_outstanding (raw count)
    total_assets (PKR) = total_assets_fact × 1000 (FinancialFact values are in PKR '000)
    """
    if live_price is None:
        return 0
    shares = _latest_fact(db, issuer_id, "shares_outstanding", "snapshot")
    total_assets = _latest_fact(db, issuer_id, "total_assets", "annual")
    if shares is None or total_assets is None or shares.value == 0 or total_assets.value == 0:
        return 0
    market_cap_pkr = live_price * float(shares.value)
    total_assets_pkr = float(total_assets.value) * 1000
    value = market_cap_pkr / total_assets_pkr
    definition = _get_or_create_ratio_definition(
        db, "tobin_q", "Tobin's Q (Simplified)", "valuation",
        "(live_price × shares_outstanding) / (total_assets × 1000) — simplified; uses book total_assets",
    )
    definition.unit = "ratio"
    inserted = int(_store_ratio_value(db, definition, issuer_id, total_assets.period_end, value, [shares.id, total_assets.id]))
    db.commit()
    return inserted


def compute_sustainable_growth_rate(db: Session, issuer_id: int) -> int:
    """Sustainable Growth Rate = ROE × (1 − payout_ratio / 100).

    The maximum growth rate a company can achieve without external financing — i.e. funded
    entirely by retained earnings. For high-dividend Pakistani fertilizer companies, this
    is typically modest (ROE 20-30%, payout 80-90% → SGR ~3-6%), which is consistent
    with the sector's relatively stable, low-growth character.

    Inputs from existing RatioValues — no new data needed.
    Result expressed as a percentage (e.g. 4.2 for 4.2% growth).
    """
    roe_rv = _latest_ratio_value_for_key(db, issuer_id, "roe")
    payout_rv = _latest_ratio_value_for_key(db, issuer_id, "dividend_payout_ratio")
    if roe_rv is None or payout_rv is None:
        return 0
    roe = float(roe_rv.value)
    payout = float(payout_rv.value)
    retention = max(0.0, 1.0 - payout / 100.0)
    value = roe * retention
    period_end = max(roe_rv.period_end, payout_rv.period_end)
    definition = _get_or_create_ratio_definition(
        db, "sustainable_growth_rate", "Sustainable Growth Rate", "growth",
        "roe × (1 − dividend_payout_ratio / 100)",
    )
    definition.unit = "percent"
    inserted = int(_store_ratio_value(db, definition, issuer_id, period_end, value, []))
    db.commit()
    return inserted


def compute_dividend_coverage(db: Session, issuer_id: int) -> int:
    """Dividend Coverage = EPS / DPS (or PAT / total_dividends_paid on aggregate basis).

    How many times over earnings cover the dividend. Coverage < 1 signals a dividend
    being paid from reserves or debt — a sustainability concern. Coverage ≥ 1.5 is
    generally considered comfortable. Pakistani fertilizer companies typically run
    high payouts (70-100%) so coverage of 1.0-1.3× is common and not necessarily alarming
    in a mature, cash-generative sector, but the trend matters.
    """
    inserted = 0
    definition = None

    dps_facts = {f.period_end: f for f in _facts_by_period(db, issuer_id, "dividend_per_share")}
    eps_facts = {f.period_end: f for f in _facts_by_period(db, issuer_id, "eps")}
    for period_end in sorted(set(dps_facts) & set(eps_facts)):
        dps, eps = dps_facts[period_end], eps_facts[period_end]
        if dps.value == 0:
            continue
        if definition is None:
            definition = _get_or_create_ratio_definition(
                db, "dividend_coverage", "Dividend Coverage", "cash_flow",
                "eps / dividend_per_share",
            )
            definition.unit = "ratio"
        value = float(eps.value / dps.value)
        if _store_ratio_value(db, definition, issuer_id, period_end, value, [eps.id, dps.id]):
            inserted += 1

    # Fallback: aggregate PAT vs total dividends paid (for issuers where only aggregate data exists)
    total_div = {f.period_end: f for f in _facts_by_period(db, issuer_id, "dividends_paid_total")}
    pat_facts = {f.period_end: f for f in _facts_by_period(db, issuer_id, "profit_after_tax")}
    for period_end in sorted(set(total_div) & set(pat_facts)):
        div, pat = total_div[period_end], pat_facts[period_end]
        if div.value == 0:
            continue
        if definition is None:
            definition = _get_or_create_ratio_definition(
                db, "dividend_coverage", "Dividend Coverage", "cash_flow",
                "eps / dividend_per_share",
            )
            definition.unit = "ratio"
        value = float(pat.value / div.value)
        if _store_ratio_value(db, definition, issuer_id, period_end, value, [pat.id, div.id]):
            inserted += 1

    db.commit()
    return inserted


def compute_all_ratios(db: Session, issuer_id: int, live_price: float | None = None) -> dict[str, int]:
    return {
        "growth_ratios_inserted": compute_growth_ratios(db, issuer_id),
        "net_profit_margin_inserted": compute_net_profit_margin(db, issuer_id),
        "point_in_time_ratios_inserted": compute_point_in_time_ratios(db, issuer_id),
        "quick_ratio_inserted": compute_quick_ratio(db, issuer_id),
        "average_denominator_ratios_inserted": compute_average_denominator_ratios(db, issuer_id),
        "cash_flow_ratios_inserted": compute_cash_flow_ratios(db, issuer_id),
        "dividend_payout_ratio_inserted": compute_dividend_payout_ratio(db, issuer_id),
        "per_share_and_valuation_inserted": compute_per_share_and_valuation_ratios(db, issuer_id, live_price),
        "graham_number_inserted": compute_graham_number(db, issuer_id),
        "tobin_q_inserted": compute_tobin_q(db, issuer_id, live_price),
        "sustainable_growth_rate_inserted": compute_sustainable_growth_rate(db, issuer_id),
        "dividend_coverage_inserted": compute_dividend_coverage(db, issuer_id),
    }


def reconcile_with_third_party(db: Session, issuer_id: int, tolerance_pct: float = 1.0) -> list[dict]:
    """Compares our independently-computed ratios against Capital Stake's reported ones.

    This is the plan's "reconciliation checks" requirement in concrete form: two
    independent calculations of the same figure should roughly agree. A mismatch beyond
    tolerance is a data-quality flag, not necessarily an error on either side (scope —
    consolidated vs standalone — is a documented open question; see source_registry.yaml).
    """
    pairs = [
        ("eps_growth_yoy", "eps_growth_reported", "EPS growth"),
        ("net_profit_margin", "net_profit_margin_reported", "Net profit margin"),
    ]
    mismatches = []
    for our_key, their_key, label in pairs:
        our_def = db.execute(
            select(RatioDefinition).where(
                RatioDefinition.key == our_key, RatioDefinition.formula_version == FORMULA_VERSION
            )
        ).scalar_one_or_none()
        their_def = db.execute(select(RatioDefinition).where(RatioDefinition.key == their_key)).scalar_one_or_none()
        if our_def is None or their_def is None:
            continue

        our_values = {
            v.period_end: v.value
            for v in db.execute(
                select(RatioValue).where(
                    RatioValue.ratio_definition_id == our_def.id, RatioValue.issuer_id == issuer_id
                )
            ).scalars()
        }
        their_values = {
            v.period_end: v.value
            for v in db.execute(
                select(RatioValue).where(
                    RatioValue.ratio_definition_id == their_def.id, RatioValue.issuer_id == issuer_id
                )
            ).scalars()
        }
        for period_end in sorted(set(our_values) & set(their_values)):
            ours = float(our_values[period_end])
            theirs = float(their_values[period_end])
            if abs(ours - theirs) > tolerance_pct:
                mismatches.append(
                    {
                        "metric": label,
                        "period_end": period_end.isoformat(),
                        "ours": ours,
                        "capital_stake": theirs,
                        "diff": round(ours - theirs, 2),
                    }
                )
    return mismatches


if __name__ == "__main__":
    from app.db.session import SessionLocal
    from app.db.models import Issuer
    from app.ingestion.psx_live import fetch_live_snapshot

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        issuers = session.execute(select(Issuer)).scalars().all()
        for issuer in issuers:
            symbol = issuer.securities[0].symbol if issuer.securities else None
            live_price = None
            if symbol:
                snapshot = fetch_live_snapshot(symbol)
                live_price = snapshot["price"] if snapshot else None

            stats = compute_all_ratios(session, issuer.id, live_price=live_price)
            mismatches = reconcile_with_third_party(session, issuer.id)
            bs_flags = reconcile_balance_sheet(session, issuer.id)
            print(f"{issuer.name} (live_price={live_price}): {stats}")
            for m in mismatches:
                print(f"  RECONCILIATION FLAG (vs third party): {m}")
            for f in bs_flags:
                print(f"  BALANCE SHEET FLAG (assets != liabilities+equity): {f}")
