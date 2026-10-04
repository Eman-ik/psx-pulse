"""Unified Research Studio endpoints for the fertilizer and cement universe.

The workspace is deliberately evidence-first: all 23 active sector names are searchable,
but fundamentals-backed output is only returned for ``full`` coverage companies. Existing
unverified cement rows remain quarantined by ``companies.get_company_overview``.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from io import BytesIO
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.companies import get_company_overview
from app.api.comparison import companies_comparison
from app.api.deps import get_db
from app.api.sectors import cement_sector, fertilizer_sector
from app.db.models import Security
from app.etl.industry_intelligence import build_industry_intelligence
from app.services.historical_financials import get_financials_as_of, get_financials_series
from app.services.historical_universe import historical_universe, universe_timeline
from app.services.historical_feature_engine import HistoricalFeatureEngine
from app.services.historical_snapshot import HistoricalSnapshotEngine
from app.universe import SNAPSHOT_PATH, coverage_tier

router = APIRouter(prefix="/api/v1/research", tags=["research"])


def _snapshot() -> dict:
    path = Path(SNAPSHOT_PATH)
    if not path.exists():
        raise HTTPException(status_code=503, detail="Research universe snapshot is unavailable")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/universe")
def research_universe(db: Session = Depends(get_db)) -> dict:
    snapshot = _snapshot()
    active = {
        security.symbol: security.issuer_id
        for security in db.execute(select(Security).where(Security.is_active.is_(True))).scalars()
    }
    entries = [
        {**entry, "coverage_tier": coverage_tier(entry["symbol"]), "issuer_id": active.get(entry["symbol"])}
        for entry in snapshot["entries"]
        if entry["symbol"] in active
    ]
    return {
        "as_of": snapshot["as_of"],
        "count": len(entries),
        "tier_counts": {t: sum(e["coverage_tier"] == t for e in entries) for t in ("full", "unverified", "price_only")},
        "sector_counts": snapshot["sector_counts"],
        "entries": entries,
        "sectors": {
            "fertilizer": fertilizer_sector(db),
            "cement": cement_sector(db),
        },
    }


@router.get("/industry/{sector_name}")
def research_industry(sector_name: str, db: Session = Depends(get_db)) -> dict:
    """Stage 2 industry structure and economics with visible evidence gaps."""
    try:
        return build_industry_intelligence(db, sector_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _workspace_company(ticker: str, db: Session) -> dict:
    symbol = ticker.strip().upper()
    security = db.execute(
        select(Security).where(Security.symbol == symbol, Security.is_active.is_(True))
    ).scalar_one_or_none()
    if security is None:
        raise HTTPException(status_code=404, detail=f"{symbol} is not an active covered security")

    overview = get_company_overview(security.issuer_id, db)
    if overview is None:
        raise HTTPException(status_code=404, detail=f"No company record for {symbol}")

    sector_name = overview["issuer"].get("sector_name")
    peers = [row for row in companies_comparison(db) if row.get("sector") == sector_name]
    return {
        "ticker": symbol,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coverage_tier": coverage_tier(symbol),
        "overview": overview,
        "peers": peers,
        "peer_selection": {
            "method": "All active securities whose issuer has the same sector in the identity master. "
                      "No size, market-cap or business-model matching is applied.",
            "sector": sector_name,
            "count": len(peers),
        },
        "industry": build_industry_intelligence(db, sector_name),
        "evidence": {
            "source_count": len(overview.get("sources", [])),
            "announcement_count": len(overview.get("announcements", [])),
            "financial_series_count": len(overview.get("financials", {})),
            "ratio_series_count": len(overview.get("ratios", {})),
            "fundamentals_renderable": overview["coverage_tier"] == "full",
        },
    }


@router.get("/{ticker}")
async def research_company(
    ticker: str,
    db: Session = Depends(get_db),
    analysis_mode: str = "quick",
    portfolio_size_thousands: int = 100,
) -> dict:
    """Get unified research flow for company (v1 API).

    Returns snapshot → analysis → decision in a single call.
    Falls back to workspace view if analysis services unavailable.

    Args:
        ticker: Company ticker
        analysis_mode: Analysis mode (quick/deep/forecast)
        portfolio_size_thousands: Portfolio size in thousands

    Returns:
        UnifiedFlowResponse or workspace company data
    """
    try:
        from app.services.snapshot_builder import SnapshotBuilder
        from app.services.evidence_pack_builder import EvidencePackBuilder
        from app.services.llm_client import LLMClient
        from app.services.analyst_engine import AnalystEngine
        import logging

        flow_status = "complete"
        snapshot_data = {}
        analysis_data = {}
        decision_data = {}
        evidence_pack = None
        llm_result = None

        # Stage 1: Build snapshot
        try:
            builder = SnapshotBuilder()
            snapshot = builder.build(ticker)
            if not snapshot:
                raise Exception(f"No data for {ticker}")

            evidence_builder = EvidencePackBuilder()
            evidence_pack = evidence_builder.build(snapshot)
            if not evidence_pack:
                raise Exception("Failed to build evidence pack")

            snapshot_data = evidence_pack.to_dict()
        except Exception as e:
            logging.error(f"Snapshot stage failed: {e}")
            flow_status = "partial"
            snapshot_data = {"error": str(e)}

        # Stage 2: Run analysis
        try:
            if not evidence_pack:
                raise Exception("No evidence pack from stage 1")

            llm = LLMClient()
            if analysis_mode == "quick":
                llm_result = llm.analyze_quick(evidence_pack)
            elif analysis_mode == "deep":
                llm_result = llm.analyze_deep(evidence_pack)
            elif analysis_mode == "forecast":
                llm_result = llm.analyze_forecast(evidence_pack, months=12)
            else:
                raise Exception(f"Unknown analysis mode: {analysis_mode}")

            if not llm_result:
                raise Exception("Analysis failed")

            analysis_data = llm_result.to_dict()
        except Exception as e:
            logging.error(f"Analysis stage failed: {e}")
            if flow_status == "complete":
                flow_status = "partial"
            analysis_data = {"error": str(e)}

        # Stage 3: Generate decision
        try:
            if not llm_result or not evidence_pack:
                raise Exception("Missing data from previous stages")

            analyst = AnalystEngine()
            decision = analyst.decide(llm_result, evidence_pack, portfolio_size_thousands)
            if not decision:
                raise Exception("Decision generation failed")

            decision_data = decision.to_dict()
        except Exception as e:
            logging.error(f"Decision stage failed: {e}")
            if flow_status == "complete":
                flow_status = "partial"
            decision_data = {"error": str(e)}

        return {
            "ticker": ticker,
            "snapshot": snapshot_data,
            "analysis": analysis_data,
            "decision": decision_data,
            "flow_status": flow_status,
        }

    except Exception as e:
        import logging
        logging.error(f"Research company v1 failed for {ticker}: {e}")
        # Fallback to workspace view on complete failure
        return _workspace_company(ticker, db)


def _latest_value(series: list[dict]) -> float | None:
    return series[-1]["value"] if series else None


def _money(value: float | None) -> str:
    if value is None:
        return "Not available"
    magnitude = abs(value)
    if magnitude >= 1_000_000_000:
        return f"PKR {value / 1_000_000_000:,.2f}bn"
    if magnitude >= 1_000_000:
        return f"PKR {value / 1_000_000:,.2f}mn"
    return f"PKR {value:,.2f}"


def build_institutional_report(payload: dict) -> bytes:
    """Render a source-aware institutional PDF from the same API payload as the UI."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="PDF report dependency is not installed") from exc

    overview = payload["overview"]
    issuer = overview["issuer"]
    full = payload["coverage_tier"] == "full"
    financials = overview.get("financials", {})
    ratios = overview.get("ratios", {})
    output = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Cover", parent=styles["Title"], fontSize=25, leading=31, textColor=colors.HexColor("#0F2942"), alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontSize=14, leading=18, textColor=colors.HexColor("#0F5C5E"), spaceBefore=12, spaceAfter=7))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#52606D")))
    styles.add(ParagraphStyle(name="BodyInstitutional", parent=styles["BodyText"], fontSize=9.5, leading=14))

    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=17*mm, bottomMargin=17*mm, title=f"{payload['ticker']} Institutional Research Report")
    story = [
        Spacer(1, 30*mm), Paragraph("KHRONOS RESEARCH STUDIO", styles["Cover"]),
        Paragraph(f"{payload['ticker']} — {issuer['name']}", styles["Title"]),
        Paragraph(f"Institutional research delivery | {issuer.get('sector_name') or 'Sector unavailable'}", styles["Heading2"]),
        Spacer(1, 8*mm),
        Table([
            ["Coverage tier", payload["coverage_tier"].upper()],
            ["Generated", payload["generated_at"]],
            ["Source records", str(payload["evidence"]["source_count"])],
            ["Financial series", str(payload["evidence"]["financial_series_count"])],
        ], colWidths=[45*mm, 105*mm], style=[("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E7F4F3")), ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#AAB7C4")), ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 9), ("PADDING", (0,0), (-1,-1), 7)]),
        Spacer(1, 8*mm),
        Paragraph("Research use only. This report is decision support, not a regulated investment recommendation. Market data may be delayed.", styles["Small"]),
        PageBreak(),
        Paragraph("1. Executive overview", styles["Section"]),
        Paragraph(issuer.get("business_description") or "A verified business description is not available.", styles["BodyInstitutional"]),
    ]

    if not full:
        story += [
            Paragraph("Evidence limitation", styles["Section"]),
            Paragraph(
                "Fundamentals-backed valuation and investment conclusions are withheld because the financial statements are not yet verified against published filings. Identity, price coverage, announcements and available source links remain included.",
                styles["BodyInstitutional"],
            ),
        ]
    else:
        rows = [["Metric", "Latest reported value"]]
        for key, label in (("revenue", "Revenue"), ("profit_after_tax", "Profit after tax"), ("eps", "EPS"), ("total_assets", "Total assets"), ("total_equity", "Total equity")):
            value = _latest_value(financials.get(key, []))
            if key == "eps" and value is None:
                value = _latest_value(financials.get("earnings_per_share", []))
            rows.append([label, _money(value) if key != "eps" else (f"PKR {value:,.2f}" if value is not None else "Not available")])
        story += [Paragraph("2. Financial snapshot", styles["Section"]), Table(rows, colWidths=[70*mm, 80*mm], repeatRows=1, style=[("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0F5C5E")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#CBD5E1")), ("FONTSIZE", (0,0), (-1,-1), 8.5), ("PADDING", (0,0), (-1,-1), 6)])]
        ratio_rows = [["Ratio", "Latest", "Unit"]]
        for key, series in list(ratios.items())[:12]:
            ratio_rows.append([series["name"], f"{_latest_value(series['values']):,.2f}" if series["values"] else "N/A", series["unit"]])
        story += [Paragraph("3. Profitability, leverage and valuation", styles["Section"]), Table(ratio_rows, colWidths=[80*mm, 35*mm, 35*mm], repeatRows=1, style=[("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0F2942")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#CBD5E1")), ("FONTSIZE", (0,0), (-1,-1), 8.5), ("PADDING", (0,0), (-1,-1), 5)])]

    thesis = overview.get("thesis")
    industry = payload.get("industry", {})
    industry_structure = industry.get("structure", {})
    industry_economics = industry.get("economics", {})
    story += [PageBreak(), Paragraph("4. Industry structure and economics", styles["Section"])]
    story.append(Paragraph(
        f"Listed competitors: {industry_structure.get('listed_competitor_count', 'Not available')} | "
        f"Verified fundamental coverage: {industry_economics.get('verified_company_count', 0)}/"
        f"{industry_economics.get('listed_company_count', 0)} companies.",
        styles["BodyInstitutional"],
    ))
    industry_rows = [["Industry metric", "Median", "Coverage"]]
    for metric in industry_economics.get("sector_medians", []):
        value = metric.get("value")
        rendered = "Not available" if value is None else f"{value:,.2f}{metric.get('unit', '')}"
        industry_rows.append([metric.get("label", metric.get("key", "Metric")), rendered, f"{metric.get('companies_covered', 0)} companies"])
    story.append(Table(industry_rows, colWidths=[80*mm, 35*mm, 35*mm], repeatRows=1, style=[("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0F5C5E")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#CBD5E1")), ("FONTSIZE", (0,0), (-1,-1), 8.5), ("PADDING", (0,0), (-1,-1), 5)]))
    story += [Paragraph("Industry conclusion", styles["Section"]), Paragraph(industry.get("attractiveness", {}).get("conclusion", "Industry evidence is unavailable."), styles["BodyInstitutional"])]

    story += [Paragraph("5. Investment case", styles["Section"])]
    if thesis and full:
        for heading, text in (("Bull case", thesis["bull_case"]), ("Base case", thesis["base_case"]), ("Bear case", thesis["bear_case"])):
            story += [Paragraph(f"<b>{heading}</b>", styles["BodyInstitutional"]), Paragraph(text, styles["BodyInstitutional"]), Spacer(1, 3*mm)]
    else:
        story.append(Paragraph("No source-verified investment thesis is available for institutional delivery.", styles["BodyInstitutional"]))

    story += [Paragraph("6. Recent announcements", styles["Section"])]
    for announcement in overview.get("announcements", [])[:8]:
        story.append(Paragraph(f"<b>{announcement['published_at'][:10]}</b> — {announcement['title']}", styles["BodyInstitutional"]))
    if not overview.get("announcements"):
        story.append(Paragraph("No announcements are stored for this issuer.", styles["BodyInstitutional"]))

    story += [PageBreak(), Paragraph("7. Sources and lineage", styles["Section"])]
    for source in overview.get("sources", []):
        label = f"{source['document_type']} | tier {source['source_tier']} | fetched {source['fetched_at']}"
        if source.get("url"):
            label += f" | {source['url']}"
        story.append(Paragraph(label, styles["Small"]))
        story.append(Spacer(1, 2*mm))
    if not overview.get("sources"):
        story.append(Paragraph("No source documents are registered.", styles["Small"]))

    doc.build(story)
    return output.getvalue()


@router.get("/{ticker}/report.pdf")
def institutional_report(ticker: str, db: Session = Depends(get_db)) -> StreamingResponse:
    payload = _workspace_company(ticker, db)
    pdf = build_institutional_report(payload)
    filename = f"{payload['ticker']}_institutional_research.pdf"
    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/financials/as-of")
def research_financials_as_of(
    ticker: str,
    as_of: str,  # ISO format date: YYYY-MM-DD
    period_type: str = None,
    scope: str = "standalone",
    db: Session = Depends(get_db),
) -> dict:
    """Get financial facts as they were known on a specific date.

    Args:
        ticker: Company ticker symbol
        as_of: Query date in ISO format (YYYY-MM-DD)
        period_type: Optional filter (annual/half_year/quarterly/ttm)
        scope: Filter by scope (standalone/consolidated)

    Returns:
        Dict with facts known as of as_of date, respecting publication dates
    """
    try:
        from datetime import datetime as dt

        as_of_date = dt.strptime(as_of, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {as_of}") from e

    return get_financials_as_of(db, ticker, as_of_date, period_type, scope)


@router.get("/financials/series")
def research_financials_series(
    ticker: str,
    line_item: str,
    scope: str = "standalone",
    db: Session = Depends(get_db),
) -> dict:
    """Get time series of a single line item for a company.

    Args:
        ticker: Company ticker symbol
        line_item: Canonical line item key (e.g. revenue, profit_after_tax)
        scope: Filter by scope (standalone/consolidated)

    Returns:
        Dict with all historical values for the line item
    """
    return get_financials_series(db, ticker, line_item, scope)


@router.get("/universe/as-of")
def research_universe_as_of(
    as_of: str,  # ISO format date: YYYY-MM-DD
    min_price_bars: int = 1,
    min_financial_facts: int = 1,
    sector: str = None,
    db: Session = Depends(get_db),
) -> dict:
    """Get the investable universe as it was on a specific date.

    Shows which securities were listed, which had price data, and which had
    fundamental coverage available on that date.

    Args:
        as_of: Query date in ISO format (YYYY-MM-DD)
        min_price_bars: Minimum price records to count as "covered"
        min_financial_facts: Minimum facts to count as "fundamentals covered"
        sector: Optional sector filter (e.g., "Fertilizer")

    Returns:
        Dict with securities list and coverage statistics
    """
    try:
        from datetime import datetime as dt

        as_of_date = dt.strptime(as_of, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {as_of}") from e

    return historical_universe(
        db, as_of_date, min_price_bars, min_financial_facts, sector
    )


@router.get("/universe/timeline")
def research_universe_timeline(
    start_date: str,  # ISO format: YYYY-MM-DD
    end_date: str,  # ISO format: YYYY-MM-DD
    sample_interval_days: int = 30,
    db: Session = Depends(get_db),
) -> dict:
    """Get historical universe snapshots at regular intervals.

    Useful for understanding how investable universe coverage evolved over time.

    Args:
        start_date: Timeline start (ISO format)
        end_date: Timeline end (ISO format)
        sample_interval_days: Snapshot interval

    Returns:
        Dict with timeline of snapshots and summary statistics
    """
    try:
        from datetime import datetime as dt

        start_dt = dt.strptime(start_date, "%Y-%m-%d").date()
        end_dt = dt.strptime(end_date, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format") from e

    return universe_timeline(db, start_dt, end_dt, sample_interval_days)


@router.get("/features/as-of")
def research_features_as_of(
    ticker: str,
    as_of: str,  # ISO format date: YYYY-MM-DD
    scope: str = "standalone",
    db: Session = Depends(get_db),
) -> dict:
    """Calculate historical features for a company as-of a specific date.

    Uses ONLY financial facts published on or before as_of_date (prevents lookahead bias).
    Features include growth, profitability, leverage, and cash flow metrics.

    Args:
        ticker: Company ticker symbol
        as_of: Query date in ISO format (YYYY-MM-DD)
        scope: Filter by scope (standalone/consolidated)

    Returns:
        Dict with feature vector and data quality indicator
    """
    try:
        from datetime import datetime as dt

        as_of_date = dt.strptime(as_of, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {as_of}") from e

    engine = HistoricalFeatureEngine(db)
    features = engine.calculate(ticker, as_of_date, scope=scope)
    return features.to_dict()


@router.get("/snapshot/as-of")
def research_snapshot_as_of(
    ticker: str,
    as_of: str,  # ISO format date: YYYY-MM-DD
    scope: str = "standalone",
    db: Session = Depends(get_db),
) -> dict:
    """Get complete historical snapshot for a company as-of a specific date.

    Merges Stages 1-3 into unified view:
    - Universe membership (was it listed, had price/fundamental coverage)
    - Financial features (growth, profitability, leverage, cash flow)
    - Price data (closing price on or before as_of_date)
    - Quality assessment (complete/partial/insufficient)

    Args:
        ticker: Company ticker symbol
        as_of: Snapshot date in ISO format (YYYY-MM-DD)
        scope: Filter by scope (standalone/consolidated)

    Returns:
        Dict with complete snapshot and investability flag
    """
    try:
        from datetime import datetime as dt

        as_of_date = dt.strptime(as_of, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {as_of}") from e

    engine = HistoricalSnapshotEngine(db)
    snapshot = engine.snapshot(ticker, as_of_date, scope=scope)
    return snapshot.to_dict()
