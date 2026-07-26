"""Sector risk snapshot seeded from real analysis, not sample data.

Source: "Macro-Fiscal Architecture and Capital Market Transmission - Pakistan FY2026-27
Budget" (user-provided institutional research paper on the Finance Bill 2026), dated
June 14, 2026, covering FY26 outturn and FY27 budget/PSX transmission.

This is deliberately a manual, analyst-authored snapshot (evidence class:
analyst_interpretation) per the model's own design (app/db/models/macro.py) — not
computed from a rule, and due for a refresh whenever a materially newer macro/budget
read is available.
"""

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Sector, SectorRiskSnapshot

logger = logging.getLogger(__name__)


def seed_fertilizer_risk_snapshot(db: Session) -> SectorRiskSnapshot:
    sector = db.execute(select(Sector).where(Sector.name == "Fertilizer")).scalar_one_or_none()

    as_of = date(2026, 6, 14)
    existing = db.execute(
        select(SectorRiskSnapshot).where(
            SectorRiskSnapshot.sector_id == (sector.id if sector else None),
            SectorRiskSnapshot.as_of_date == as_of,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    snapshot = SectorRiskSnapshot(
        sector_id=sector.id if sector else None,
        as_of_date=as_of,
        overall_risk="MODERATE",
        geopolitical="MODERATE TENSION",
        economy="STABILIZING",
        imf_program="ACTIVE (EFF)",
        currency_pkr="STABLE",
        key_positives=[
            "Real GDP growth accelerated to 3.70% in FY26 (from 3.18% in FY25), driven by an LSM industrial rebound and agricultural resilience",
            "Current account posted a marginal FY26 surplus (~$72m) and workers' remittances rose 8.2% to $30.3bn, easing PKR pressure",
            "Fiscal consolidation on track: primary surplus at 3.2% of GDP and total fiscal deficit narrowed to 0.7% of GDP (Jul-Mar FY26)",
            "Fertilizer/E&P PSX stance is 'Neutral / Cash Yield': energy circular-debt resolution is unlocking cash flow conversion through the supply chain",
            "FFC specifically flagged as retaining strong pricing power to sustain high ROE despite the sector's tax treatment",
        ],
        key_negatives=[
            "Fertilizer manufacturing was explicitly excluded from the Finance Bill 2026 Super Tax relief — stays at the maximum 10% rate above Rs150m profit, unlike most other sectors",
            "CPI averaged 6.2% in FY26 — moderate, but still a real cost pressure on gas/input pricing for fertilizer producers",
            "Recovery is IMF-EFF-program-dependent; the fiscal space created by consolidation is conditional on continued program compliance",
            "PKR stability is a recent, not structural, trend — remittance-driven and subject to reversal if external financing conditions shift",
        ],
        notes=(
            "Source: user-provided institutional research paper, 'Macro-Fiscal Architecture and "
            "Capital Market Transmission — Pakistan FY2026-27 Budget', dated 2026-06-14, covering "
            "the Finance Bill 2026 and its PSX transmission. Superseded automatically by nothing — "
            "needs a manual refresh when a materially newer macro read is available."
        ),
    )
    db.add(snapshot)
    db.commit()
    return snapshot


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        snapshot = seed_fertilizer_risk_snapshot(session)
        print(f"Seeded sector risk snapshot id={snapshot.id}, as_of={snapshot.as_of_date}")
