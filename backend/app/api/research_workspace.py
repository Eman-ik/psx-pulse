"""Unified Research Studio endpoints for the fertilizer and cement universe.

The workspace is deliberately evidence-first: all 23 active sector names are searchable,
but fundamentals-backed output is only returned for ``full`` coverage companies. Existing
unverified cement rows remain quarantined by ``companies.get_company_overview``.
"""

from __future__ import annotations

from datetime import datetime, timezone
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
def research_company(ticker: str, db: Session = Depends(get_db)) -> dict:
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
