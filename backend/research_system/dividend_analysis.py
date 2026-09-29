"""Dividend Analysis - Yield, payout ratio, sustainability, and growth tracking"""

from typing import Dict, List, Optional


def calculate_dividend_yield(dividend_per_share: Optional[float], share_price: Optional[float]) -> Optional[float]:
    """Calculate Dividend Yield"""
    if not dividend_per_share or not share_price or share_price <= 0:
        return None
    return (dividend_per_share / share_price) * 100


def calculate_payout_ratio(dividend: Optional[float], net_income: Optional[float]) -> Optional[float]:
    """Calculate Payout Ratio (Dividend / Net Income)"""
    if not dividend or not net_income or net_income <= 0:
        return None
    return (dividend / net_income) * 100


def calculate_dividend_growth(previous_dividend: Optional[float], current_dividend: Optional[float]) -> Optional[float]:
    """Calculate dividend growth percentage"""
    if not previous_dividend or not current_dividend or previous_dividend <= 0:
        return None
    return ((current_dividend / previous_dividend) - 1) * 100


def extract_dividend_data(workspace: Dict) -> Dict:
    """Extract dividend data from workspace"""
    financials = workspace.get('overview', {}).get('financials', {})

    data = {
        'dividend_history': [],
        'share_price': None,
        'net_income': None,
        'operating_cash_flow': None,
    }

    # Extract dividend history and payout data
    for key, series in financials.items():
        key_lower = key.lower()
        if 'dividend' in key_lower:
            data['dividend_history'] = series
        elif 'stock_price' in key_lower or 'share_price' in key_lower:
            data['share_price'] = series
        elif 'net' in key_lower and ('income' in key_lower or 'profit' in key_lower):
            data['net_income'] = series
        elif 'operating' in key_lower and 'cash' in key_lower:
            data['operating_cash_flow'] = series

    return data


def get_latest_value(series: Optional[List[Dict]]) -> Optional[float]:
    """Get latest value from series"""
    if not series or len(series) == 0:
        return None
    return series[-1].get('value')


def get_values_by_periods(series: Optional[List[Dict]], periods: int = 5) -> List[Dict]:
    """Get historical values"""
    if not series:
        return []
    sorted_series = sorted(series, key=lambda x: x.get('period_end', ''))
    return [{'period': item.get('period_end'), 'value': item.get('value')} for item in sorted_series[-periods:]]


def analyze_dividend_metrics(data: Dict) -> Dict:
    """Analyze dividend metrics and sustainability"""

    result = {
        'current_yield': None,
        'payout_ratio': None,
        'dividend_history': [],
        'dividend_growth': None,
        'fcf_coverage': None,
        'sustainability': 'unknown'
    }

    dividend_latest = get_latest_value(data.get('dividend_history'))
    share_price_latest = get_latest_value(data.get('share_price'))
    ni_latest = get_latest_value(data.get('net_income'))
    ocf_latest = get_latest_value(data.get('operating_cash_flow'))

    if dividend_latest and share_price_latest:
        result['current_yield'] = calculate_dividend_yield(dividend_latest, share_price_latest)

    if dividend_latest and ni_latest:
        result['payout_ratio'] = calculate_payout_ratio(dividend_latest, ni_latest)

    # Dividend history and growth
    div_history = get_values_by_periods(data.get('dividend_history'), 10)
    if len(div_history) >= 2:
        result['dividend_history'] = div_history
        growth = calculate_dividend_growth(div_history[0]['value'], div_history[-1]['value'])
        result['dividend_growth'] = growth

    # FCF coverage (can dividend be covered by FCF?)
    if ocf_latest and dividend_latest:
        result['fcf_coverage'] = ocf_latest / dividend_latest if dividend_latest > 0 else None

    # Sustainability assessment
    if result['payout_ratio'] is not None:
        if result['payout_ratio'] < 30:
            result['sustainability'] = 'excellent'
        elif result['payout_ratio'] < 50:
            result['sustainability'] = 'good'
        elif result['payout_ratio'] < 75:
            result['sustainability'] = 'moderate'
        else:
            result['sustainability'] = 'risky'

    if result['fcf_coverage'] is not None and result['fcf_coverage'] < 1.0:
        result['sustainability'] = 'risky'

    return result


def calculate_dividend_scorecard(metrics: Dict) -> Dict:
    """Generate dividend analysis scorecard"""

    scorecard = {
        'yield_assessment': 'unknown',
        'growth_assessment': 'unknown',
        'sustainability_rating': 'unknown',
        'overall_dividend_score': 0,
        'recommendations': []
    }

    # Yield assessment
    div_yield = metrics.get('current_yield')
    if div_yield is not None:
        if div_yield > 12:
            scorecard['yield_assessment'] = 'high'
            scorecard['recommendations'].append('High yield - verify sustainability before chasing')
        elif div_yield > 6:
            scorecard['yield_assessment'] = 'attractive'
        elif div_yield > 2:
            scorecard['yield_assessment'] = 'moderate'
        else:
            scorecard['yield_assessment'] = 'low'

    # Growth assessment
    div_growth = metrics.get('dividend_growth')
    if div_growth is not None:
        if div_growth > 10:
            scorecard['growth_assessment'] = 'strong'
            scorecard['recommendations'].append('Strong dividend growth - positive sign')
        elif div_growth > 5:
            scorecard['growth_assessment'] = 'good'
        elif div_growth > 0:
            scorecard['growth_assessment'] = 'modest'
        else:
            scorecard['growth_assessment'] = 'declining'
            scorecard['recommendations'].append('Dividend declining - investigate reasons')

    # Sustainability
    sustainability = metrics.get('sustainability')
    scorecard['sustainability_rating'] = sustainability

    if sustainability == 'risky':
        scorecard['recommendations'].append('Low margin of safety - dividend at risk of cuts')
    elif sustainability == 'excellent':
        scorecard['recommendations'].append('Conservative payout - dividend very safe')

    # Overall score
    score = 0

    if scorecard['yield_assessment'] == 'attractive':
        score += 25
    elif scorecard['yield_assessment'] == 'moderate':
        score += 15
    elif scorecard['yield_assessment'] == 'high':
        score += 12  # penalize chasing yield

    if scorecard['growth_assessment'] == 'strong':
        score += 30
    elif scorecard['growth_assessment'] == 'good':
        score += 22
    elif scorecard['growth_assessment'] == 'modest':
        score += 12

    if sustainability == 'excellent':
        score += 30
    elif sustainability == 'good':
        score += 22
    elif sustainability == 'moderate':
        score += 12
    elif sustainability == 'risky':
        score += 3

    scorecard['overall_dividend_score'] = min(100, score)

    return scorecard


def get_dividend_analysis(workspace: Dict) -> Dict:
    """Main function to get dividend analysis"""

    data = extract_dividend_data(workspace)
    metrics = analyze_dividend_metrics(data)
    scorecard = calculate_dividend_scorecard(metrics)

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'dividend_metrics': metrics,
        'dividend_scorecard': scorecard,
        'summary': {
            'current_yield': metrics.get('current_yield'),
            'payout_ratio': metrics.get('payout_ratio'),
            'dividend_growth': metrics.get('dividend_growth'),
            'sustainability': scorecard['sustainability_rating'],
            'overall_dividend_score': scorecard['overall_dividend_score']
        }
    }
