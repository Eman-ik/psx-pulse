"""Capital Allocation Analysis - How management deploys shareholder capital"""

from typing import Dict, List, Optional


def analyze_cash_deployment(workspace: Dict) -> Dict:
    """Analyze how company deploys excess cash"""

    analysis = {
        'reinvestment': None,
        'debt_repayment': None,
        'dividend_payout': None,
        'share_buyback': None,
        'acquisitions': None,
        'cash_accumulation': None,
        'capital_allocation_score': 0
    }

    # Extract relevant metrics
    ocf = workspace.get('overview', {}).get('financials', {}).get('operating_cash_flow', [None])
    capex = workspace.get('overview', {}).get('financials', {}).get('capex', [None])
    debt_change = workspace.get('overview', {}).get('financials', {}).get('debt', [None])
    dividend = workspace.get('overview', {}).get('financials', {}).get('dividend', [None])

    if ocf[0] and capex[0]:
        analysis['reinvestment'] = ((capex[0] / ocf[0]) * 100) if ocf[0] > 0 else None

    if ocf[0] and dividend[0]:
        analysis['dividend_payout'] = ((dividend[0] / ocf[0]) * 100) if ocf[0] > 0 else None

    return analysis


def calculate_roc_on_capex(incremental_capex: Optional[float], incremental_profit: Optional[float]) -> Optional[float]:
    """Calculate return on incremental capex"""
    if not incremental_capex or not incremental_profit or incremental_capex <= 0:
        return None
    return (incremental_profit / incremental_capex) * 100


def assess_allocation_quality(deployment: Dict) -> Dict:
    """Assess quality of capital allocation decisions"""

    assessment = {
        'allocation_quality': 'unknown',
        'focus_area': 'unknown',
        'recommendations': []
    }

    reinvest_pct = deployment.get('reinvestment')
    dividend_pct = deployment.get('dividend_payout')

    if reinvest_pct and reinvest_pct > 50:
        assessment['focus_area'] = 'growth_focused'
        assessment['recommendations'].append('Company prioritizing reinvestment for growth')
    elif dividend_pct and dividend_pct > 30:
        assessment['focus_area'] = 'shareholder_return'
        assessment['recommendations'].append('Strong focus on shareholder returns via dividends')
    else:
        assessment['focus_area'] = 'balanced'

    # Quality assessment
    if reinvest_pct and reinvest_pct < 30 and dividend_pct and dividend_pct < 50:
        assessment['allocation_quality'] = 'conservative'
        assessment['recommendations'].append('Conservative use of capital - cash accumulating')
    elif reinvest_pct and reinvest_pct > 40 and dividend_pct and dividend_pct < 30:
        assessment['allocation_quality'] = 'growth_oriented'
        assessment['recommendations'].append('Growth-oriented allocation strategy')
    else:
        assessment['allocation_quality'] = 'balanced'

    return assessment


def get_capital_allocation_analysis(workspace: Dict) -> Dict:
    """Main function to get capital allocation analysis"""

    deployment = analyze_cash_deployment(workspace)
    assessment = assess_allocation_quality(deployment)

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'cash_deployment': deployment,
        'allocation_assessment': assessment,
        'summary': {
            'allocation_quality': assessment['allocation_quality'],
            'focus_area': assessment['focus_area'],
            'recommendations': assessment['recommendations']
        }
    }
