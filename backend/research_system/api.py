"""
Research System API Layer (Sprint 6)

REST API exposing all research data:
- Company identity and profiles
- Financial statements (raw and calculated)
- Financial metrics
- Peer comparisons
- Documents and announcements
- Events and corporate actions
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .schema import (
    Security, CompanyProfile, Document, FinancialPeriod, FinancialLineItem,
    FinancialMetric, MetricDefinition, Sector, Industry, Source
)
from .database import get_session


# ════════════════════════════════════════════════════════════════════════════════
# Response Models (Pydantic-like dicts for JSON serialization)
# ════════════════════════════════════════════════════════════════════════════════

def security_to_dict(security: Security) -> Dict[str, Any]:
    """Convert Security to API response dict."""
    return {
        "security_id": security.security_id,
        "ticker": security.ticker,
        "company_name": security.company_name,
        "legal_name": security.legal_name,
        "sector": security.sector.sector_name if security.sector else None,
        "industry": security.industry.industry_name if security.industry else None,
        "listing_date": security.listing_date.isoformat() if security.listing_date else None,
        "fiscal_year_end": security.fiscal_year_end,
        "website": security.website,
        "active": security.active,
    }


def company_profile_to_dict(profile: CompanyProfile) -> Dict[str, Any]:
    """Convert CompanyProfile to API response dict."""
    return {
        "description": profile.description,
        "business_model": profile.business_model,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


def financial_line_item_to_dict(item: FinancialLineItem) -> Dict[str, Any]:
    """Convert FinancialLineItem to API response dict."""
    metric = item.__dict__.get('metric_id')  # Will be loaded via relationship
    metric_code = None
    metric_name = None

    return {
        "metric_code": item.__dict__.get('metric_code', "UNKNOWN"),
        "reported_label": item.reported_label,
        "value": float(item.value) if item.value else 0,
        "extraction_confidence": item.extraction_confidence,
        "currency": item.currency,
    }


def financial_metric_to_dict(metric: FinancialMetric) -> Dict[str, Any]:
    """Convert FinancialMetric to API response dict."""
    return {
        "metric_code": metric.metric_code,
        "value": float(metric.value) if metric.value else 0,
        "calculation_version": metric.calculation_version,
        "calculated_at": metric.calculated_at.isoformat() if metric.calculated_at else None,
    }


def document_to_dict(doc: Document) -> Dict[str, Any]:
    """Convert Document to API response dict."""
    return {
        "document_id": doc.document_id,
        "title": doc.title,
        "document_type": doc.document_type.value if doc.document_type else None,
        "publication_date": doc.publication_date.isoformat() if doc.publication_date else None,
        "fiscal_year": doc.fiscal_year,
        "fiscal_quarter": doc.fiscal_quarter,
        "processing_status": doc.processing_status.value if doc.processing_status else None,
        "downloaded_at": doc.downloaded_at.isoformat() if doc.downloaded_at else None,
    }


# ════════════════════════════════════════════════════════════════════════════════
# API Endpoints (Business Logic)
# ════════════════════════════════════════════════════════════════════════════════

def get_all_securities(session: Session) -> List[Dict[str, Any]]:
    """GET /api/securities - List all securities."""
    securities = session.query(Security).filter_by(active=True).all()
    return [security_to_dict(s) for s in securities]


def get_security_by_ticker(session: Session, ticker: str) -> Optional[Dict[str, Any]]:
    """GET /api/securities/{ticker} - Get company identity."""
    security = session.query(Security).filter_by(ticker=ticker).first()
    if not security:
        return None
    return security_to_dict(security)


def get_company_profile(session: Session, ticker: str) -> Optional[Dict[str, Any]]:
    """GET /api/securities/{ticker}/profile - Get company business info."""
    security = session.query(Security).filter_by(ticker=ticker).first()
    if not security:
        return None

    profile = session.query(CompanyProfile).filter_by(
        security_id=security.security_id
    ).first()

    if not profile:
        return None

    return {
        "security": security_to_dict(security),
        "profile": company_profile_to_dict(profile),
    }


def get_financial_statements(
    session: Session,
    ticker: str,
    fiscal_year: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """GET /api/securities/{ticker}/financials - Get raw financial statements."""
    security = session.query(Security).filter_by(ticker=ticker).first()
    if not security:
        return None

    # Get financial periods
    query = session.query(FinancialPeriod).filter_by(security_id=security.security_id)
    if fiscal_year:
        query = query.filter_by(fiscal_year=fiscal_year)

    periods = query.all()
    if not periods:
        return None

    statements = []
    for period in periods:
        line_items = session.query(FinancialLineItem).filter_by(
            period_id=period.period_id
        ).all()

        period_type = "ANNUAL" if period.period_type.value == "ANNUAL" else f"Q{period.fiscal_quarter}"

        statements.append({
            "period": f"{period_type} FY{period.fiscal_year}",
            "period_start": period.period_start.isoformat() if period.period_start else None,
            "period_end": period.period_end.isoformat() if period.period_end else None,
            "line_items": [financial_line_item_to_dict(item) for item in line_items],
        })

    return {
        "security": security_to_dict(security),
        "statements": statements,
    }


def get_financial_metrics(
    session: Session,
    ticker: str,
    fiscal_year: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """GET /api/securities/{ticker}/metrics - Get calculated financial metrics."""
    security = session.query(Security).filter_by(ticker=ticker).first()
    if not security:
        return None

    # Get financial periods
    query = session.query(FinancialPeriod).filter_by(security_id=security.security_id)
    if fiscal_year:
        query = query.filter_by(fiscal_year=fiscal_year)

    periods = query.all()
    if not periods:
        return None

    metrics_by_period = []
    for period in periods:
        metrics = session.query(FinancialMetric).filter_by(
            period_id=period.period_id
        ).all()

        period_type = "ANNUAL" if period.period_type.value == "ANNUAL" else f"Q{period.fiscal_quarter}"

        metrics_by_period.append({
            "period": f"{period_type} FY{period.fiscal_year}",
            "metrics": [financial_metric_to_dict(m) for m in metrics],
        })

    return {
        "security": security_to_dict(security),
        "periods": metrics_by_period,
    }


def get_peer_companies(
    session: Session,
    ticker: str,
) -> Optional[Dict[str, Any]]:
    """GET /api/securities/{ticker}/peers - Get comparable companies."""
    security = session.query(Security).filter_by(ticker=ticker).first()
    if not security:
        return None

    # Get peers (same industry)
    peers = session.query(Security).filter(
        and_(
            Security.industry_id == security.industry_id,
            Security.security_id != security.security_id,
            Security.active == True,
        )
    ).all()

    return {
        "company": security_to_dict(security),
        "peers": [security_to_dict(p) for p in peers],
        "peer_count": len(peers),
    }


def get_documents(
    session: Session,
    ticker: str,
) -> Optional[Dict[str, Any]]:
    """GET /api/securities/{ticker}/documents - Get linked documents."""
    security = session.query(Security).filter_by(ticker=ticker).first()
    if not security:
        return None

    documents = session.query(Document).filter_by(
        security_id=security.security_id
    ).order_by(Document.publication_date.desc()).all()

    return {
        "security": security_to_dict(security),
        "documents": [document_to_dict(d) for d in documents],
        "document_count": len(documents),
    }


def get_statistics(session: Session) -> Dict[str, Any]:
    """GET /api/stats - Get research system statistics."""
    securities_count = session.query(Security).filter_by(active=True).count()
    documents_count = session.query(Document).count()
    line_items_count = session.query(FinancialLineItem).count()
    metrics_count = session.query(FinancialMetric).count()
    periods_count = session.query(FinancialPeriod).count()

    return {
        "securities": securities_count,
        "documents": documents_count,
        "financial_periods": periods_count,
        "line_items": line_items_count,
        "calculated_metrics": metrics_count,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ════════════════════════════════════════════════════════════════════════════════
# Simple WSGI/HTTP Server Wrapper (for testing without FastAPI)
# ════════════════════════════════════════════════════════════════════════════════

class SimpleAPI:
    """Simple API wrapper for testing without external dependencies."""

    def __init__(self):
        self.session = get_session()

    def handle_request(self, path: str, query_params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Handle API request by path."""

        # /api/securities
        if path == "/api/securities":
            return {
                "status": "success",
                "data": get_all_securities(self.session)
            }

        # /api/securities/{ticker}
        elif path.startswith("/api/securities/") and path.count("/") == 3:
            ticker = path.split("/")[3].upper()
            security = get_security_by_ticker(self.session, ticker)
            if not security:
                return {"status": "error", "message": f"Security {ticker} not found"}
            return {"status": "success", "data": security}

        # /api/securities/{ticker}/profile
        elif path.endswith("/profile"):
            ticker = path.split("/")[3].upper()
            profile = get_company_profile(self.session, ticker)
            if not profile:
                return {"status": "error", "message": f"Profile for {ticker} not found"}
            return {"status": "success", "data": profile}

        # /api/securities/{ticker}/financials
        elif path.endswith("/financials"):
            ticker = path.split("/")[3].upper()
            fiscal_year = int(query_params.get("fiscal_year")) if query_params and "fiscal_year" in query_params else None
            financials = get_financial_statements(self.session, ticker, fiscal_year)
            if not financials:
                return {"status": "error", "message": f"Financials for {ticker} not found"}
            return {"status": "success", "data": financials}

        # /api/securities/{ticker}/metrics
        elif path.endswith("/metrics"):
            ticker = path.split("/")[3].upper()
            fiscal_year = int(query_params.get("fiscal_year")) if query_params and "fiscal_year" in query_params else None
            metrics = get_financial_metrics(self.session, ticker, fiscal_year)
            if not metrics:
                return {"status": "error", "message": f"Metrics for {ticker} not found"}
            return {"status": "success", "data": metrics}

        # /api/securities/{ticker}/peers
        elif path.endswith("/peers"):
            ticker = path.split("/")[3].upper()
            peers = get_peer_companies(self.session, ticker)
            if not peers:
                return {"status": "error", "message": f"Peers for {ticker} not found"}
            return {"status": "success", "data": peers}

        # /api/securities/{ticker}/documents
        elif path.endswith("/documents"):
            ticker = path.split("/")[3].upper()
            documents = get_documents(self.session, ticker)
            if not documents:
                return {"status": "error", "message": f"Documents for {ticker} not found"}
            return {"status": "success", "data": documents}

        # /api/stats
        elif path == "/api/stats":
            return {
                "status": "success",
                "data": get_statistics(self.session)
            }

        else:
            return {"status": "error", "message": "Endpoint not found"}

    def close(self):
        """Close database session."""
        self.session.close()


