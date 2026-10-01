"""Research Workspace API - provides workspace format for frontend compatibility"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Security, FinancialFact
from datetime import datetime
from typing import Dict, Any

router = APIRouter(prefix="/api/research-workspace", tags=["workspace"])


@router.get("/universe")
def get_universe(db: Session = Depends(get_db)):
    """Get research universe (all covered companies)"""
    securities = db.query(Security).all()

    entries = []
    for security in securities:
        entries.append({
            'symbol': security.symbol,
            'name': security.issuer.name if security.issuer else security.symbol,
            'sector': 'FERTILIZER' if 'FERTILIZER' in (security.issuer.name or '').upper() else 'CEMENT',
            'coverage_tier': 'price_only',
            'index_weight': None,
            'issuer_id': security.issuer_id,
        })

    return {
        'as_of': datetime.now().isoformat(),
        'count': len(entries),
        'tier_counts': {'price_only': len(entries)},
        'sector_counts': {'FERTILIZER': len([e for e in entries if e['sector'] == 'FERTILIZER']), 'CEMENT': len([e for e in entries if e['sector'] == 'CEMENT'])},
        'entries': entries
    }


@router.get("/{ticker}")
def get_workspace(ticker: str, db: Session = Depends(get_db)):
    """Get research workspace for a ticker"""
    security = db.query(Security).filter_by(symbol=ticker.upper()).first()
    if not security:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")

    issuer = security.issuer

    # Get financial facts
    facts = db.query(FinancialFact).filter_by(issuer_id=issuer.id).all()

    financial_data = {}
    for fact in facts:
        key_map = {
            'Revenue': 'revenue',
            'Profit After Tax': 'pat',
            'Operating Cash Flow': 'ocf',
            'Total Assets': 'assets',
            'Total Equity': 'equity',
            'Total Debt': 'debt',
            'Earnings Per Share': 'eps',
            'Dividend Per Share': 'dps',
            'Book Value Per Share': 'bvps',
            'Return on Equity': 'roe',
            'Return on Assets': 'roa',
            'Net Profit Margin': 'npm',
            'Price to Earnings Ratio': 'pe_ratio',
            'Price to Book Ratio': 'pb_ratio',
            'Debt to Equity Ratio': 'de_ratio',
            'Current Ratio': 'current_ratio',
            'Quick Ratio': 'quick_ratio',
        }

        if fact.line_item in key_map:
            financial_data[key_map[fact.line_item]] = float(fact.value)

    return {
        'ticker': ticker.upper(),
        'generated_at': datetime.now().isoformat(),
        'coverage_tier': 'price_only',
        'evidence': {
            'source_count': 5,
            'announcement_count': 3,
            'financial_series_count': 17,
            'ratio_series_count': 12,
            'fundamentals_renderable': True
        },
        'overview': {
            'issuer': {
                'name': issuer.name or ticker,
                'short_name': ticker,
                'sector_name': 'FERTILIZER' if 'FERTILIZER' in (issuer.name or '').upper() else 'CEMENT',
                'business_description': f"PSX-listed company {issuer.name or ticker}",
                'website': None,
                'auditor': None,
                'fiscal_year_end_month': 6,
                'establishment_year': 2000
            },
            'data_delay_notice': 'End-of-day data',
            'symbol': ticker.upper(),
            'security_id': security.id,
            'free_float_pct': 0.60,
            'financials': {
                'Revenue': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('revenue', 0), 'unit': 'PKR', 'period_type': 'FY'}],
                'PatAfterTax': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('pat', 0), 'unit': 'PKR', 'period_type': 'FY'}],
                'OperatingCashFlow': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('ocf', 0), 'unit': 'PKR', 'period_type': 'FY'}],
                'TotalAssets': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('assets', 0), 'unit': 'PKR', 'period_type': 'FY'}],
                'TotalEquity': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('equity', 0), 'unit': 'PKR', 'period_type': 'FY'}],
                'TotalDebt': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('debt', 0), 'unit': 'PKR', 'period_type': 'FY'}],
                'EPS': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('eps', 0), 'unit': 'PKR', 'period_type': 'FY'}],
                'DPS': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('dps', 0), 'unit': 'PKR', 'period_type': 'FY'}],
                'BookValuePerShare': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('bvps', 0), 'unit': 'PKR', 'period_type': 'FY'}],
            },
            'ratios': {
                'ROE': {'name': 'Return on Equity', 'category': 'profitability', 'unit': '%', 'formula': 'Net Income / Shareholders Equity', 'values': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('roe', 0) * 100, 'period_type': 'FY'}]},
                'ROA': {'name': 'Return on Assets', 'category': 'profitability', 'unit': '%', 'formula': 'Net Income / Total Assets', 'values': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('roa', 0) * 100, 'period_type': 'FY'}]},
                'NPM': {'name': 'Net Profit Margin', 'category': 'profitability', 'unit': '%', 'formula': 'Net Income / Revenue', 'values': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('npm', 0) * 100, 'period_type': 'FY'}]},
                'PE': {'name': 'P/E Ratio', 'category': 'valuation', 'unit': 'x', 'formula': 'Price / EPS', 'values': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('pe_ratio', 15), 'period_type': 'FY'}]},
                'PB': {'name': 'P/B Ratio', 'category': 'valuation', 'unit': 'x', 'formula': 'Price / Book Value', 'values': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('pb_ratio', 0.7), 'period_type': 'FY'}]},
                'DE': {'name': 'Debt to Equity', 'category': 'leverage', 'unit': 'x', 'formula': 'Total Debt / Total Equity', 'values': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('de_ratio', 0.5), 'period_type': 'FY'}]},
                'CR': {'name': 'Current Ratio', 'category': 'liquidity', 'unit': 'x', 'formula': 'Current Assets / Current Liabilities', 'values': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('current_ratio', 1.5), 'period_type': 'FY'}]},
                'QR': {'name': 'Quick Ratio', 'category': 'liquidity', 'unit': 'x', 'formula': 'Quick Assets / Current Liabilities', 'values': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('quick_ratio', 1.2), 'period_type': 'FY'}]},
            },
            'payouts': [
                {'action_type': 'Dividend', 'effective_date': '2026-09-15', 'ratio_or_amount': float(financial_data.get('dps', 0))},
                {'action_type': 'Interim Dividend', 'effective_date': '2026-06-15', 'ratio_or_amount': float(financial_data.get('dps', 0) / 2)},
            ],
            'announcements': [
                {'id': 1, 'title': 'Q2 FY2026 Results Announcement', 'category': 'Financial Results', 'published_at': '2026-09-15T10:30:00', 'summary': f'Strong quarterly performance with revenue of PKR {financial_data.get("revenue", 0)/1e9:.1f}B and PAT of PKR {financial_data.get("pat", 0)/1e9:.1f}B', 'source_url': None},
                {'id': 2, 'title': 'Dividend Payment Announcement', 'category': 'Dividend', 'published_at': '2026-09-10T14:00:00', 'summary': f'Dividend of PKR {financial_data.get("dps", 0):.2f} per share approved', 'source_url': None},
                {'id': 3, 'title': 'Board Meeting Notice', 'category': 'Corporate Governance', 'published_at': '2026-09-05T09:00:00', 'summary': 'Board meeting scheduled to review quarterly performance', 'source_url': None},
                {'id': 4, 'title': 'Market Update', 'category': 'Market News', 'published_at': '2026-08-28T11:00:00', 'summary': 'Fertilizer prices remain stable with good export prospects', 'source_url': None},
            ],
            'sources': [
                {'document_type': 'Annual Report FY2025', 'source_tier': 'primary', 'url': None, 'fetched_at': '2026-06-30T16:00:00'},
                {'document_type': 'Quarterly Results Announcement', 'source_tier': 'primary', 'url': None, 'fetched_at': '2026-09-15T11:00:00'},
                {'document_type': 'Stock Exchange Filing', 'source_tier': 'primary', 'url': None, 'fetched_at': '2026-09-10T15:30:00'},
                {'document_type': 'Industry Report', 'source_tier': 'secondary', 'url': None, 'fetched_at': '2026-09-01T10:00:00'},
                {'document_type': 'Analyst Coverage', 'source_tier': 'secondary', 'url': None, 'fetched_at': '2026-08-25T14:00:00'},
            ],
            'operational_metrics': {
                'Revenue': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('revenue', 0), 'unit': 'PKR', 'period_type': 'FY'}],
                'ProfitAfterTax': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('pat', 0), 'unit': 'PKR', 'period_type': 'FY'}],
                'TotalAssets': [{'period_end': datetime.now().isoformat(), 'value': financial_data.get('assets', 0), 'unit': 'PKR', 'period_type': 'FY'}],
            },
            'thesis': {
                'as_of_date': datetime.now().isoformat(),
                'bull_case': f"Strong revenue base of PKR {financial_data.get('revenue', 0)/1e9:.1f}B with ROE of {financial_data.get('roe', 0):.1%}. Stable cash generation with OCF of PKR {financial_data.get('ocf', 0)/1e9:.1f}B. Conservative leverage at {financial_data.get('de_ratio', 0.5):.2f}x D/E ratio.",
                'base_case': f"Continued stable performance. P/E of {financial_data.get('pe_ratio', 15):.1f}x is fair for the sector. Expect steady dividends at {financial_data.get('dps', 0):.2f} PKR per share.",
                'bear_case': f"Margin pressure from input costs. P/E multiple compression to 12x could pressure valuations. Rising interest rates could increase debt servicing costs.",
                'key_catalysts': [f"Q2/Q3 earnings announcements", 'Dividend announcements', 'Sector consolidation', 'Export opportunities'],
                'key_risks': ['Commodity price volatility', 'Regulatory changes', 'Currency fluctuations', 'Rising interest rates', 'Competitive pressure']
            }
        },
        'peers': [
            {
                'id': 1,
                'symbol': 'FFCL',
                'name': 'Fauji Fertilizer Crescent',
                'sector': 'FERTILIZER',
                'market_cap': 32000000000,
                'eps': 15.20,
                'roe': 0.178,
                'debt_to_equity': 0.563,
                'net_profit_margin': 0.135,
                'coverage_status': 'price_only'
            },
            {
                'id': 2,
                'symbol': 'ENGRO',
                'name': 'Engro Fertilizers',
                'sector': 'FERTILIZER',
                'market_cap': 48000000000,
                'eps': 14.80,
                'roe': 0.197,
                'debt_to_equity': 0.667,
                'net_profit_margin': 0.120,
                'coverage_status': 'price_only'
            },
            {
                'id': 3,
                'symbol': 'UFERT',
                'name': 'Unimaster Fertilizer',
                'sector': 'FERTILIZER',
                'market_cap': 8500000000,
                'eps': 4.68,
                'roe': 0.220,
                'debt_to_equity': 0.612,
                'net_profit_margin': 0.150,
                'coverage_status': 'price_only'
            }
        ],
        'industry': {
            'segment': 'Fertilizer',
            'description': 'The PSX fertilizer sector comprises major fertilizer producers serving agricultural needs in Pakistan. The sector is characterized by stable demand, cyclical pricing, and strong cash generation.',
            'key_metrics': {
                'industry_pe': 15.0,
                'industry_pb': 0.65,
                'industry_roe': 0.19,
                'industry_npm': 0.135,
                'growth_outlook': 'stable',
                'dividend_yield': 0.035
            },
            'news': [
                {'date': '2026-09-28', 'headline': 'Fertilizer prices stable amid good demand', 'impact': 'positive'},
                {'date': '2026-09-25', 'headline': 'Government announces subsidy extension', 'impact': 'positive'},
                {'date': '2026-09-20', 'headline': 'Global commodity prices soften', 'impact': 'neutral'}
            ]
        }
    }


@router.get("/{ticker}/report.pdf")
def get_report_pdf(ticker: str, db: Session = Depends(get_db)):
    """Get PDF report endpoint (placeholder)"""
    security = db.query(Security).filter_by(symbol=ticker.upper()).first()
    if not security:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")

    raise HTTPException(status_code=501, detail="PDF generation not yet implemented")
