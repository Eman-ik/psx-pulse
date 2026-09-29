"""
Research Studio API - Production Endpoints
Serves R1-R7 data layers to frontend

Endpoints:
  GET /api/research/companies - List covered companies
  GET /api/research/company/{ticker} - Get company master data (R1)
  GET /api/research/{ticker}/financials - Get financial statements (R2-R3)
  GET /api/research/{ticker}/metrics - Get calculated metrics (R4)
  GET /api/research/{ticker}/valuations - Get valuations (R5)
  GET /api/research/{ticker}/announcements - Get announcements (R6)
  GET /api/research/{ticker}/summary - Get AI summary (R7)
  GET /api/research/{ticker}/report - Generate PDF report
"""

from flask import Blueprint, jsonify, request, send_file
from datetime import datetime, timedelta
from models import (
    db, Company, FinancialMetric, MetricDefinition,
    StockPrice, Valuation, Announcement, ResearchSession, AIResponse
)
from sqlalchemy import desc
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

research_bp = Blueprint('research', __name__, url_prefix='/api/research')

# ============================================================================
# Helper Functions
# ============================================================================

def serialize_company(company):
    """Serialize company object to JSON"""
    if not company:
        return None
    return {
        'company_id': company.company_id,
        'ticker': company.ticker,
        'legal_name': company.legal_name,
        'sector': company.sector,
        'market_cap': float(company.market_cap) if company.market_cap else 0,
        'stock_price': float(company.stock_price) if company.stock_price else 0,
        'shares_outstanding': float(company.shares_outstanding) if company.shares_outstanding else 0,
    }

def get_latest_metrics(company_id, limit=8):
    """Get latest calculated metrics for a company"""
    metrics = FinancialMetric.query.filter_by(
        company_id=company_id,
        is_calculated=True
    ).order_by(desc(FinancialMetric.calculated_at)).limit(limit).all()

    return [{
        'code': m.metric_definition.metric_code if m.metric_definition else 'UNKNOWN',
        'value': float(m.value) if m.value else 0,
        'unit': m.unit or 'x',
        'period': f"FY{m.fiscal_year}",
        'yoy_change': float(m.yoy_change) if hasattr(m, 'yoy_change') else 0,
    } for m in metrics]

def get_financials(company_id, limit=5):
    """Get latest financial statements"""
    from sqlalchemy import and_
    from models import FinancialStatement, StatementLineItem

    statements = FinancialStatement.query.filter_by(
        company_id=company_id
    ).order_by(desc(FinancialStatement.reporting_period_end)).limit(limit).all()

    financials = []
    for stmt in statements:
        line_items = StatementLineItem.query.filter_by(
            statement_id=stmt.statement_id
        ).all()

        data = {
            'revenue': 0,
            'gross_profit': 0,
            'operating_profit': 0,
            'pat': 0,
            'total_assets': 0,
            'total_debt': 0,
            'equity': 0,
            'period': f"FY{stmt.fiscal_year}",
        }

        for item in line_items:
            if item.line_code == 'REV':
                data['revenue'] = float(item.value) if item.value else 0
            elif item.line_code == 'GROSS_PROFIT':
                data['gross_profit'] = float(item.value) if item.value else 0
            elif item.line_code == 'OPERATING_PROFIT':
                data['operating_profit'] = float(item.value) if item.value else 0
            elif item.line_code == 'PAT':
                data['pat'] = float(item.value) if item.value else 0
            elif item.line_code == 'TOTAL_ASSETS':
                data['total_assets'] = float(item.value) if item.value else 0
            elif item.line_code in ['SHORT_TERM_DEBT', 'LONG_TERM_DEBT']:
                data['total_debt'] += float(item.value) if item.value else 0
            elif item.line_code == 'TOTAL_EQUITY':
                data['equity'] = float(item.value) if item.value else 0

        financials.append(data)

    return financials[0] if financials else {
        'revenue': 0, 'gross_profit': 0, 'operating_profit': 0,
        'pat': 0, 'total_assets': 0, 'total_debt': 0, 'equity': 0, 'period': 'N/A'
    }

def get_valuations(company_id):
    """Get latest valuations"""
    valuations = Valuation.query.filter_by(
        company_id=company_id
    ).order_by(desc(Valuation.valuation_date)).limit(1).all()

    if not valuations:
        return []

    return [{
        'metric': f"{v.valuation_type}" if hasattr(v, 'valuation_type') else 'P/E',
        'value': float(v.value) if v.value else 0,
        'sector_median': float(v.sector_median) if v.sector_median else 0,
        'percentile': float(v.sector_percentile) if hasattr(v, 'sector_percentile') else 50,
    } for v in valuations]

def get_announcements(company_id, limit=5):
    """Get latest announcements"""
    announcements = Announcement.query.filter_by(
        company_id=company_id
    ).order_by(desc(Announcement.announcement_date)).limit(limit).all()

    return [{
        'date': a.announcement_date.strftime('%b %d, %Y') if a.announcement_date else '',
        'type': a.announcement_type or 'News',
        'title': a.title or a.announcement_type,
        'impact': float(a.impact_score) if hasattr(a, 'impact_score') and a.impact_score else 0,
        'metrics': json.loads(a.parsed_data) if a.parsed_data and isinstance(a.parsed_data, str) else a.parsed_data or {},
    } for a in announcements]

# ============================================================================
# API Endpoints
# ============================================================================

@research_bp.route('/companies', methods=['GET'])
def list_companies():
    """List all covered companies (R1)"""
    companies = Company.query.filter_by(status='active').order_by(Company.ticker).all()
    return jsonify({
        'success': True,
        'count': len(companies),
        'data': [serialize_company(c) for c in companies]
    })

