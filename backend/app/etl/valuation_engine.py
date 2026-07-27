"""CAPM cost-of-equity + a simple Gordon Growth fair-value range.

Deliberately not a full DCF: that needs FCF projections we don't have reliably for any
issuer yet. A Gordon Growth dividend model is the honest alternative *when dividend data
actually exists* — for issuers without a clean, sustained dividend series (or where the
growth rate implied would exceed the cost of equity, which breaks the model), this
produces nothing rather than a fabricated number. See app/ingestion/capm_seed.py for the
assumption sources.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CapmAssumption, FinancialFact, RatioDefinition, RatioValue

logger = logging.getLogger(__name__)

FORMULA_VERSION = 1


def _get_assumption(db: Session, issuer_id: int) -> CapmAssumption | None:
    issuer_specific = db.execute(
        select(CapmAssumption)
        .where(CapmAssumption.issuer_id == issuer_id)
        .order_by(CapmAssumption.as_of_date.desc())
    ).scalars().first()
    if issuer_specific is not None:
        return issuer_specific
    return db.execute(
        select(CapmAssumption).where(CapmAssumption.issuer_id.is_(None)).order_by(CapmAssumption.as_of_date.desc())
    ).scalars().first()


def _get_or_create_definition(db: Session, key: str, name: str, description: str) -> RatioDefinition:
    existing = db.execute(
        select(RatioDefinition).where(RatioDefinition.key == key, RatioDefinition.formula_version == FORMULA_VERSION)
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    definition = RatioDefinition(
        key=key, formula_version=FORMULA_VERSION, name=name, category="valuation",
        formula_description=description, unit="percent",
    )
    db.add(definition)
    db.flush()
    return definition


def compute_cost_of_equity(db: Session, issuer_id: int) -> dict | None:
    assumption = _get_assumption(db, issuer_id)
    if assumption is None:
        return None

    risk_free = float(assumption.risk_free_rate_pct)
    beta = float(assumption.beta)
    base_erp = float(assumption.base_equity_risk_premium_pct)
    country_erp = float(assumption.country_risk_premium_pct)

    ke_base = risk_free + beta * base_erp
    ke_strict = risk_free + beta * country_erp

    base_def = _get_or_create_definition(
        db, "cost_of_equity_base", "Cost of Equity (base CAPM)",
        "risk_free_rate + beta * base_equity_risk_premium",
    )
    strict_def = _get_or_create_definition(
        db, "cost_of_equity_strict", "Cost of Equity (strict CAPM, country risk premium)",
        "risk_free_rate + beta * country_risk_premium",
    )

    for definition, value in [(base_def, ke_base), (strict_def, ke_strict)]:
        existing = db.execute(
            select(RatioValue).where(
                RatioValue.ratio_definition_id == definition.id,
                RatioValue.issuer_id == issuer_id,
                RatioValue.period_end == assumption.as_of_date,
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(
                RatioValue(
                    ratio_definition_id=definition.id, issuer_id=issuer_id, period_end=assumption.as_of_date,
                    period_type="snapshot", scope="consolidated", value=value, input_fact_ids=[],
                )
            )
    db.commit()
    return {"as_of_date": assumption.as_of_date, "beta": beta, "ke_base": ke_base, "ke_strict": ke_strict}


def compute_fair_value_range(db: Session, issuer_id: int, live_price: float | None = None) -> dict | None:
    """Gordon Growth: Fair Value = D1 / (Ke - g). Only produced when the inputs actually
    support it — a real dividend series, a sane (non-negative, sub-Ke) growth rate, AND
    (when a live price is available) a result that isn't wildly divergent from the market
    price. A single year-over-year dividend move is a fragile basis for a "growth rate" —
    e.g. FATIMA's dividend fell Rs 7.00 to Rs 6.00 for payout-discipline reasons the source
    report explains, not a business decline, and naively compounding that -14% "growth"
    produces a fair value of ~Rs 16 against an actual price of ~Rs 150. That's not a real
    89% overvaluation signal, it's the model breaking on thin data — so it's suppressed
    rather than shown, consistent with "no signal is better than a fabricated one."
    """
    cost_of_equity = compute_cost_of_equity(db, issuer_id)
    if cost_of_equity is None:
        return None

    dividends = db.execute(
        select(FinancialFact)
        .where(
            FinancialFact.issuer_id == issuer_id,
            FinancialFact.line_item == "dividend_per_share",
            FinancialFact.superseded_by_id.is_(None),
        )
        .order_by(FinancialFact.period_end)
    ).scalars().all()

    if len(dividends) < 2:
        return None

    d0, d1_fact = float(dividends[-2].value), dividends[-1]
    d1 = float(d1_fact.value)
    if d0 <= 0 or d1 <= 0:
        return None

    growth_rate = (d1 - d0) / d0
    ke_base, ke_strict = cost_of_equity["ke_base"] / 100, cost_of_equity["ke_strict"] / 100

    if growth_rate >= ke_base or growth_rate < -0.5:
        logger.info(
            "Skipping fair value for issuer %s: growth rate %.2f%% is not sane for Gordon Growth (Ke_base=%.2f%%)",
            issuer_id, growth_rate * 100, cost_of_equity["ke_base"],
        )
        return None

    next_dividend = d1 * (1 + growth_rate)
    fair_value_conservative = next_dividend / (ke_strict - growth_rate) if growth_rate < ke_strict else None
    fair_value_optimistic = next_dividend / (ke_base - growth_rate)

    if live_price is not None and live_price > 0:
        deviation = abs(fair_value_optimistic - live_price) / live_price
        if deviation > 0.6:
            logger.info(
                "Suppressing fair value for issuer %s: Gordon Growth output %.2f is %.0f%% away "
                "from live price %.2f — not a meaningful signal from a single-year dividend move.",
                issuer_id, fair_value_optimistic, deviation * 100, live_price,
            )
            return None

    definition = _get_or_create_definition(
        db, "fair_value_gordon_growth", "Fair Value (Gordon Growth, base case)",
        "next_dividend_per_share / (cost_of_equity_base - dividend_growth_rate)",
    )
    definition.unit = "PKR"
    existing = db.execute(
        select(RatioValue).where(
            RatioValue.ratio_definition_id == definition.id,
            RatioValue.issuer_id == issuer_id,
            RatioValue.period_end == d1_fact.period_end,
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            RatioValue(
                ratio_definition_id=definition.id, issuer_id=issuer_id, period_end=d1_fact.period_end,
                period_type="annual", scope="consolidated", value=fair_value_optimistic,
                input_fact_ids=[dividends[-2].id, d1_fact.id],
            )
        )
        db.commit()

    return {
        "growth_rate_pct": growth_rate * 100,
        "fair_value_optimistic": fair_value_optimistic,
        "fair_value_conservative": fair_value_conservative,
        "ke_base_pct": cost_of_equity["ke_base"],
        "ke_strict_pct": cost_of_equity["ke_strict"],
    }


if __name__ == "__main__":
    from app.db.session import SessionLocal
    from app.db.models import Issuer
    from app.ingestion.psx_live import fetch_live_snapshot

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        # Only issuers with a tracked Security — parent/holding stubs (Fauji Foundation,
        # Dawood Hercules) get no cost-of-equity/valuation, since we don't track their prices.
        issuers = session.execute(select(Issuer).where(Issuer.securities.any())).scalars().all()
        for issuer in issuers:
            symbol = issuer.securities[0].symbol
            snapshot = fetch_live_snapshot(symbol)
            live_price = snapshot["price"] if snapshot else None

            ke = compute_cost_of_equity(session, issuer.id)
            fv = compute_fair_value_range(session, issuer.id, live_price=live_price)
            print(f"{issuer.name} (price={live_price}): cost_of_equity={ke}, fair_value={fv}")
