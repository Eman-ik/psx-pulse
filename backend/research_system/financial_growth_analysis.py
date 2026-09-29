"""Financial Growth & Profitability Analysis - Multi-year trends and CAGR calculations"""

from typing import Dict, List, Optional, Tuple
import math


def calculate_cagr(start_value: Optional[float], end_value: Optional[float], years: int) -> Optional[float]:
    """Calculate Compound Annual Growth Rate (CAGR)"""
    if not start_value or not end_value or start_value <= 0 or end_value <= 0 or years <= 0:
        return None

    try:
        return ((end_value / start_value) ** (1 / years) - 1) * 100
    except:
        return None


def calculate_margin(profit: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """Calculate margin percentage"""
    if not profit or not revenue or revenue == 0:
        return None
    return (profit / revenue) * 100


def extract_financial_series(workspace: Dict) -> Dict:
    """Extract and organize financial series from workspace"""
    financials = workspace.get('overview', {}).get('financials', {})

    # Map of financial keys we're interested in
    metrics = {
        'revenue': None,
        'gross_profit': None,
        'operating_profit': None,
        'net_income': None,
        'eps': None,
        'shares_outstanding': None,
    }

    # Find matching keys (case-insensitive)
    for key, series in financials.items():
        key_lower = key.lower()

        if 'revenue' in key_lower and 'revenue' not in metrics:
            metrics['revenue'] = series
        elif 'gross' in key_lower and 'profit' in key_lower:
            metrics['gross_profit'] = series
        elif 'operating' in key_lower and 'profit' in key_lower:
            metrics['operating_profit'] = series
        elif 'net' in key_lower and ('income' in key_lower or 'profit' in key_lower):
            metrics['net_income'] = series
        elif 'eps' in key_lower:
            metrics['eps'] = series
        elif 'shares' in key_lower:
            metrics['shares_outstanding'] = series

    return metrics


def get_latest_values(series: Optional[List[Dict]]) -> Tuple[Optional[float], Optional[str]]:
    """Get latest value and date from a time series"""
    if not series or len(series) == 0:
        return None, None

    latest = series[-1]
    return latest.get('value'), latest.get('period_end')


def get_values_by_periods(series: Optional[List[Dict]], periods: int = 5) -> List[Tuple[float, str]]:
    """Get last N values from a time series"""
    if not series:
        return []

    # Sort by period_end to ensure chronological order
    sorted_series = sorted(series, key=lambda x: x.get('period_end', ''))

    result = []
    for item in sorted_series[-periods:]:
        value = item.get('value')
        period = item.get('period_end')
        if value is not None and period:
            result.append((value, period))

    return result


def analyze_growth_metrics(metrics: Dict) -> Dict:
    """Calculate growth metrics (CAGR for revenue, profit, EPS)"""

    revenue_series = metrics.get('revenue')
    operating_profit_series = metrics.get('operating_profit')
    net_income_series = metrics.get('net_income')
    eps_series = metrics.get('eps')

    growth = {
        'revenue_growth': {},
        'profit_growth': {},
        'eps_growth': {},
        'historical_data': {}
    }

    # Revenue growth
    if revenue_series and len(revenue_series) > 0:
        rev_values = get_values_by_periods(revenue_series, 10)
        if len(rev_values) >= 2:
            growth['historical_data']['revenue'] = rev_values

            # 1-year growth
            if len(rev_values) >= 2:
                growth['revenue_growth']['1y'] = calculate_cagr(rev_values[-2][0], rev_values[-1][0], 1)

            # 3-year CAGR
            if len(rev_values) >= 4:
                growth['revenue_growth']['3y_cagr'] = calculate_cagr(rev_values[-4][0], rev_values[-1][0], 3)

            # 5-year CAGR
            if len(rev_values) >= 6:
                growth['revenue_growth']['5y_cagr'] = calculate_cagr(rev_values[-6][0], rev_values[-1][0], 5)

            # 10-year CAGR
            if len(rev_values) >= 11:
                growth['revenue_growth']['10y_cagr'] = calculate_cagr(rev_values[-11][0], rev_values[-1][0], 10)
            elif len(rev_values) > 2:
                years = len(rev_values) - 1
                growth['revenue_growth']['max_cagr'] = calculate_cagr(rev_values[0][0], rev_values[-1][0], years)

    # Operating profit growth
    if operating_profit_series and len(operating_profit_series) > 0:
        op_values = get_values_by_periods(operating_profit_series, 10)
        if len(op_values) >= 2:
            growth['historical_data']['operating_profit'] = op_values

            if len(op_values) >= 2:
                growth['profit_growth']['1y'] = calculate_cagr(op_values[-2][0], op_values[-1][0], 1)

            if len(op_values) >= 4:
                growth['profit_growth']['3y_cagr'] = calculate_cagr(op_values[-4][0], op_values[-1][0], 3)

            if len(op_values) >= 6:
                growth['profit_growth']['5y_cagr'] = calculate_cagr(op_values[-6][0], op_values[-1][0], 5)

    # Net income growth
    if net_income_series and len(net_income_series) > 0:
        ni_values = get_values_by_periods(net_income_series, 10)
        if len(ni_values) >= 2:
            growth['historical_data']['net_income'] = ni_values

            if len(ni_values) >= 2:
                growth['profit_growth']['ni_1y'] = calculate_cagr(ni_values[-2][0], ni_values[-1][0], 1)

            if len(ni_values) >= 6:
                growth['profit_growth']['ni_5y_cagr'] = calculate_cagr(ni_values[-6][0], ni_values[-1][0], 5)

    # EPS growth
    if eps_series and len(eps_series) > 0:
        eps_values = get_values_by_periods(eps_series, 10)
        if len(eps_values) >= 2:
            growth['historical_data']['eps'] = eps_values

            if len(eps_values) >= 2:
                growth['eps_growth']['1y'] = calculate_cagr(eps_values[-2][0], eps_values[-1][0], 1)

            if len(eps_values) >= 4:
                growth['eps_growth']['3y_cagr'] = calculate_cagr(eps_values[-4][0], eps_values[-1][0], 3)

            if len(eps_values) >= 6:
                growth['eps_growth']['5y_cagr'] = calculate_cagr(eps_values[-6][0], eps_values[-1][0], 5)

    return growth


def analyze_margin_trends(metrics: Dict) -> Dict:
    """Calculate margin trends (gross, operating, net)"""

    revenue_series = metrics.get('revenue')
    gross_profit_series = metrics.get('gross_profit')
    operating_profit_series = metrics.get('operating_profit')
    net_income_series = metrics.get('net_income')

    margins = {
        'gross_margin': [],
        'operating_margin': [],
        'net_margin': [],
        'margin_trends': {}
    }

    # Gross Margin trend
    if gross_profit_series and revenue_series and len(gross_profit_series) > 0 and len(revenue_series) > 0:
        # Match periods by date
        gp_dict = {item.get('period_end'): item.get('value') for item in gross_profit_series}
        rev_dict = {item.get('period_end'): item.get('value') for item in revenue_series}

        common_dates = sorted(set(gp_dict.keys()) & set(rev_dict.keys()))

        for date in common_dates[-5:]:  # Last 5 periods
            gm = calculate_margin(gp_dict[date], rev_dict[date])
            if gm is not None:
                margins['gross_margin'].append({'period': date, 'margin': gm})

    # Operating Margin trend
    if operating_profit_series and revenue_series and len(operating_profit_series) > 0 and len(revenue_series) > 0:
        op_dict = {item.get('period_end'): item.get('value') for item in operating_profit_series}
        rev_dict = {item.get('period_end'): item.get('value') for item in revenue_series}

        common_dates = sorted(set(op_dict.keys()) & set(rev_dict.keys()))

        for date in common_dates[-5:]:
            om = calculate_margin(op_dict[date], rev_dict[date])
            if om is not None:
                margins['operating_margin'].append({'period': date, 'margin': om})

    # Net Margin trend
    if net_income_series and revenue_series and len(net_income_series) > 0 and len(revenue_series) > 0:
        ni_dict = {item.get('period_end'): item.get('value') for item in net_income_series}
        rev_dict = {item.get('period_end'): item.get('value') for item in revenue_series}

        common_dates = sorted(set(ni_dict.keys()) & set(rev_dict.keys()))

        for date in common_dates[-5:]:
            nm = calculate_margin(ni_dict[date], rev_dict[date])
            if nm is not None:
                margins['net_margin'].append({'period': date, 'margin': nm})

    # Margin trend analysis
    if margins['net_margin'] and len(margins['net_margin']) >= 2:
        first_margin = margins['net_margin'][0]['margin']
        latest_margin = margins['net_margin'][-1]['margin']
        change = latest_margin - first_margin

        margins['margin_trends']['net_margin_trend'] = {
            'direction': 'improving' if change > 0 else 'deteriorating' if change < 0 else 'stable',
            'change_points': change,
            'first_period': margins['net_margin'][0]['period'],
            'latest_period': margins['net_margin'][-1]['period']
        }

    return margins


def analyze_dilution(metrics: Dict, net_income_series: Optional[List] = None) -> Dict:
    """Analyze share dilution - EPS growth vs Net Income growth"""

    eps_series = metrics.get('eps')
    net_income_series = metrics.get('net_income')

    dilution = {
        'eps_vs_earnings_growth': {},
        'dilution_analysis': {},
        'has_dilution': False
    }

    if eps_series and net_income_series and len(eps_series) > 1 and len(net_income_series) > 1:
        # Sort by date
        eps_sorted = sorted(eps_series, key=lambda x: x.get('period_end', ''))
        ni_sorted = sorted(net_income_series, key=lambda x: x.get('period_end', ''))

        # Get latest and earliest values
        eps_latest = eps_sorted[-1].get('value')
        eps_earliest = eps_sorted[0].get('value')
        ni_latest = ni_sorted[-1].get('value')
        ni_earliest = ni_sorted[0].get('value')

        if all([eps_latest, eps_earliest, ni_latest, ni_earliest]):
            years = len(eps_sorted) - 1

            eps_growth = calculate_cagr(eps_earliest, eps_latest, years)
            ni_growth = calculate_cagr(ni_earliest, ni_latest, years)

            dilution['eps_vs_earnings_growth'] = {
                'eps_cagr': eps_growth,
                'net_income_cagr': ni_growth,
                'years_analyzed': years
            }

            if eps_growth is not None and ni_growth is not None:
                if eps_growth < ni_growth - 2:  # More than 2% difference
                    dilution['has_dilution'] = True
                    dilution['dilution_analysis'] = {
                        'status': 'dilution_detected',
                        'message': f'Net Income growing faster ({ni_growth:.1f}%) than EPS ({eps_growth:.1f}%) - share dilution occurring',
                        'difference': ni_growth - eps_growth
                    }
                elif eps_growth > ni_growth + 2:
                    dilution['dilution_analysis'] = {
                        'status': 'share_buyback',
                        'message': f'EPS growing faster ({eps_growth:.1f}%) than Net Income ({ni_growth:.1f}%) - share buyback activity',
                        'difference': eps_growth - ni_growth
                    }
                else:
                    dilution['dilution_analysis'] = {
                        'status': 'no_dilution',
                        'message': f'EPS and Net Income growing in sync - minimal share dilution',
                        'difference': abs(eps_growth - ni_growth)
                    }

    return dilution


def calculate_growth_scorecard(growth: Dict, margins: Dict, dilution: Dict) -> Dict:
    """Create overall growth scorecard"""

    scorecard = {
        'revenue_health': 'unknown',
        'profit_health': 'unknown',
        'margin_health': 'unknown',
        'dilution_health': 'unknown',
        'overall_growth_score': 0,
        'recommendations': []
    }

    # Revenue health
    rev_5y = growth.get('revenue_growth', {}).get('5y_cagr')
    if rev_5y is not None:
        if rev_5y > 15:
            scorecard['revenue_health'] = 'excellent'
        elif rev_5y > 8:
            scorecard['revenue_health'] = 'good'
        elif rev_5y > 3:
            scorecard['revenue_health'] = 'moderate'
        else:
            scorecard['revenue_health'] = 'weak'

    # Profit health
    profit_5y = growth.get('profit_growth', {}).get('5y_cagr')
    if profit_5y is not None:
        if profit_5y > 20:
            scorecard['profit_health'] = 'excellent'
        elif profit_5y > 10:
            scorecard['profit_health'] = 'good'
        elif profit_5y > 0:
            scorecard['profit_health'] = 'moderate'
        else:
            scorecard['profit_health'] = 'declining'

    # Margin health
    margin_trend = margins.get('margin_trends', {}).get('net_margin_trend', {})
    if margin_trend:
        direction = margin_trend.get('direction')
        if direction == 'improving':
            scorecard['margin_health'] = 'improving'
            scorecard['recommendations'].append('Margins expanding - pricing power or cost efficiency improving')
        elif direction == 'deteriorating':
            scorecard['margin_health'] = 'deteriorating'
            scorecard['recommendations'].append('Margins contracting - investigate cost pressures or competitive intensity')
        else:
            scorecard['margin_health'] = 'stable'

    # Dilution health
    if dilution.get('has_dilution'):
        scorecard['dilution_health'] = 'warning'
        scorecard['recommendations'].append('Share dilution detected - monitor outstanding shares')
    else:
        scorecard['dilution_health'] = 'healthy'

    # Overall growth score (0-100)
    score = 0
    if scorecard['revenue_health'] == 'excellent':
        score += 25
    elif scorecard['revenue_health'] == 'good':
        score += 18
    elif scorecard['revenue_health'] == 'moderate':
        score += 10

    if scorecard['profit_health'] == 'excellent':
        score += 25
    elif scorecard['profit_health'] == 'good':
        score += 18
    elif scorecard['profit_health'] == 'moderate':
        score += 10

    if scorecard['margin_health'] == 'improving':
        score += 25
    elif scorecard['margin_health'] == 'stable':
        score += 15

    if scorecard['dilution_health'] == 'healthy':
        score += 25
    elif scorecard['dilution_health'] == 'warning':
        score += 12

    scorecard['overall_growth_score'] = min(100, score)

    return scorecard


def get_financial_growth_analysis(workspace: Dict) -> Dict:
    """Main function to get complete financial growth analysis"""

    metrics = extract_financial_series(workspace)
    growth = analyze_growth_metrics(metrics)
    margins = analyze_margin_trends(metrics)
    dilution = analyze_dilution(metrics)
    scorecard = calculate_growth_scorecard(growth, margins, dilution)

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'growth_metrics': growth,
        'margin_analysis': margins,
        'dilution_analysis': dilution,
        'growth_scorecard': scorecard,
        'summary': {
            'revenue_health': scorecard['revenue_health'],
            'profit_health': scorecard['profit_health'],
            'margin_health': scorecard['margin_health'],
            'dilution_health': scorecard['dilution_health'],
            'overall_score': scorecard['overall_growth_score']
        }
    }