@research_bp.route('/company/<ticker>', methods=['GET'])
def get_company(ticker):
    """Get company master data (R1)"""
    company = Company.query.filter_by(ticker=ticker.upper()).first()
    if not company:
        return jsonify({'success': False, 'error': f'Company {ticker} not found'}), 404

    return jsonify({
        'success': True,
        'data': serialize_company(company)
    })

@research_bp.route('/<ticker>/financials', methods=['GET'])
def get_company_financials(ticker):
    """Get financial statements (R2-R3)"""
    company = Company.query.filter_by(ticker=ticker.upper()).first()
    if not company:
        return jsonify({'success': False, 'error': f'Company {ticker} not found'}), 404

    financials = get_financials(company.company_id)
    return jsonify({
        'success': True,
        'ticker': ticker.upper(),
        'latest': financials
    })

@research_bp.route('/<ticker>/metrics', methods=['GET'])
def get_company_metrics(ticker):
    """Get calculated metrics (R4)"""
    company = Company.query.filter_by(ticker=ticker.upper()).first()
    if not company:
        return jsonify({'success': False, 'error': f'Company {ticker} not found'}), 404

    metrics = get_latest_metrics(company.company_id)
    metric_dict = {}
    for m in metrics:
        metric_dict[m['code'].lower()] = m['value']

    return jsonify({
        'success': True,
        'ticker': ticker.upper(),
        'calculated': metric_dict,
        'raw': metrics
    })

@research_bp.route('/<ticker>/valuations', methods=['GET'])
def get_company_valuations(ticker):
    """Get valuations (R5)"""
    company = Company.query.filter_by(ticker=ticker.upper()).first()
    if not company:
        return jsonify({'success': False, 'error': f'Company {ticker} not found'}), 404

    valuations = get_valuations(company.company_id)
    return jsonify({
        'success': True,
        'ticker': ticker.upper(),
        'data': valuations
    })

@research_bp.route('/<ticker>/announcements', methods=['GET'])
def get_company_announcements(ticker):
    """Get announcements (R6)"""
    limit = request.args.get('limit', 10, type=int)
    company = Company.query.filter_by(ticker=ticker.upper()).first()
    if not company:
        return jsonify({'success': False, 'error': f'Company {ticker} not found'}), 404

    announcements = get_announcements(company.company_id, limit)
    return jsonify({
        'success': True,
        'ticker': ticker.upper(),
        'count': len(announcements),
        'data': announcements
    })

@research_bp.route('/<ticker>/summary', methods=['GET'])
def get_company_summary(ticker):
    """Get AI research summary (R7)"""
    company = Company.query.filter_by(ticker=ticker.upper()).first()
    if not company:
        return jsonify({'success': False, 'error': f'Company {ticker} not found'}), 404

    # Get latest session for this company
    session = ResearchSession.query.filter_by(
        company_id=company.company_id
    ).order_by(desc(ResearchSession.created_at)).first()

    quality_score = 0
    if session and session.context_snapshot:
        context = json.loads(session.context_snapshot) if isinstance(session.context_snapshot, str) else session.context_snapshot
        quality_score = len([k for k, v in context.items() if v]) * 12.5

    return jsonify({
        'success': True,
        'ticker': ticker.upper(),
        'quality_score': int(quality_score),
        'last_updated': session.created_at.isoformat() if session else None
    })

@research_bp.route('/<ticker>/report', methods=['GET'])
def generate_report(ticker):
    """Generate PDF research report"""
    format_type = request.args.get('format', 'pdf')

    company = Company.query.filter_by(ticker=ticker.upper()).first()
    if not company:
        return jsonify({'success': False, 'error': f'Company {ticker} not found'}), 404

    # Gather all data
    financials = get_financials(company.company_id)
    metrics = get_latest_metrics(company.company_id)
    valuations = get_valuations(company.company_id)
    announcements = get_announcements(company.company_id, 5)

    if format_type == 'json':
        return jsonify({
            'success': True,
            'ticker': ticker.upper(),
            'company': serialize_company(company),
            'financials': financials,
            'metrics': metrics,
            'valuations': valuations,
            'announcements': announcements,
        })

    # Generate PDF
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1f2937',
        spaceAfter=6,
    )
    elements.append(Paragraph(f"Research Report: {company.ticker}", title_style))
    elements.append(Paragraph(company.legal_name, styles['Heading3']))
    elements.append(Spacer(1, 0.3*inch))

    # Company Overview
    elements.append(Paragraph("Company Overview", styles['Heading2']))
    overview_data = [
        ['Ticker', company.ticker],
        ['Sector', company.sector],
        ['Market Cap', f"Rs. {company.market_cap:,.0f}" if company.market_cap else 'N/A'],
    ]
    overview_table = Table(overview_data)
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), '#f3f4f6'),
        ('TEXTCOLOR', (0, 0), (-1, -1), '#1f2937'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, '#d1d5db')
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 0.2*inch))

    # Financials
    elements.append(Paragraph("Latest Financials", styles['Heading2']))
    fin_data = [
        ['Metric', 'Value'],
        ['Revenue', f"Rs. {financials.get('revenue', 0):,.0f}M"],
        ['Operating Profit', f"Rs. {financials.get('operating_profit', 0):,.0f}M"],
        ['Profit After Tax', f"Rs. {financials.get('pat', 0):,.0f}M"],
    ]
    fin_table = Table(fin_data)
    fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#3b82f6'),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, '#d1d5db')
    ]))
    elements.append(fin_table)
    elements.append(Spacer(1, 0.2*inch))

    # Build and return PDF
    doc.build(elements)
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{ticker.upper()}-research-report.pdf'
    )

# Register blueprint with Flask app
def init_research_api(app):
    """Initialize research API with Flask app"""
    app.register_blueprint(research_bp)