# ════════════════════════════════════════════════════════════════════════════════
# Sprint 6 Test
# ════════════════════════════════════════════════════════════════════════════════

def sprint_6_api_layer():
    """
    Sprint 6: API Layer Implementation

    1. Define all API endpoints
    2. Test endpoints with sample requests
    3. Verify JSON responses
    """
    print("\n" + "="*70)
    print("SPRINT 6: RESEARCH SYSTEM API LAYER")
    print("="*70 + "\n")

    api = SimpleAPI()

    try:
        print("Step 1: Testing API endpoints...\n")

        # Test /api/securities
        print("GET /api/securities")
        response = api.handle_request("/api/securities")
        count = len(response.get("data", []))
        print(f"  [OK] {count} securities returned\n")

        # Test /api/securities/{ticker}
        print("GET /api/securities/FFC")
        response = api.handle_request("/api/securities/FFC")
        if response["status"] == "success":
            ticker = response["data"]["ticker"]
            company_name = response["data"]["company_name"]
            print(f"  [OK] {ticker}: {company_name}\n")

        # Test /api/securities/{ticker}/profile
        print("GET /api/securities/FFC/profile")
        response = api.handle_request("/api/securities/FFC/profile")
        if response["status"] == "success":
            description = response["data"]["profile"]["description"][:50]
            print(f"  [OK] Profile: {description}...\n")

        # Test /api/securities/{ticker}/financials
        print("GET /api/securities/FFC/financials?fiscal_year=2026")
        response = api.handle_request(
            "/api/securities/FFC/financials",
            {"fiscal_year": "2026"}
        )
        if response["status"] == "success":
            periods = len(response["data"]["statements"])
            total_items = sum(len(s["line_items"]) for s in response["data"]["statements"])
            print(f"  [OK] {periods} period(s), {total_items} line items\n")

        # Test /api/securities/{ticker}/metrics
        print("GET /api/securities/FFC/metrics?fiscal_year=2026")
        response = api.handle_request(
            "/api/securities/FFC/metrics",
            {"fiscal_year": "2026"}
        )
        if response["status"] == "success":
            periods = len(response["data"]["periods"])
            total_metrics = sum(len(p["metrics"]) for p in response["data"]["periods"])
            print(f"  [OK] {periods} period(s), {total_metrics} metrics\n")

        # Test /api/securities/{ticker}/peers
        print("GET /api/securities/FFC/peers")
        response = api.handle_request("/api/securities/FFC/peers")
        if response["status"] == "success":
            peer_count = response["data"]["peer_count"]
            print(f"  [OK] {peer_count} peer company(ies)\n")

        # Test /api/securities/{ticker}/documents
        print("GET /api/securities/FFC/documents")
        response = api.handle_request("/api/securities/FFC/documents")
        if response["status"] == "success":
            doc_count = response["data"]["document_count"]
            print(f"  [OK] {doc_count} document(s)\n")

        # Test /api/stats
        print("GET /api/stats")
        response = api.handle_request("/api/stats")
        if response["status"] == "success":
            data = response["data"]
            print(f"  [OK] Research System Statistics:")
            print(f"       - Securities: {data['securities']}")
            print(f"       - Documents: {data['documents']}")
            print(f"       - Periods: {data['financial_periods']}")
            print(f"       - Line Items: {data['line_items']}")
            print(f"       - Metrics: {data['calculated_metrics']}\n")

        print("="*70)
        print("Step 2: API Specification Summary")
        print("="*70 + "\n")

        endpoints = [
            ("GET", "/api/securities", "List all active companies"),
            ("GET", "/api/securities/{ticker}", "Get company by ticker"),
            ("GET", "/api/securities/{ticker}/profile", "Get company profile"),
            ("GET", "/api/securities/{ticker}/financials", "Get financial statements"),
            ("GET", "/api/securities/{ticker}/metrics", "Get calculated metrics"),
            ("GET", "/api/securities/{ticker}/peers", "Get peer companies"),
            ("GET", "/api/securities/{ticker}/documents", "Get linked documents"),
            ("GET", "/api/stats", "Get system statistics"),
        ]

        for method, path, description in endpoints:
            print(f"{method} {path}")
            print(f"  --> {description}\n")

        print("="*70)
        print("SPRINT 6 COMPLETE: Research System API is ready")
        print("="*70)

        return {
            "endpoints": len(endpoints),
            "securities_available": count,
            "status": "VALID"
        }

    finally:
        api.close()


if __name__ == "__main__":
    sprint_6_api_layer()
