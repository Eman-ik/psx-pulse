"""Returns on Capital Analysis - ROE, ROA, ROIC trend analysis and sustainability"""

from typing import Dict, List, Optional, Tuple


def calculate_roe(net_income: Optional[float], equity: Optional[float]) -> Optional[float]:
    """Calculate Return on Equity (Net Income / Shareholders' Equity)"""
    if not net_income or not equity or equity <= 0:
        return None
    return (net_income / equity) * 100


def calculate_roa(net_income: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """Calculate Return on Assets (Net Income / Total Assets)"""
    if not net_income or not total_assets or total_assets <= 0:
        return None
    return (net_income / total_assets) * 100


def calculate_roic(nopat: Optional[float], invested_capital: Optional[float]) -> Optional[float]:
    """Calculate Return on Invested Capital (NOPAT / Invested Capital)"""
    if not nopat or not invested_capital or invested_capital <= 0:
        return None
    return (nopat / invested_capital) * 100


def extract_capital_metrics(workspace: Dict) -> Dict:
    """Extract net income, equity, assets, and operating profit from workspace"""
    financials = workspace.get('overview', {}).get('financials', {})

    metrics = {
        'net_income': None,
        'equity': None,
        'total_assets': None,
        'operating_profit': None,
        'interest_expense': None,
    }

    for key, series in financials.items():
        key_lower = key.lower()

        if 'net' in key_lower and ('income' in key_lower or 'profit' in key_lower):
            metrics['net_income'] = series
        elif 'equity' in key_lower or 'shareholder' in key_lower:
            metrics['equity'] = series
        elif 'asset' in key_lower and 'total' in key_lower:
            metrics['total_assets'] = series
        elif 'operating' in key_lower and 'profit' in key_lower:
            metrics['operating_profit'] = series
        elif 'interest' in key_lower and 'expense' in key_lower:
            metrics['interest_expense'] = series

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


def analyze_return_metrics(metrics: Dict) -> Dict:
    """Calculate ROE, ROA, ROIC from available data"""

    net_income_series = metrics.get('net_income')
    equity_series = metrics.get('equity')
    assets_series = metrics.get('total_assets')
    operating_profit_series = metrics.get('operating_profit')

    result = {
        'roe_analysis': {},
        'roa_analysis': {},
        'roic_analysis': {},
        'historical_data': {}
    }

    # ROE Analysis
    if net_income_series and equity_series:
        ni_latest = get_latest_value(net_income_series)
        eq_latest = get_latest_value(equity_series)

        if ni_latest and eq_latest:
            roe = calculate_roe(ni_latest, eq_latest)
            result['roe_analysis']['current'] = roe

            # Get historical ROE trend
            ni_values = get_values_by_periods(net_income_series, 5)
            eq_values = get_values_by_periods(equity_series, 5)

            if len(ni_values) > 0 and len(eq_values) > 0:
                roe_values = []
                for i, (ni, period) in enumerate(ni_values):
                    if i < len(eq_values):
                        eq = eq_values[i][0]
                        roe_val = calculate_roe(ni, eq)
                        if roe_val is not None:
                            roe_values.append({'period': period, 'roe': roe_val})

                if len(roe_values) >= 2:
                    result['roe_analysis']['trend'] = roe_values
                    first_roe = roe_values[0]['roe']
                    latest_roe = roe_values[-1]['roe']
                    change = latest_roe - first_roe
                    result['roe_analysis']['direction'] = 'improving' if change > 0.5 else 'declining' if change < -0.5 else 'stable'
                    result['roe_analysis']['change_points'] = change

    # ROA Analysis
    if net_income_series and assets_series:
        ni_latest = get_latest_value(net_income_series)
        assets_latest = get_latest_value(assets_series)

        if ni_latest and assets_latest:
            roa = calculate_roa(ni_latest, assets_latest)
            result['roa_analysis']['current'] = roa

            ni_values = get_values_by_periods(net_income_series, 5)
            assets_values = get_values_by_periods(assets_series, 5)

            if len(ni_values) > 0 and len(assets_values) > 0:
                roa_values = []
                for i, (ni, period) in enumerate(ni_values):
                    if i < len(assets_values):
                        assets = assets_values[i][0]
                        roa_val = calculate_roa(ni, assets)
                        if roa_val is not None:
                            roa_values.append({'period': period, 'roa': roa_val})

                if len(roa_values) >= 2:
                    result['roa_analysis']['trend'] = roa_values
                    first_roa = roa_values[0]['roa']
                    latest_roa = roa_values[-1]['roa']
                    change = latest_roa - first_roa
                    result['roa_analysis']['direction'] = 'improving' if change > 0.5 else 'declining' if change < -0.5 else 'stable'

    # ROIC Analysis (simplified: using operating profit as proxy for NOPAT)
    if operating_profit_series and assets_series:
        op_latest = get_latest_value(operating_profit_series)
        assets_latest = get_latest_value(assets_series)

        if op_latest and assets_latest:
            # Simplified ROIC = Operating Profit / Total Assets
            roic = calculate_roic(op_latest, assets_latest)
            result['roic_analysis']['current'] = roic

            op_values = get_values_by_periods(operating_profit_series, 5)
            assets_values = get_values_by_periods(assets_series, 5)

            if len(op_values) > 0 and len(assets_values) > 0:
                roic_values = []
                for i, (op, period) in enumerate(op_values):
                    if i < len(assets_values):
                        assets = assets_values[i][0]
                        roic_val = calculate_roic(op, assets)
                        if roic_val is not None:
                            roic_values.append({'period': period, 'roic': roic_val})

                if len(roic_values) >= 2:
                    result['roic_analysis']['trend'] = roic_values
                    first_roic = roic_values[0]['roic']
                    latest_roic = roic_values[-1]['roic']
                    change = latest_roic - first_roic
                    result['roic_analysis']['direction'] = 'improving' if change > 0.5 else 'declining' if change < -0.5 else 'stable'

    return result


def calculate_return_scorecard(roe_analysis: Dict, roa_analysis: Dict, roic_analysis: Dict) -> Dict:
    """Generate overall return on capital scorecard"""

    scorecard = {
        'roe_health': 'unknown',
        'roa_health': 'unknown',
        'roic_health': 'unknown',
        'overall_return_score': 0,
        'recommendations': []
    }

    # ROE Health (excellent >15%, good >10%, moderate >5%, weak <5%)
    roe_current = roe_analysis.get('current')
    if roe_current is not None:
        if roe_current > 20:
            scorecard['roe_health'] = 'excellent'
            scorecard['recommendations'].append('Exceptional ROE - management generating strong returns on equity')
        elif roe_current > 15:
            scorecard['roe_health'] = 'excellent'
            scorecard['recommendations'].append('Strong ROE indicates efficient capital utilization')
        elif roe_current > 10:
            scorecard['roe_health'] = 'good'
            scorecard['recommendations'].append('Solid ROE showing good shareholder value creation')
        elif roe_current > 5:
            scorecard['roe_health'] = 'moderate'
            scorecard['recommendations'].append('Moderate ROE - room for improvement in capital efficiency')
        else:
            scorecard['roe_health'] = 'weak'
            scorecard['recommendations'].append('Weak ROE - investigate capital inefficiency')

    # ROA Health
    roa_current = roa_analysis.get('current')
    if roa_current is not None:
        if roa_current > 10:
            scorecard['roa_health'] = 'excellent'
        elif roa_current > 5:
            scorecard['roa_health'] = 'good'
        elif roa_current > 2:
            scorecard['roa_health'] = 'moderate'
        else:
            scorecard['roa_health'] = 'weak'

    # ROIC Health
    roic_current = roic_analysis.get('current')
    if roic_current is not None:
        if roic_current > 15:
            scorecard['roic_health'] = 'excellent'
            scorecard['recommendations'].append('High ROIC indicates strong competitive advantage')
        elif roic_current > 10:
            scorecard['roic_health'] = 'good'
        elif roic_current > 5:
            scorecard['roic_health'] = 'moderate'
        else:
            scorecard['roic_health'] = 'weak'

    # Overall score (0-100)
    score = 0

    if scorecard['roe_health'] == 'excellent':
        score += 30
    elif scorecard['roe_health'] == 'good':
        score += 22
    elif scorecard['roe_health'] == 'moderate':
        score += 12

    if scorecard['roa_health'] == 'excellent':
        score += 25
    elif scorecard['roa_health'] == 'good':
        score += 18
    elif scorecard['roa_health'] == 'moderate':
        score += 10

    if scorecard['roic_health'] == 'excellent':
        score += 35
    elif scorecard['roic_health'] == 'good':
        score += 25
    elif scorecard['roic_health'] == 'moderate':
        score += 12

    # Trend bonus/penalty
    roe_direction = roe_analysis.get('direction')
    if roe_direction == 'improving':
        score += 5
    elif roe_direction == 'declining':
        score -= 5

    scorecard['overall_return_score'] = min(100, max(0, score))

    return scorecard


def get_returns_on_capital_analysis(workspace: Dict) -> Dict:
    """Main function to get complete returns on capital analysis"""

    metrics = extract_capital_metrics(workspace)
    returns = analyze_return_metrics(metrics)
    scorecard = calculate_return_scorecard(
        returns['roe_analysis'],
        returns['roa_analysis'],
        returns['roic_analysis']
    )

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'roe_analysis': returns['roe_analysis'],
        'roa_analysis': returns['roa_analysis'],
        'roic_analysis': returns['roic_analysis'],
        'return_scorecard': scorecard,
        'summary': {
            'roe_health': scorecard['roe_health'],
            'roa_health': scorecard['roa_health'],
            'roic_health': scorecard['roic_health'],
            'overall_return_score': scorecard['overall_return_score']
        }
    }
