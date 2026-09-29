"""Evidence-controlled Stage 2 industry intelligence.

The engine deliberately distinguishes an unanswered industry question from a negative
answer.  It aggregates only source-verified company ratios and operational metrics; the
remaining structural questions are returned as explicit evidence gaps until primary or
licensed data is ingested.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import IndustryAssessment, IndustryObservation, Issuer, MacroObservation, MacroSeries, OperationalMetric, RatioDefinition, RatioValue, Sector, Security
from app.universe import TIER_FULL, load_snapshot


STRUCTURE_QUESTIONS = {
    "market_share": ("Market share", "Company filings, sector association statistics"),
    "pricing_power": ("Pricing power", "Realized prices, input costs and margin-through-cycle history"),
    "capacity": ("Installed capacity", "Annual reports and industry capacity statistics"),
    "capacity_utilization": ("Capacity utilization", "Production divided by verified effective capacity"),
    "entry_barriers": ("Entry barriers", "Licensing, capital requirements and project lead times"),
    "imports": ("Import exposure", "PBS customs data and ministry/industry statistics"),
    "exports": ("Export exposure", "Company filings, PBS customs data and sector dispatch data"),
    "regulation": ("Government regulation", "Official ministry and regulator notifications"),
    "substitutes": ("Substitutes", "Product-market and demand-substitution research"),
}

SECTOR_PROFIT_DRIVERS = {
    "FERTILIZER": [
        "feedstock and fuel gas price and availability",
        "urea and DAP offtake, inventory and imports",
        "plant reliability and utilization",
        "government pricing, subsidy and agricultural policy",
    ],
    "CEMENT": [
        "domestic and export dispatch volumes",
        "retention price and competitive discipline",
        "coal, electricity and transport costs",
        "capacity utilization and new capacity additions",
    ],
}

ECONOMY_TRANSMISSION = {
    "FERTILIZER": [
        ("policy_rate", "Policy rate", "financing costs and agricultural credit conditions", "SBP"),
        ("cpi", "Inflation", "farmer purchasing power and administered-price pressure", "PBS"),
        ("usd_pkr", "USD/PKR", "DAP/import parity and imported input costs", "SBP"),
        ("gas_policy", "Gas price and allocation", "feedstock cost, plant economics and production availability", "Petroleum Division / OGRA"),
        ("crop_economics", "Crop economics", "fertilizer affordability and offtake", "PBS / Ministry of National Food Security"),
    ],
    "CEMENT": [
        ("policy_rate", "Policy rate", "construction finance and housing demand", "SBP"),
        ("public_development", "Public development spending", "infrastructure-led cement demand", "Federal and provincial budgets"),
        ("usd_pkr", "USD/PKR", "imported coal, machinery and spare-part costs", "SBP"),
        ("energy_cost", "Coal and electricity costs", "kiln and grinding cash costs", "PBS / NEPRA / international commodity source"),
        ("construction_activity", "Construction activity", "domestic dispatch demand", "PBS / APCMA"),
    ],
}

ECONOMIC_RATIO_KEYS = {
    "roe": "Median return on equity",
    "roic": "Median return on invested capital",
    "gross_profit_margin": "Median gross margin",
    "net_profit_margin": "Median net margin",
    "debt_to_equity": "Median debt to equity",
    "interest_coverage": "Median interest coverage",
}

MACRO_CODE_ALIASES = {
    "policy_rate": ("SBP_POLICY_RATE",),
    "cpi": ("NATIONAL_CPI_YOY",),
    "usd_pkr": ("PKR_USD_RATE",),
    "public_development": ("PSDP_SPENDING",),
    "energy_cost": ("COAL_PRICE", "INDUSTRIAL_ELECTRICITY_TARIFF"),
    "construction_activity": ("CONSTRUCTION_GROWTH",),
    "crop_economics": ("AGRI_GDP_GROWTH", "CROP_PRICE_INDEX"),
}


def _latest_ratio_values(db: Session, issuer_ids: set[int]) -> dict[str, list[float]]:
    if not issuer_ids:
        return {}
    rows = db.execute(
        select(RatioValue, RatioDefinition)
        .join(RatioDefinition, RatioDefinition.id == RatioValue.ratio_definition_id)
        .where(RatioValue.issuer_id.in_(issuer_ids))
        .order_by(RatioValue.issuer_id, RatioDefinition.key, RatioValue.period_end.desc())
    ).all()
    latest: dict[tuple[int, str], float] = {}
    for value, definition in rows:
        latest.setdefault((value.issuer_id, definition.key), float(value.value))
    grouped: dict[str, list[float]] = defaultdict(list)
    for (_, key), value in latest.items():
        if key in ECONOMIC_RATIO_KEYS:
            grouped[key].append(value)
    return grouped


def _operating_coverage(db: Session, issuer_ids: set[int]) -> dict[str, dict]:
    rows = db.execute(
        select(OperationalMetric).where(OperationalMetric.issuer_id.in_(issuer_ids))
    ).scalars().all() if issuer_ids else []
    grouped: dict[str, list[OperationalMetric]] = defaultdict(list)
    for row in rows:
        grouped[row.metric_key].append(row)
    return {
        key: {
            "companies_covered": len({row.issuer_id for row in values}),
            "observations": len(values),
            "latest_period": max(row.period_end for row in values).isoformat(),
            "units": sorted({row.unit for row in values}),
        }
        for key, values in sorted(grouped.items())
    }


def _industry_dataset(db: Session, sector_id: int) -> tuple[dict[str, list[dict]], dict[str, dict]]:
    observations = db.execute(
        select(IndustryObservation)
        .where(IndustryObservation.sector_id == sector_id, IndustryObservation.is_verified.is_(True))
        .order_by(IndustryObservation.metric_key, IndustryObservation.period_end)
    ).scalars().all()
    series: dict[str, list[dict]] = defaultdict(list)
    for row in observations:
        series[row.metric_key].append({
            "period_end": row.period_end.isoformat(), "value": float(row.value),
            "unit": row.unit, "company_issuer_id": row.company_issuer_id,
            "product": row.product, "source_document_id": row.source_document_id,
            "source_page": row.source_page, "confidence": row.confidence,
        })
    assessments = db.execute(
        select(IndustryAssessment)
        .where(IndustryAssessment.sector_id == sector_id)
        .order_by(IndustryAssessment.dimension, IndustryAssessment.as_of_date.desc())
    ).scalars().all()
    latest_assessment: dict[str, dict] = {}
    for row in assessments:
        latest_assessment.setdefault(row.dimension, {
            "rating": row.rating, "assessment": row.assessment,
            "as_of": row.as_of_date.isoformat(), "source_document_id": row.source_document_id,
            "source_page": row.source_page, "confidence": row.confidence,
            "review_date": row.review_date.isoformat() if row.review_date else None,
        })
    return dict(series), latest_assessment


def _latest_total(series: list[dict], company_specific: bool | None = None) -> tuple[str | None, float | None, str | None]:
    rows = [row for row in series if company_specific is None or (row["company_issuer_id"] is not None) == company_specific]
    if not rows:
        return None, None, None
    latest_period = max(row["period_end"] for row in rows)
    latest = [row for row in rows if row["period_end"] == latest_period]
    units = {row["unit"] for row in latest}
    if len(units) != 1:
        return latest_period, None, None
    return latest_period, sum(row["value"] for row in latest), next(iter(units))


def _derived_industry_metrics(series: dict[str, list[dict]]) -> dict:
    derived: dict[str, dict] = {}

    def latest_growth(key: str) -> dict | None:
        rows = [row for row in series.get(key, []) if row["company_issuer_id"] is None]
        if len(rows) < 2:
            return None
        totals: dict[str, float] = defaultdict(float)
        units: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            totals[row["period_end"]] += row["value"]
            units[row["period_end"]].add(row["unit"])
        periods = sorted(totals)
        current, previous = periods[-1], periods[-2]
        if len(units[current]) != 1 or units[current] != units[previous] or totals[previous] == 0:
            return None
        return {
            "value": round(100 * (totals[current] / totals[previous] - 1), 2),
            "unit": "%", "period_end": current, "previous_period": previous,
            "formula": f"latest {key} / previous {key} - 1",
        }

    production_period, production, production_unit = _latest_total(series.get("production", []))
    capacity_period, capacity, capacity_unit = _latest_total(series.get("effective_capacity", []) or series.get("installed_capacity", []))
    if production is not None and capacity and production_unit == capacity_unit:
        derived["capacity_utilization"] = {
            "value": round(100 * production / capacity, 2), "unit": "%",
            "period_end": min(production_period, capacity_period),
            "formula": "verified production / verified capacity × 100",
        }
    demand_growth = latest_growth("domestic_demand") or latest_growth("domestic_dispatches")
    capacity_growth = latest_growth("effective_capacity") or latest_growth("installed_capacity")
    if demand_growth:
        derived["demand_growth"] = demand_growth
    if capacity_growth:
        derived["capacity_growth"] = capacity_growth
    if demand_growth and capacity_growth:
        derived["demand_minus_capacity_growth"] = {
            "value": round(demand_growth["value"] - capacity_growth["value"], 2), "unit": "pp",
            "period_end": min(demand_growth["period_end"], capacity_growth["period_end"]),
            "formula": "demand growth minus capacity growth",
        }
    domestic_period, domestic, domestic_unit = _latest_total(series.get("domestic_dispatches", []) or series.get("domestic_demand", []))
    export_period, exports, export_unit = _latest_total(series.get("export_dispatches", []) or series.get("exports", []))
    if domestic is not None and exports is not None and domestic_unit == export_unit and domestic + exports:
        derived["export_mix"] = {
            "value": round(100 * exports / (domestic + exports), 2), "unit": "%",
            "period_end": min(domestic_period, export_period),
            "formula": "verified exports / (domestic + exports) × 100",
        }
    roic_period, roic, _ = _latest_total(series.get("sector_roic", []), company_specific=False)
    if roic is not None:
        derived["sector_roic"] = {"value": roic, "unit": "%", "period_end": roic_period, "formula": "reported sector ROIC"}
    coc_period, cost_of_capital, _ = _latest_total(series.get("cost_of_capital", []), company_specific=False)
    if roic is not None and cost_of_capital is not None:
        derived["roic_spread"] = {
            "value": round(roic - cost_of_capital, 2), "unit": "pp",
            "period_end": min(roic_period, coc_period), "formula": "sector ROIC minus cost of capital",
        }
    price_growth = latest_growth("realized_price") or latest_growth("retention_price")
    input_growth = latest_growth("input_cost")
    if price_growth:
        derived["realized_price_growth"] = price_growth
    if input_growth:
        derived["input_cost_growth"] = input_growth
    if price_growth and input_growth:
        derived["pricing_power_spread"] = {
            "value": round(price_growth["value"] - input_growth["value"], 2), "unit": "pp",
            "period_end": min(price_growth["period_end"], input_growth["period_end"]),
            "formula": "realized price growth minus input cost growth",
        }

    company_production = [row for row in series.get("production", []) if row["company_issuer_id"] is not None]
    if company_production:
        latest_period = max(row["period_end"] for row in company_production)
        latest_rows = [row for row in company_production if row["period_end"] == latest_period]
        if len({row["unit"] for row in latest_rows}) == 1:
            total = sum(row["value"] for row in latest_rows)
            if total:
                derived["company_market_shares"] = {
                    "period_end": latest_period, "unit": "%",
                    "formula": "company production / covered-company production × 100",
                    "values": [
                        {"issuer_id": row["company_issuer_id"], "value": round(100 * row["value"] / total, 2)}
                        for row in latest_rows
                    ],
                }
    return derived


def _macro_context(db: Session, sector: str) -> dict:
    channels = []
    for key, label, effect, required_source in ECONOMY_TRANSMISSION.get(sector, []):
        aliases = MACRO_CODE_ALIASES.get(key, ())
        observation = None
        matched_series = None
        if aliases:
            matched_series = db.execute(select(MacroSeries).where(MacroSeries.code.in_(aliases))).scalars().first()
            if matched_series:
                observation = db.execute(
                    select(MacroObservation)
                    .where(MacroObservation.macro_series_id == matched_series.id)
                    .order_by(MacroObservation.period.desc())
                ).scalars().first()
        channels.append({
            "key": key, "label": label, "industry_effect": effect,
            "required_source": required_source,
            "current_observation": float(observation.value) if observation else None,
            "unit": matched_series.unit if observation and matched_series else None,
            "period": observation.period.isoformat() if observation else None,
            "source": matched_series.source if observation and matched_series else None,
            "evidence_status": "available" if observation else "missing",
        })
    available = sum(channel["evidence_status"] == "available" for channel in channels)
    return {
        "status": "AVAILABLE" if channels and available == len(channels) else ("PARTIAL" if available else "INSUFFICIENT_EVIDENCE"),
        "transmission_channels": channels,
        "conclusion": (
            f"{available}/{len(channels)} mapped macro channels have current stored observations. "
            "Directional interpretation is withheld until the missing channels are populated."
        ),
    }


def build_industry_intelligence(db: Session, sector_name: str) -> dict:
    normalized = sector_name.strip().upper()
    snapshot_entries = [entry for entry in load_snapshot() if entry.sector == normalized]
    if not snapshot_entries:
        raise ValueError(f"Unsupported industry: {sector_name}")

    symbols = {entry.symbol for entry in snapshot_entries}
    securities = db.execute(
        select(Security).where(Security.symbol.in_(symbols), Security.is_active.is_(True))
    ).scalars().all()
    issuer_ids = {security.issuer_id for security in securities}
    verified_symbols = {entry.symbol for entry in snapshot_entries if entry.coverage_tier == TIER_FULL}
    verified_ids = {security.issuer_id for security in securities if security.symbol in verified_symbols}
    issuer_by_id = {
        issuer.id: issuer
        for issuer in db.execute(select(Issuer).where(Issuer.id.in_(issuer_ids))).scalars()
    }
    sector = db.execute(select(Sector).where(Sector.name.ilike(normalized))).scalar_one()
    industry_series, assessments = _industry_dataset(db, sector.id)
    derived = _derived_industry_metrics(industry_series)

    ratios = _latest_ratio_values(db, verified_ids)
    economics = []
    for key, label in ECONOMIC_RATIO_KEYS.items():
        values = ratios.get(key, [])
        economics.append({
            "key": key,
            "label": label,
            "value": round(median(values), 3) if values else None,
            "unit": "%" if "margin" in key or key in {"roe", "roic"} else "x",
            "companies_covered": len(values),
            "evidence_status": "available" if values else "missing",
        })

    operating = _operating_coverage(db, verified_ids)
    structure = []
    for key, (label, required_source) in STRUCTURE_QUESTIONS.items():
        related = [name for name in {*operating, *industry_series, *derived} if key in name]
        assessment = assessments.get(key)
        structure.append({
            "key": key,
            "label": label,
            "evidence_status": "available" if assessment else ("partial" if related else "missing"),
            "available_series": related,
            "required_source": required_source,
            "assessment": assessment,
        })

    verified_count = len(verified_symbols)
    company_count = len(snapshot_entries)
    evidence_pct = round(100 * verified_count / company_count, 1) if company_count else 0.0
    roic_spread = derived.get("roic_spread", {}).get("value")
    supply_demand = derived.get("demand_minus_capacity_growth", {}).get("value")
    pricing_spread = derived.get("pricing_power_spread", {}).get("value")
    conclusion_defensible = evidence_pct >= 60 and roic_spread is not None and supply_demand is not None
    if conclusion_defensible:
        structural_label = "ATTRACTIVE" if roic_spread > 0 and supply_demand >= 0 else "CHALLENGED"
        conclusion = (
            f"{structural_label}: verified sector ROIC spread is {roic_spread:+.2f}pp and demand growth "
            f"minus capacity growth is {supply_demand:+.2f}pp."
            + (f" Pricing power spread is {pricing_spread:+.2f}pp." if pricing_spread is not None else "")
        )
    else:
        structural_label = "INSUFFICIENT_EVIDENCE"
        conclusion = "A structural industry conclusion is withheld until verified return-on-capital and supply-demand evidence are available."

    return {
        "sector": normalized,
        "as_of": date.today().isoformat(),
        "structure": {
            "listed_competitor_count": company_count,
            "competitors": [
                {
                    "symbol": entry.symbol,
                    "name": issuer_by_id.get(
                        next((s.issuer_id for s in securities if s.symbol == entry.symbol), -1)
                    ).name if next((s.issuer_id for s in securities if s.symbol == entry.symbol), -1) in issuer_by_id else entry.name,
                    "coverage_tier": entry.coverage_tier,
                }
                for entry in snapshot_entries
            ],
            "dimensions": structure,
        },
        "economics": {
            "verified_company_count": verified_count,
            "listed_company_count": company_count,
            "verified_coverage_pct": evidence_pct,
            "sector_medians": economics,
            "operating_data_coverage": operating,
            "industry_series": industry_series,
            "derived_metrics": derived,
            "profit_driver_framework": SECTOR_PROFIT_DRIVERS.get(normalized, []),
            "profit_driver_status": "research_framework_not_yet_confirmed",
        },
        "cycle": {
            "state": "INSUFFICIENT_EVIDENCE",
            "reason": "Demand, verified capacity, utilization, price and input-cost time series are required.",
        },
        "economy_context": _macro_context(db, normalized),
        "attractiveness": {
            "status": structural_label,
            "conclusion": conclusion,
            "required_for_conclusion": [
                "verified ROIC through a full cycle",
                "demand growth versus capacity growth",
                "capacity utilization history",
                "realized pricing versus input costs",
                "imports, exports and regulatory changes",
            ],
        },
    }
