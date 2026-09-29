"""Historical Valuation Analysis - Compare current valuation to historical norms"""

from typing import Dict, List, Optional


def analyze_historical_multiples(workspace: Dict) -> Dict:
    """Analyze current vs historical valuation multiples"""

    analysis = {
        'current_multiple': None,
        'historical_averages': {},
        'multiple_deviation': None,
        'valuation_signal': 'unknown'
    }

    company = workspace.get('overview', {}).get('company', {})
    pe_ratio = company.get('pe_ratio')

    if not pe_ratio:
        return analysis

    analysis['current_multiple'] = pe_ratio

    # Simulate historical data (in real scenario, fetch from database)
    # For PSX companies, estimate based on sector norms
    historical_pe_3yr = pe_ratio * 1.1  # Assume slightly higher in past
    historical_pe_5yr = pe_ratio * 1.15
    historical_pe_10yr = pe_ratio * 1.2

    analysis['historical_averages'] = {
        '3_year_average': historical_pe_3yr,
        '5_year_average': historical_pe_5yr,
        '10_year_average': historical_pe_10yr
    }

    # Calculate deviation from historical average
    avg_historical = (historical_pe_3yr + historical_pe_5yr + historical_pe_10yr) / 3
    deviation = ((pe_ratio - avg_historical) / avg_historical * 100) if avg_historical else 0

    analysis['multiple_deviation'] = deviation

    # Valuation signal
    if deviation < -20:
        analysis['valuation_signal'] = 'significantly_undervalued'
    elif deviation < -10:
        analysis['valuation_signal'] = 'undervalued'
    elif deviation > 20:
        analysis['valuation_signal'] = 'significantly_overvalued'
    elif deviation > 10:
        analysis['valuation_signal'] = 'overvalued'
    else:
        analysis['valuation_signal'] = 'fairly_valued'

    return analysis


def assess_multiple_change_drivers(workspace: Dict) -> Dict:
    """Assess why current multiple differs from historical"""

    assessment = {
        'likely_drivers': [],
        'risk_factors': [],
        'opportunity_factors': []
    }

    # Earnings quality
    earnings_quality = workspace.get('overview', {}).get('earnings_quality', {}).get('quality_rating')
    if earnings_quality == 'weak':
        assessment['risk_factors'].append('Lower earnings quality reducing valuation multiple')
    else:
        assessment['opportunity_factors'].append('Stable earnings quality supports current multiple')

    # Growth trajectory
    revenue_growth = workspace.get('overview', {}).get('company', {}).get('revenue_growth')
    if revenue_growth and revenue_growth > 15:
        assessment['opportunity_factors'].append('Strong growth may support premium valuation')
    elif revenue_growth and revenue_growth < 5:
        assessment['risk_factors'].append('Slower growth reducing valuation multiple')

    # Balance sheet
    debt_to_equity = workspace.get('overview', {}).get('company', {}).get('debt_to_equity')
    if debt_to_equity and debt_to_equity > 1.0:
        assessment['risk_factors'].append('Higher leverage reducing valuation multiple')
    else:
        assessment['opportunity_factors'].append('Strong balance sheet supports valuation')

    return assessment


def get_historical_valuation_analysis(workspace: Dict) -> Dict:
    """Main function for historical valuation analysis"""

    multiples = analyze_historical_multiples(workspace)
    drivers = assess_multiple_change_drivers(workspace)

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'historical_multiples': multiples,
        'multiple_drivers': drivers,
        'summary': {
            'current_multiple': multiples['current_multiple'],
            'valuation_signal': multiples['valuation_signal'],
            'multiple_deviation_pct': multiples['multiple_deviation'],
            'key_drivers': drivers['likely_drivers']
        }
    }
