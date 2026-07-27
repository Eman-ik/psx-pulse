"""CAPM cost-of-equity inputs, sourced from the user-provided Fatima Fertilizer.pdf analysis
(section 7.1: "CAPM Inputs and Cost of Equity"), which itself cites Trading Economics
(risk-free rate), SCSTrade (beta) and Damodaran (country risk premium).

Market-wide assumptions (risk-free rate, base/country equity risk premium) apply to every
issuer via issuer_id=None; only beta is issuer-specific and only known for FATIMA from this
source. Other issuers fall back to a neutral beta=1.0 default in app/etl/valuation_engine.py,
clearly labeled as an assumption rather than presented as a researched figure.
"""

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CapmAssumption, Issuer

logger = logging.getLogger(__name__)

AS_OF_DATE = date(2026, 7, 7)
SOURCE_NOTE = (
    "Risk-free rate: Trading Economics, Pakistan 10-year government bond yield, Jul 2026. "
    "Base equity risk premium: practical local-market premium for a mature, profitable listed "
    "stock. Country risk premium: Aswath Damodaran, Country Default Spreads and Risk Premiums, "
    "Jan 2026, Pakistan. Source: user-provided Fatima Fertilizer.pdf analysis, section 7.1."
)

MARKET_WIDE = {
    "risk_free_rate_pct": 11.69,
    "base_equity_risk_premium_pct": 6.00,
    "country_risk_premium_pct": 13.94,
}

# issuer_name -> beta (only where a specific source gives one; else the engine assumes 1.0)
ISSUER_BETA = {
    "Fatima Fertilizer Company Limited": 1.02,
}


def seed_capm_assumptions(db: Session) -> dict[str, int]:
    inserted = skipped = 0

    # Market-wide row (issuer_id=None) — the default beta=1.0 case.
    existing = db.execute(
        select(CapmAssumption).where(CapmAssumption.issuer_id.is_(None), CapmAssumption.as_of_date == AS_OF_DATE)
    ).scalar_one_or_none()
    if existing is None:
        db.add(CapmAssumption(issuer_id=None, as_of_date=AS_OF_DATE, beta=1.0, source_note=SOURCE_NOTE, **MARKET_WIDE))
        inserted += 1
    else:
        skipped += 1

    for issuer_name, beta in ISSUER_BETA.items():
        issuer = db.execute(select(Issuer).where(Issuer.name == issuer_name)).scalar_one_or_none()
        if issuer is None:
            continue
        existing = db.execute(
            select(CapmAssumption).where(CapmAssumption.issuer_id == issuer.id, CapmAssumption.as_of_date == AS_OF_DATE)
        ).scalar_one_or_none()
        if existing is not None:
            skipped += 1
            continue
        db.add(CapmAssumption(issuer_id=issuer.id, as_of_date=AS_OF_DATE, beta=beta, source_note=SOURCE_NOTE, **MARKET_WIDE))
        inserted += 1

    db.commit()
    return {"inserted": inserted, "skipped": skipped}


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        print(seed_capm_assumptions(session))
