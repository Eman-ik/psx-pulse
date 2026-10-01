"""Operational/production KPIs (the plan's "Operations and production" IA section),
manually entered from the same user-provided analyst research as manual_financials_seed.py.

Values are physical volumes (thousand tonnes / million tonnes) or percentages, tied to a
specific product line where the source distinguishes one (urea vs DAP vs NP vs CAN) —
deliberately not fabricated for companies with no such research (FFBL/ENGRO/AGL/AHCL get
nothing here, same asymmetry as the financial facts).
"""

import hashlib
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Issuer, OperationalMetric, SourceDocument

logger = logging.getLogger(__name__)

# issuer_name -> source label -> list of (metric_key, product, year, value, unit)
FFC_METRICS = {
    "source_label": "RAP Workings updated.xlsx (FFC P&L) — ACCA RAP workbook from FFC annual reports",
    "rows": [
        ("capacity_utilization_pct", None, 2020, 121, "percent"),
        ("capacity_utilization_pct", None, 2021, 122, "percent"),
        ("capacity_utilization_pct", None, 2022, 117, "percent"),
        ("capacity_utilization_pct", None, 2023, 123, "percent"),
        ("production_volume", "urea", 2020, 2487, "KT"),
        ("production_volume", "urea", 2021, 2507, "KT"),
        ("production_volume", "urea", 2022, 2404, "KT"),
        ("production_volume", "urea", 2023, 2521, "KT"),
        ("sales_volume", "urea", 2020, 2512, "KT"),
        ("sales_volume", "urea", 2021, 2477, "KT"),
        ("sales_volume", "urea", 2022, 2423, "KT"),
        ("sales_volume", "urea", 2023, 2505, "KT"),
        ("sales_volume", "dap_imported", 2020, 233, "KT"),
        ("sales_volume", "dap_imported", 2021, 205, "KT"),
        ("sales_volume", "dap_imported", 2022, 70, "KT"),
        ("sales_volume", "dap_imported", 2023, 105, "KT"),
    ],
}

EFERT_METRICS = {
    "source_label": "EFERT.docx — user-provided EFERT analysis",
    "rows": [
        ("production_volume", "urea", 2023, 2313, "KT"),
        ("production_volume", "urea", 2024, 2147, "KT"),
        ("sales_volume", "urea", 2023, 2327, "KT"),
        ("sales_volume", "urea", 2024, 2026, "KT"),
        ("sales_volume", "urea", 2025, 2314, "KT"),
        ("market_share_pct", "urea", 2023, 35, "percent"),
        ("market_share_pct", "urea", 2024, 31, "percent"),
        ("market_share_pct", "urea", 2025, 34, "percent"),
    ],
}

FATIMA_METRICS = {
    "source_label": "Fatima Fertilizer.pdf — user-provided analysis citing Annual Reports 2024/2025 and PACRA",
    "rows": [
        ("production_volume", "fertilizer_total", 2024, 2795, "KT"),
        ("production_volume", "fertilizer_total", 2025, 2856, "KT"),
        ("sales_volume", "fertilizer_total", 2023, 2866, "KT"),
        ("sales_volume", "fertilizer_total", 2024, 2523, "KT"),
        ("sales_volume", "fertilizer_total", 2025, 2883, "KT"),
        ("market_share_pct", "fertilizer_production", 2024, 27.7, "percent"),
        ("market_share_pct", "fertilizer_offtake", 2024, 27.4, "percent"),
        ("nameplate_capacity", "fertilizer_total", 2025, 2570, "KT"),
        ("product_mix_pct", "np", 2025, 39, "percent"),
        ("product_mix_pct", "urea", 2025, 32, "percent"),
        ("product_mix_pct", "can", 2025, 24, "percent"),
    ],
}


def _get_or_create_source_document(db: Session, issuer: Issuer, label: str) -> SourceDocument:
    content_hash = hashlib.sha256(f"operational-kpi-manual-entry::{issuer.name}::{label}".encode()).hexdigest()
    existing = db.execute(select(SourceDocument).where(SourceDocument.content_hash == content_hash)).scalar_one_or_none()
    if existing is not None:
        return existing
    document = SourceDocument(
        issuer_id=issuer.id,
        local_path=label,
        content_hash=content_hash,
        document_type="operational_kpi_manual_entry",
        source_tier="primary",
    )
    db.add(document)
    db.flush()
    return document


def seed_issuer_operational_metrics(db: Session, issuer_name: str, data: dict) -> dict[str, int]:
    issuer = db.execute(select(Issuer).where(Issuer.name == issuer_name)).scalar_one_or_none()
    if issuer is None:
        return {"inserted": 0, "skipped": 0}

    source_document = _get_or_create_source_document(db, issuer, data["source_label"])
    inserted = skipped = 0
    for metric_key, product, year, value, unit in data["rows"]:
        period_start, period_end = date(year, 1, 1), date(year, 12, 31)
        existing = db.execute(
            select(OperationalMetric).where(
                OperationalMetric.issuer_id == issuer.id,
                OperationalMetric.metric_key == metric_key,
                OperationalMetric.product == product,
                OperationalMetric.period_end == period_end,
            )
        ).scalar_one_or_none()
        if existing is not None:
            skipped += 1
            continue
        db.add(
            OperationalMetric(
                issuer_id=issuer.id,
                metric_key=metric_key,
                product=product,
                period_start=period_start,
                period_end=period_end,
                period_type="annual",
                value=value,
                unit=unit,
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
        for issuer_name, data in [
            ("Fauji Fertilizer Company Limited", FFC_METRICS),
            ("Engro Fertilizers Limited", EFERT_METRICS),
            ("Fatima Fertilizer Company Limited", FATIMA_METRICS),
        ]:
            stats = seed_issuer_operational_metrics(session, issuer_name, data)
            print(f"{issuer_name}: {stats}")
