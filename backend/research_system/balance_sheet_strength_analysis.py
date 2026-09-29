"""Balance Sheet Strength Analysis - Debt, liquidity, and solvency ratios"""

from typing import Dict, List, Optional, Tuple


def calculate_debt_to_equity(debt: Optional[float], equity: Optional[float]) -> Optional[float]:
    """Calculate Debt-to-Equity ratio"""
    if not debt or not equity or equity <= 0:
        return None
    return debt / equity


def calculate_debt_to_ebitda(debt: Optional[float], ebitda: Optional[float]) -> Optional[float]:
    """Calculate Debt-to-EBITDA ratio"""
    if not debt or not ebitda or ebitda <= 0:
        return None
    return debt / ebitda


def calculate_interest_coverage(ebit: Optional[float], interest_expense: Optional[float]) -> Optional[float]:
    """Calculate Interest Coverage ratio (EBIT / Finance Cost)"""
    if not ebit or not interest_expense or interest_expense <= 0:
        return None
    return ebit / interest_expense


def calculate_current_ratio(current_assets: Optional[float], current_liabilities: Optional[float]) -> Optional[float]:
    """Calculate Current Ratio"""
    if not current_assets or not current_liabilities or current_liabilities <= 0:
        return None
    return current_assets / current_liabilities


def calculate_quick_ratio(
    cash: Optional[float],
    receivables: Optional[float],
    current_liabilities: Optional[float]
) -> Optional[float]:
    """Calculate Quick Ratio (acid-test ratio)"""
    quick_assets = (cash or 0) + (receivables or 0)
    if not quick_assets or not current_liabilities or current_liabilities <= 0:
        return None
    return quick_assets / current_liabilities


def extract_balance_sheet_metrics(workspace: Dict) -> Dict:
    """Extract debt, equity, assets, liabilities from workspace"""
    financials = workspace.get('overview', {}).get('financials', {})

    metrics = {
        'debt': None,
        'equity': None,
        'current_assets': None,
        'current_liabilities': None,
        'cash': None,
        'receivables': None,
        'inventory': None,
        'ppe': None,
        'total_assets': None,
        'ebitda': None,
        'operating_profit': None,
        'interest_expense': None,
    }

    for key, series in financials.items():
        key_lower = key.lower()

        if 'debt' in key_lower or ('long' in key_lower and 'term' in key_lower):
            metrics['debt'] = series
        elif 'equity' in key_lower or 'shareholder' in key_lower:
            metrics['equity'] = series
        elif 'current' in key_lower and 'asset' in key_lower:
            metrics['current_assets'] = series
        elif 'current' in key_lower and 'liabil' in key_lower:
            metrics['current_liabilities'] = series
        elif 'cash' in key_lower:
            metrics['cash'] = series
        elif 'receivable' in key_lower:
            metrics['receivables'] = series
        elif 'inventory' in key_lower:
            metrics['inventory'] = series
        elif 'ppe' in key_lower or ('property' in key_lower and 'plant' in key_lower):
            metrics['ppe'] = series
        elif 'total' in key_lower and 'asset' in key_lower:
            metrics['total_assets'] = series
        elif 'ebitda' in key_lower:
            metrics['ebitda'] = series
        elif 'operating' in key_lower and 'profit' in key_lower:
            metrics['operating_profit'] = series
        elif 'interest' in key_lower and ('expense' in key_lower or 'cost' in key_lower):
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


