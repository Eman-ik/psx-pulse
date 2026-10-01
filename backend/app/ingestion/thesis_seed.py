"""Analyst thesis (bull/base/bear) for FFC, EFERT and FATIMA — built from the real SWOT,
conclusion and scenario-analysis sections in the same user-provided research documents as
manual_financials_seed.py, not synthesized from nothing. Evidence class: analyst_interpretation.

Only these three get a thesis: they're the only issuers with source documents that actually
contain thesis-grade analysis (explicit bull/base/bear for FATIMA; SWOT + conclusions for FFC
and EFERT that this module condenses into the same structure). FFBL/ENGRO/AGL/AHCL get none —
writing one without underlying research would be exactly the fabricated-number problem this
whole project has been trying to avoid.
"""

import hashlib
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Issuer, SourceDocument, Thesis

logger = logging.getLogger(__name__)

THESES = {
    "Fauji Fertilizer Company Limited": {
        "source_label": "RAP-2023.docx (ACCA Research and Analysis Project, Topic 5: FFC 2021-2023 exceptional performance vs Fatima)",
        "as_of_date": date(2024, 1, 1),  # the RAP's own coverage period ends CY2023
        "bull_case": (
            "FFC holds the largest urea market share in Pakistan on the back of a 3,400-dealer, "
            "152-warehouse distribution network built over decades, plus 6 farmer advisory centres "
            "that reinforce brand loyalty. Over 2021-2023 it out-executed Fatima on nearly every "
            "metric: GPM +11% vs Fatima's -15.7%, average ROE 45.5% (2.6x Fatima's), average EPS "
            "2.1x higher, and average ITR/ATR both meaningfully ahead. Debt-to-equity fell 12.3% as "
            "FFC reinvested profits rather than layering on leverage — a genuinely stronger capital "
            "structure than the peer group, not just a stronger income statement."
        ),
        "base_case": (
            "FFC continues to defend its #1 urea share through pricing discipline and distribution "
            "reach, with margins tracking gas and RM cost pass-through rather than structural expansion. "
            "Working capital stays a persistent, manageable drag (average current ratio ~1.01, "
            "declining trend) rather than a solvency issue, funded by GIDC-related payables and "
            "short-term borrowing that FFC has historically serviced on time."
        ),
        "bear_case": (
            "The single biggest risk flagged in the RAP is structural gas supply: Pakistan already "
            "consumes more gas (4,100 MMcf/d) than it produces (3,227 MMcf/d), and a report cited in "
            "the research warns of declining gas resources within the coming decade — a direct threat "
            "to urea feedstock. Water shortage for ammonia cooling is a secondary operational risk. "
            "The global shift toward organic fertilizer (projected ~9.2% CAGR 2024-2030) is a slower-"
            "moving but real long-term demand risk for chemical-based fertilizer producers generally."
        ),
        "key_catalysts": [
            "Backup gas pipeline project connecting SNGPL to FFC's facility",
            "PEF (energy efficiency) project with MARI to conserve gas",
            "Neem-coated urea and other R&D-driven product launches (already generated ~PKR750m incremental revenue in one quarter per the RAP)",
        ],
        "key_risks": [
            "Structural natural gas supply deficit (consumption > production nationally)",
            "Water availability for ammonia/urea production cooling",
            "Working capital / current ratio has trended down for 3 consecutive years",
            "Long-term demand risk from the global organic-fertilizer shift",
        ],
        "author": "ACCA Research and Analysis Project (user-provided), condensed by this platform into bull/base/bear structure",
    },
    "Engro Fertilizers Limited": {
        "source_label": "EFERT.docx (user-provided EFERT financial analysis, 2024-2025)",
        "as_of_date": date(2025, 12, 31),
        "bull_case": (
            "Urea sales and market share recovered strongly in 2025 (to ~2.31 million tonnes and ~34% "
            "share) after the 2024 EnVen plant turnaround temporarily disrupted production — the "
            "turnaround itself was a deliberate long-term reliability investment, not a demand problem. "
            "Gross margin recovered to 35.37% in 2025 alongside the production recovery."
        ),
        "base_case": (
            "EFERT's core urea franchise is intact and recovering, but 2025 net profit still fell "
            "(NPM 16.18% to 12.30%) because higher finance costs and a large drop in other income "
            "outweighed the operating recovery. Reading the two years together: 2024's earnings beat "
            "was tax- and non-operating-income-driven, not purely operational, so normalized "
            "profitability is closer to the 2025 print than the 2024 one."
        ),
        "bear_case": (
            "Phosphate market share nearly halved (19% to 13%) on international price and FX exposure, "
            "a segment EFERT does not control as directly as urea. Leverage rose sharply: debt-to-equity "
            "went from 0.73x (2023) to 1.49x (2024) to 3.45x (2025 per the debt/activity workbook), while "
            "both liquidity ratios stayed below 1.0x throughout — EFERT remains dependent on continuous "
            "cash generation and refinancing to meet short-term obligations, and asset turnover has been "
            "declining as the asset base grew faster than sales."
        ),
        "key_catalysts": [
            "Continued urea demand/offtake recovery into the Kharif/Rabi cycles",
            "Phosphate market share stabilization if international DAP prices ease",
        ],
        "key_risks": [
            "Debt-to-equity nearly tripled in two years (0.73x to 3.45x per company workbook)",
            "Current ratio and quick ratio both persistently below 1.0x",
            "Phosphate segment market share loss to import competition",
            "Declining asset turnover as investment outpaces revenue growth",
        ],
        "author": "User-provided EFERT financial analysis, condensed by this platform into bull/base/bear structure",
    },
    "Fatima Fertilizer Company Limited": {
        "source_label": "Fatima Fertilizer.pdf (user-provided analysis citing Annual Reports 2024/2025 and PACRA), section 7.5",
        "as_of_date": date(2026, 7, 7),
        "bull_case": (
            "Margins stabilize, offtake keeps improving, finance cost declines and the aviation/mining/"
            "real-estate/oil-and-gas diversification proves value-accretive. Under this scenario the "
            "source analysis sees the stock justifying a move toward Rs 190-210, a 'hold or trim "
            "gradually' zone rather than a fresh-buy zone at that point."
        ),
        "base_case": (
            "EPS grows slowly, the dividend stays roughly stable, and fertilizer demand remains "
            "defensive as it structurally is. The source analysis prefers accumulating only on dips "
            "below Rs 170, with Rs 155 as the preferred entry given the CAPM-implied required return."
        ),
        "bear_case": (
            "Gas costs rise, the working-capital cycle stays heavy (inventory days rose from 103 to "
            "124.5, DSO rose from 20.6 to 33.6 days in the source data), finance cost stays elevated, "
            "or policy intervention compresses margins. The recommended response is to avoid fresh "
            "buying and reassess below Rs 145."
        ),
        "key_catalysts": [
            "AA+/A1+ Stable PACRA rating reaffirmed (July 2025) supports the credit/financing story",
            "Diversification into aviation, mining, real estate, oil & gas exploration (optionality if disciplined)",
            "Continued urea/NP/CAN volume recovery (2025 production was the company's highest-ever at 2.856m MT)",
        ],
        "key_risks": [
            "Gas pricing and availability — flagged as the single biggest operating risk",
            "Working capital deterioration: inventory days and DSO both rose materially in 2025",
            "Finance cost rose 56.2% in 2025 even though coverage (9.61x) is still comfortable",
            "Dividend per share declined (Rs 7.00 to Rs 6.00) despite EPS growth — payout discipline shifted toward retention",
        ],
        "author": "User-provided institutional-style Fatima Fertilizer analysis (section 7.5 Scenario View), condensed into this platform's structure",
    },
}


