"""Earnings Quality Analysis - Recurring vs non-recurring earnings and normalized earnings"""

from typing import Dict, List, Optional, Tuple


def extract_earnings_data(workspace: Dict) -> Dict:
    """Extract net income, operating profit, and core business metrics"""
    financials = workspace.get('overview', {}).get('financials', {})

    metrics = {
        'net_income': None,
        'operating_profit': None,
        'revenue': None,
        'eps': None,
    }

    for key, series in financials.items():
        key_lower = key.lower()

        if 'net' in key_lower and ('income' in key_lower or 'profit' in key_lower):
            metrics['net_income'] = series
        elif 'operating' in key_lower and 'profit' in key_lower:
            metrics['operating_profit'] = series
        elif 'revenue' in key_lower:
            metrics['revenue'] = series
        elif 'eps' in key_lower:
            metrics['eps'] = series

    return metrics


def get_latest_value(series: Optional[List[Dict]]) -> Optional[float]:
    """Get latest value from a time series"""
    if not series or len(series) == 0:
        return None
    return series[-1].get('value')


def get_values_by_periods(series: Optional[List[Dict]], periods: int = 5) -> List[Tuple[float, str]]:
    """Get last N values from a time series in chronological order"""
    if not series:
        return []

    sorted_series = sorted(series, key=lambda x: x.get('period_end', ''))
    result = []

    for item in sorted_series[-periods:]:
        value = item.get('value')
        period = item.get('period_end')
        if value is not None and period:
            result.append((value, period))

    return result