def analyze_leverage(metrics: Dict) -> Dict:
    """Analyze debt levels and leverage"""

    debt_series = metrics.get('debt')
    equity_series = metrics.get('equity')
    ebitda_series = metrics.get('ebitda')
    operating_profit_series = metrics.get('operating_profit')
    interest_expense_series = metrics.get('interest_expense')

    result = {
        'debt_to_equity': {},
        'debt_to_ebitda': {},
        'interest_coverage': {},
        'debt_trend': {}
    }

    # Debt-to-Equity
    if debt_series and equity_series:
        debt_latest = get_latest_value(debt_series)
        equity_latest = get_latest_value(equity_series)

        if debt_latest is not None and equity_latest:
            de = calculate_debt_to_equity(debt_latest, equity_latest)
            result['debt_to_equity']['current'] = de

            # Trend analysis
            debt_values = get_values_by_periods(debt_series, 5)
            equity_values = get_values_by_periods(equity_series, 5)

            if len(debt_values) > 0:
                de_values = []
                for i, (debt, period) in enumerate(debt_values):
                    if i < len(equity_values):
                        eq = equity_values[i][0]
                        de_val = calculate_debt_to_equity(debt, eq)
                        if de_val is not None:
                            de_values.append({'period': period, 'ratio': de_val})

                if len(de_values) >= 2:
                    result['debt_to_equity']['trend'] = de_values
                    first_de = de_values[0]['ratio']
                    latest_de = de_values[-1]['ratio']
                    change = latest_de - first_de
                    result['debt_to_equity']['direction'] = 'increasing' if change > 0.1 else 'decreasing' if change < -0.1 else 'stable'
                    result['debt_to_equity']['change'] = change

    # Debt-to-EBITDA
    if debt_series and ebitda_series:
        debt_latest = get_latest_value(debt_series)
        ebitda_latest = get_latest_value(ebitda_series)

        if debt_latest is not None and ebitda_latest:
            de_ebitda = calculate_debt_to_ebitda(debt_latest, ebitda_latest)
            result['debt_to_ebitda']['current'] = de_ebitda

    # Interest Coverage
    if operating_profit_series and interest_expense_series:
        op_latest = get_latest_value(operating_profit_series)
        int_latest = get_latest_value(interest_expense_series)

        if op_latest and int_latest:
            ic = calculate_interest_coverage(op_latest, int_latest)
            result['interest_coverage']['current'] = ic

    return result


def analyze_liquidity(metrics: Dict) -> Dict:
    """Analyze liquidity and short-term solvency"""

    current_assets_series = metrics.get('current_assets')
    current_liab_series = metrics.get('current_liabilities')
    cash_series = metrics.get('cash')
    receivables_series = metrics.get('receivables')

    result = {
        'current_ratio': {},
        'quick_ratio': {},
        'liquidity_trend': {}
    }

    # Current Ratio
    if current_assets_series and current_liab_series:
        ca_latest = get_latest_value(current_assets_series)
        cl_latest = get_latest_value(current_liab_series)

        if ca_latest and cl_latest:
            cr = calculate_current_ratio(ca_latest, cl_latest)
            result['current_ratio']['current'] = cr

            # Healthy current ratio is typically 1.5-3.0
            if cr and cr >= 1.5:
                result['current_ratio']['health'] = 'healthy'
            elif cr and cr >= 1.0:
                result['current_ratio']['health'] = 'adequate'
            else:
                result['current_ratio']['health'] = 'concerning'

    # Quick Ratio
    if cash_series and receivables_series and current_liab_series:
        cash_latest = get_latest_value(cash_series)
        rec_latest = get_latest_value(receivables_series)
        cl_latest = get_latest_value(current_liab_series)

        if cl_latest:
            qr = calculate_quick_ratio(cash_latest, rec_latest, cl_latest)
            result['quick_ratio']['current'] = qr

            # Healthy quick ratio is typically >= 1.0
            if qr and qr >= 1.0:
                result['quick_ratio']['health'] = 'healthy'
            elif qr and qr >= 0.5:
                result['quick_ratio']['health'] = 'adequate'
            else:
                result['quick_ratio']['health'] = 'concerning'

    return result