def _get_or_create_source_document(db: Session, issuer: Issuer, label: str) -> SourceDocument:
    content_hash = hashlib.sha256(f"thesis-manual-entry::{issuer.name}::{label}".encode()).hexdigest()
    existing = db.execute(select(SourceDocument).where(SourceDocument.content_hash == content_hash)).scalar_one_or_none()
    if existing is not None:
        return existing
    document = SourceDocument(
        issuer_id=issuer.id, local_path=label, content_hash=content_hash, document_type="thesis_source", source_tier="primary",
    )
    db.add(document)
    db.flush()
    return document


def seed_theses(db: Session) -> dict[str, int]:
    inserted = skipped = 0
    for issuer_name, data in THESES.items():
        issuer = db.execute(select(Issuer).where(Issuer.name == issuer_name)).scalar_one_or_none()
        if issuer is None:
            continue
        existing = db.execute(
            select(Thesis).where(Thesis.issuer_id == issuer.id, Thesis.as_of_date == data["as_of_date"])
        ).scalar_one_or_none()
        if existing is not None:
            skipped += 1
            continue
        source_document = _get_or_create_source_document(db, issuer, data["source_label"])
        db.add(
            Thesis(
                issuer_id=issuer.id,
                as_of_date=data["as_of_date"],
                bull_case=data["bull_case"],
                base_case=data["base_case"],
                bear_case=data["bear_case"],
                key_catalysts=data["key_catalysts"],
                key_risks=data["key_risks"],
                author=data["author"],
                source_document_id=source_document.id,
            )
        )
        inserted += 1
    db.commit()
    return {"inserted": inserted, "skipped": skipped}


if __name__ == "__main__":
    from app.db.session import SessionLocal

    logging.basicConfig(level=logging.INFO)

    with SessionLocal() as session:
        print(seed_theses(session))