def calculate_operating_margin(operating_profit: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """Calculate operating margin percentage"""
    if not operating_profit or not revenue or revenue <= 0:
        return None
    return (operating_profit / revenue) * 100


def calculate_net_margin(net_income: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """Calculate net margin percentage"""
    if not net_income or not revenue or revenue <= 0:
        return None
    return (net_income / revenue) * 100


def analyze_earnings_quality(metrics: Dict) -> Dict:
    """Analyze earnings quality and consistency"""

    ni_series = metrics.get('net_income')
    op_series = metrics.get('operating_profit')
    revenue_series = metrics.get('revenue')
    eps_series = metrics.get('eps')

    result = {
        'reported_earnings': {},
        'operating_earnings': {},
        'earning_persistence': {},
        'margin_quality': {}
    }

    # Reported Earnings Analysis
    if ni_series:
        ni_values = get_values_by_periods(ni_series, 5)
        if len(ni_values) > 0:
            result['reported_earnings']['trend'] = ni_values

            # Check for consistency
            if len(ni_values) >= 3:
                changes = []
                for i in range(1, len(ni_values)):
                    prev = ni_values[i-1][0]
                    curr = ni_values[i][0]
                    if prev > 0:
                        pct_change = ((curr / prev) - 1) * 100
                        changes.append(pct_change)

                if changes:
                    avg_volatility = sum(abs(c) for c in changes) / len(changes)
                    result['reported_earnings']['volatility'] = avg_volatility

                    # Consistency assessment
                    if avg_volatility < 10:
                        result['reported_earnings']['consistency'] = 'high'
                        result['reported_earnings']['note'] = 'Earnings stable and predictable'
                    elif avg_volatility < 25:
                        result['reported_earnings']['consistency'] = 'moderate'
                        result['reported_earnings']['note'] = 'Normal earnings volatility'
                    else:
                        result['reported_earnings']['consistency'] = 'low'
                        result['reported_earnings']['note'] = 'Highly volatile earnings'

    # Operating Earnings Quality (excluding one-time items)
    if op_series and revenue_series:
        op_latest = get_latest_value(op_series)
        ni_latest = get_latest_value(ni_series) if ni_series else None

        if op_latest and ni_latest:
            # If operating profit significantly differs from net income, there are non-operating items
            operating_margin = calculate_operating_margin(op_latest, get_latest_value(revenue_series))
            net_margin = calculate_net_margin(ni_latest, get_latest_value(revenue_series))

            if operating_margin and net_margin:
                margin_diff = abs(operating_margin - net_margin)
                result['operating_earnings']['operating_margin'] = operating_margin
                result['operating_earnings']['net_margin'] = net_margin
                result['operating_earnings']['margin_difference'] = margin_diff

                # Quality assessment
                if margin_diff < 2:
                    result['operating_earnings']['quality'] = 'excellent'
                    result['operating_earnings']['note'] = 'Non-recurring items minimal - high quality earnings'
                elif margin_diff < 5:
                    result['operating_earnings']['quality'] = 'good'
                    result['operating_earnings']['note'] = 'Some non-recurring items but manageable'
                else:
                    result['operating_earnings']['quality'] = 'concerning'
                    result['operating_earnings']['note'] = 'Significant gap between operating and net earnings'

        # Operating earnings trend
        op_values = get_values_by_periods(op_series, 5)
        if len(op_values) >= 2:
            result['operating_earnings']['trend'] = op_values
            first_op = op_values[0][0]
            latest_op = op_values[-1][0]

            if first_op > 0:
                op_growth = ((latest_op / first_op) - 1) * 100
                result['operating_earnings']['growth_pct'] = op_growth
                result['operating_earnings']['direction'] = 'improving' if op_growth > 5 else 'declining' if op_growth < -5 else 'stable'

    # Earnings Persistence (how sustainable are current earnings)
    if ni_series:
        ni_values = get_values_by_periods(ni_series, 5)
        if len(ni_values) >= 3:
            # Calculate trend slope
            positive_periods = 0
            for i in range(1, len(ni_values)):
                if ni_values[i][0] > ni_values[i-1][0]:
                    positive_periods += 1

            persistence_ratio = positive_periods / (len(ni_values) - 1)
            result['earning_persistence']['positive_growth_ratio'] = persistence_ratio

            if persistence_ratio >= 0.8:
                result['earning_persistence']['sustainability'] = 'high'
                result['earning_persistence']['note'] = 'Consistent earnings growth - sustainable trajectory'
            elif persistence_ratio >= 0.5:
                result['earning_persistence']['sustainability'] = 'moderate'
                result['earning_persistence']['note'] = 'Mixed earnings pattern'
            else:
                result['earning_persistence']['sustainability'] = 'low'
                result['earning_persistence']['note'] = 'Earnings declining or inconsistent'

    # Margin Quality (stability of margins)
    if op_series and revenue_series:
        op_values = get_values_by_periods(op_series, 5)
        rev_values = get_values_by_periods(revenue_series, 5)

        if len(op_values) > 0 and len(rev_values) > 0:
            margins = []
            for i, (op, period) in enumerate(op_values):
                if i < len(rev_values):
                    rev = rev_values[i][0]
                    margin = calculate_operating_margin(op, rev)
                    if margin is not None:
                        margins.append({'period': period, 'margin': margin})

            if len(margins) >= 2:
                result['margin_quality']['trend'] = margins

                # Margin stability
                margin_changes = []
                for i in range(1, len(margins)):
                    change = margins[i]['margin'] - margins[i-1]['margin']
                    margin_changes.append(abs(change))

                if margin_changes:
                    avg_margin_change = sum(margin_changes) / len(margin_changes)
                    result['margin_quality']['avg_change'] = avg_margin_change

                    if avg_margin_change < 1:
                        result['margin_quality']['stability'] = 'excellent'
                    elif avg_margin_change < 2:
                        result['margin_quality']['stability'] = 'good'
                    elif avg_margin_change < 4:
                        result['margin_quality']['stability'] = 'moderate'
                    else:
                        result['margin_quality']['stability'] = 'poor'

    return result


def calculate_normalized_eps(eps_series: Optional[List[Dict]], quality_score: float) -> Dict:
    """Calculate normalized EPS estimate based on quality"""

    result = {
        'current_eps': None,
        'normalized_eps': None,
        'quality_adjustment': 0
    }

    if eps_series:
        eps_latest = get_latest_value(eps_series)
        result['current_eps'] = eps_latest

        # Normalize based on quality score
        # If quality is low, discount normalized EPS
        # If quality is high, use current EPS
        if eps_latest:
            if quality_score >= 85:
                result['normalized_eps'] = eps_latest
                result['quality_adjustment'] = 0
            elif quality_score >= 70:
                result['normalized_eps'] = eps_latest * 0.98
                result['quality_adjustment'] = -2
            elif quality_score >= 50:
                result['normalized_eps'] = eps_latest * 0.95
                result['quality_adjustment'] = -5
            else:
                result['normalized_eps'] = eps_latest * 0.90
                result['quality_adjustment'] = -10

    return result


def calculate_earnings_quality_scorecard(quality: Dict) -> Dict:
    """Generate overall earnings quality scorecard"""

    scorecard = {
        'consistency_rating': 'unknown',
        'persistence_rating': 'unknown',
        'quality_rating': 'unknown',
        'overall_earnings_quality_score': 0,
        'recommendations': []
    }

    # Consistency rating
    consistency = quality.get('reported_earnings', {}).get('consistency')
    if consistency == 'high':
        scorecard['consistency_rating'] = 'excellent'
        scorecard['recommendations'].append('Highly consistent earnings - predictable business')
    elif consistency == 'moderate':
        scorecard['consistency_rating'] = 'good'
        scorecard['recommendations'].append('Normal earnings variability from business cycles')
    elif consistency == 'low':
        scorecard['consistency_rating'] = 'weak'
        scorecard['recommendations'].append('Volatile earnings - higher uncertainty')

    # Persistence rating
    sustainability = quality.get('earning_persistence', {}).get('sustainability')
    if sustainability == 'high':
        scorecard['persistence_rating'] = 'excellent'
        scorecard['recommendations'].append('Strong earnings momentum - sustainable growth')
    elif sustainability == 'moderate':
        scorecard['persistence_rating'] = 'moderate'
    else:
        scorecard['persistence_rating'] = 'weak'
        scorecard['recommendations'].append('Declining or inconsistent earnings trajectory')

    # Operating earnings quality
    op_quality = quality.get('operating_earnings', {}).get('quality')
    if op_quality == 'excellent':
        scorecard['quality_rating'] = 'excellent'
        scorecard['recommendations'].append('Minimal non-recurring items - clean earnings')
    elif op_quality == 'good':
        scorecard['quality_rating'] = 'good'
    elif op_quality == 'concerning':
        scorecard['quality_rating'] = 'weak'
        scorecard['recommendations'].append('Significant non-recurring items - adjust for analysis')

    # Overall score (0-100)
    score = 0

    if scorecard['consistency_rating'] == 'excellent':
        score += 30
    elif scorecard['consistency_rating'] == 'good':
        score += 22
    elif scorecard['consistency_rating'] == 'weak':
        score += 8

    if scorecard['persistence_rating'] == 'excellent':
        score += 35
    elif scorecard['persistence_rating'] == 'moderate':
        score += 20
    else:
        score += 8

    if scorecard['quality_rating'] == 'excellent':
        score += 35
    elif scorecard['quality_rating'] == 'good':
        score += 25
    elif scorecard['quality_rating'] == 'weak':
        score += 10

    scorecard['overall_earnings_quality_score'] = min(100, score)

    return scorecard


def get_earnings_quality_analysis(workspace: Dict) -> Dict:
    """Main function to get complete earnings quality analysis"""

    metrics = extract_earnings_data(workspace)
    quality = analyze_earnings_quality(metrics)
    scorecard = calculate_earnings_quality_scorecard(quality)
    normalized_eps = calculate_normalized_eps(metrics.get('eps'), scorecard['overall_earnings_quality_score'])

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'reported_earnings_analysis': quality['reported_earnings'],
        'operating_earnings_analysis': quality['operating_earnings'],
        'earning_persistence_analysis': quality['earning_persistence'],
        'margin_quality_analysis': quality['margin_quality'],
        'normalized_eps': normalized_eps,
        'earnings_quality_scorecard': scorecard,
        'summary': {
            'consistency_rating': scorecard['consistency_rating'],
            'persistence_rating': scorecard['persistence_rating'],
            'quality_rating': scorecard['quality_rating'],
            'overall_earnings_quality_score': scorecard['overall_earnings_quality_score']
        }
    }