def calculate_balance_sheet_scorecard(leverage: Dict, liquidity: Dict) -> Dict:
    """Generate overall balance sheet strength scorecard"""

    scorecard = {
        'leverage_health': 'unknown',
        'liquidity_health': 'unknown',
        'overall_balance_sheet_score': 0,
        'financial_risk': 'low',
        'recommendations': []
    }

    # Leverage health based on D/E ratio
    de_ratio = leverage.get('debt_to_equity', {}).get('current')
    if de_ratio is not None:
        if de_ratio < 0.5:
            scorecard['leverage_health'] = 'excellent'
            scorecard['recommendations'].append('Conservative debt levels - strong balance sheet')
        elif de_ratio < 1.0:
            scorecard['leverage_health'] = 'good'
            scorecard['recommendations'].append('Moderate leverage - manageable debt')
        elif de_ratio < 1.5:
            scorecard['leverage_health'] = 'moderate'
            scorecard['recommendations'].append('Elevated leverage - monitor debt trends')
        else:
            scorecard['leverage_health'] = 'weak'
            scorecard['recommendations'].append('High leverage - increased financial risk')

    # Trend check
    de_direction = leverage.get('debt_to_equity', {}).get('direction')
    if de_direction == 'increasing':
        scorecard['recommendations'].append('Debt levels increasing - investigate reasons')
    elif de_direction == 'decreasing':
        scorecard['recommendations'].append('Debt decreasing - positive deleveraging trend')

    # Liquidity health
    current_ratio_health = liquidity.get('current_ratio', {}).get('health')
    quick_ratio_health = liquidity.get('quick_ratio', {}).get('health')

    if current_ratio_health == 'healthy' or quick_ratio_health == 'healthy':
        scorecard['liquidity_health'] = 'healthy'
    elif current_ratio_health == 'adequate' or quick_ratio_health == 'adequate':
        scorecard['liquidity_health'] = 'adequate'
    else:
        scorecard['liquidity_health'] = 'concerning'

    # Interest coverage check
    ic_current = leverage.get('interest_coverage', {}).get('current')
    if ic_current is not None:
        if ic_current > 5.0:
            scorecard['recommendations'].append('Strong interest coverage - comfortable debt servicing')
        elif ic_current < 2.0:
            scorecard['recommendations'].append('Weak interest coverage - debt servicing at risk')

    # Overall score (0-100)
    score = 0

    if scorecard['leverage_health'] == 'excellent':
        score += 35
    elif scorecard['leverage_health'] == 'good':
        score += 26
    elif scorecard['leverage_health'] == 'moderate':
        score += 15
    elif scorecard['leverage_health'] == 'weak':
        score += 5

    if scorecard['liquidity_health'] == 'healthy':
        score += 35
    elif scorecard['liquidity_health'] == 'adequate':
        score += 22
    elif scorecard['liquidity_health'] == 'concerning':
        score += 8

    if ic_current is not None:
        if ic_current > 5.0:
            score += 30
        elif ic_current > 2.0:
            score += 20
        else:
            score += 5

    # Financial risk assessment
    if score >= 80:
        scorecard['financial_risk'] = 'low'
    elif score >= 60:
        scorecard['financial_risk'] = 'moderate'
    elif score >= 40:
        scorecard['financial_risk'] = 'elevated'
    else:
        scorecard['financial_risk'] = 'high'

    scorecard['overall_balance_sheet_score'] = min(100, score)

    return scorecard


def get_balance_sheet_strength_analysis(workspace: Dict) -> Dict:
    """Main function to get complete balance sheet strength analysis"""

    metrics = extract_balance_sheet_metrics(workspace)
    leverage = analyze_leverage(metrics)
    liquidity = analyze_liquidity(metrics)
    scorecard = calculate_balance_sheet_scorecard(leverage, liquidity)

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'leverage_analysis': leverage,
        'liquidity_analysis': liquidity,
        'balance_sheet_scorecard': scorecard,
        'summary': {
            'leverage_health': scorecard['leverage_health'],
            'liquidity_health': scorecard['liquidity_health'],
            'financial_risk': scorecard['financial_risk'],
            'overall_balance_sheet_score': scorecard['overall_balance_sheet_score']
        }
    }
