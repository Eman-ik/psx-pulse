"""Working Capital Analysis - Receivables, Inventory, Payables, Cash Conversion Cycle"""

from typing import Dict, List, Optional, Tuple


def calculate_receivable_days(receivables: Optional[float], revenue: Optional[float], days: int = 365) -> Optional[float]:
    """Calculate Days Sales Outstanding (Receivable Days)"""
    if not receivables or not revenue or revenue <= 0:
        return None
    return (receivables / revenue) * days


def calculate_inventory_days(inventory: Optional[float], cost_of_goods_sold: Optional[float], days: int = 365) -> Optional[float]:
    """Calculate Days Inventory Outstanding"""
    if not inventory or not cost_of_goods_sold or cost_of_goods_sold <= 0:
        return None
    return (inventory / cost_of_goods_sold) * days


def calculate_payable_days(payables: Optional[float], cost_of_goods_sold: Optional[float], days: int = 365) -> Optional[float]:
    """Calculate Days Payable Outstanding"""
    if not payables or not cost_of_goods_sold or cost_of_goods_sold <= 0:
        return None
    return (payables / cost_of_goods_sold) * days


def calculate_cash_conversion_cycle(
    receivable_days: Optional[float],
    inventory_days: Optional[float],
    payable_days: Optional[float]
) -> Optional[float]:
    """Calculate Cash Conversion Cycle (DIO + DSO - DPO)"""
    if receivable_days is None or inventory_days is None or payable_days is None:
        return None
    return receivable_days + inventory_days - payable_days


def extract_working_capital_metrics(workspace: Dict) -> Dict:
    """Extract working capital components from workspace"""
    financials = workspace.get('overview', {}).get('financials', {})

    metrics = {
        'receivables': None,
        'inventory': None,
        'payables': None,
        'revenue': None,
        'cogs': None,
    }

    for key, series in financials.items():
        key_lower = key.lower()

        if 'receivable' in key_lower:
            metrics['receivables'] = series
        elif 'inventory' in key_lower:
            metrics['inventory'] = series
        elif 'payable' in key_lower:
            metrics['payables'] = series
        elif 'revenue' in key_lower:
            metrics['revenue'] = series
        elif 'cogs' in key_lower or ('cost' in key_lower and 'goods' in key_lower):
            metrics['cogs'] = series

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


def analyze_working_capital_components(metrics: Dict) -> Dict:
    """Analyze working capital components"""

    result = {
        'receivable_days': {},
        'inventory_days': {},
        'payable_days': {},
        'cash_conversion_cycle': {}
    }

    receivables_series = metrics.get('receivables')
    inventory_series = metrics.get('inventory')
    payables_series = metrics.get('payables')
    revenue_series = metrics.get('revenue')
    cogs_series = metrics.get('cogs')

    # Calculate current values
    rec_latest = get_latest_value(receivables_series)
    inv_latest = get_latest_value(inventory_series)
    pay_latest = get_latest_value(payables_series)
    rev_latest = get_latest_value(revenue_series)
    cogs_latest = get_latest_value(cogs_series)

    if rec_latest and rev_latest:
        rec_days = calculate_receivable_days(rec_latest, rev_latest)
        result['receivable_days']['current'] = rec_days

    if inv_latest and cogs_latest:
        inv_days = calculate_inventory_days(inv_latest, cogs_latest)
        result['inventory_days']['current'] = inv_days

    if pay_latest and cogs_latest:
        pay_days = calculate_payable_days(pay_latest, cogs_latest)
        result['payable_days']['current'] = pay_days

    # Calculate CCC
    if result['receivable_days'].get('current') and result['inventory_days'].get('current') and result['payable_days'].get('current'):
        ccc = calculate_cash_conversion_cycle(
            result['receivable_days']['current'],
            result['inventory_days']['current'],
            result['payable_days']['current']
        )
        result['cash_conversion_cycle']['current'] = ccc

    # Trend analysis
    if receivables_series and revenue_series and cogs_series:
        rec_values = get_values_by_periods(receivables_series, 5)
        rev_values = get_values_by_periods(revenue_series, 5)
        cogs_values = get_values_by_periods(cogs_series, 5)
        inv_values = get_values_by_periods(inventory_series, 5) if inventory_series else []
        pay_values = get_values_by_periods(payables_series, 5) if payables_series else []

        ccc_values = []
        for i in range(min(len(rec_values), len(rev_values), len(cogs_values))):
            rec_days = calculate_receivable_days(rec_values[i][0], rev_values[i][0])

            inv_days = None
            if i < len(inv_values):
                inv_days = calculate_inventory_days(inv_values[i][0], cogs_values[i][0])
            else:
                inv_days = 0

            pay_days = None
            if i < len(pay_values):
                pay_days = calculate_payable_days(pay_values[i][0], cogs_values[i][0])
            else:
                pay_days = 0

            if rec_days and inv_days is not None and pay_days is not None:
                ccc = rec_days + inv_days - pay_days
                ccc_values.append({'period': rec_values[i][1], 'ccc': ccc})

        if len(ccc_values) >= 2:
            result['cash_conversion_cycle']['trend'] = ccc_values
            first_ccc = ccc_values[0]['ccc']
            latest_ccc = ccc_values[-1]['ccc']
            change = latest_ccc - first_ccc
            result['cash_conversion_cycle']['direction'] = 'improving' if change < -5 else 'deteriorating' if change > 5 else 'stable'

    return result


def calculate_working_capital_scorecard(wc: Dict) -> Dict:
    """Generate working capital efficiency scorecard"""

    scorecard = {
        'receivable_health': 'unknown',
        'inventory_health': 'unknown',
        'payable_health': 'unknown',
        'ccc_health': 'unknown',
        'overall_wc_score': 0,
        'recommendations': []
    }

    # Receivable health (lower is better - faster collection)
    rec_days = wc.get('receivable_days', {}).get('current')
    if rec_days is not None:
        if rec_days < 30:
            scorecard['receivable_health'] = 'excellent'
        elif rec_days < 45:
            scorecard['receivable_health'] = 'good'
        elif rec_days < 60:
            scorecard['receivable_health'] = 'moderate'
        else:
            scorecard['receivable_health'] = 'weak'
            scorecard['recommendations'].append('High receivable days - cash collection slowdown')

    # Inventory health
    inv_days = wc.get('inventory_days', {}).get('current')
    if inv_days is not None:
        if inv_days < 30:
            scorecard['inventory_health'] = 'excellent'
        elif inv_days < 60:
            scorecard['inventory_health'] = 'good'
        elif inv_days < 90:
            scorecard['inventory_health'] = 'moderate'
        else:
            scorecard['inventory_health'] = 'weak'
            scorecard['recommendations'].append('High inventory days - potential obsolescence or slow sales')

    # CCC health (lower is better - less cash tied up)
    ccc = wc.get('cash_conversion_cycle', {}).get('current')
    if ccc is not None:
        if ccc < 30:
            scorecard['ccc_health'] = 'excellent'
            scorecard['recommendations'].append('Excellent CCC - efficient working capital management')
        elif ccc < 60:
            scorecard['ccc_health'] = 'good'
        elif ccc < 90:
            scorecard['ccc_health'] = 'moderate'
        else:
            scorecard['ccc_health'] = 'weak'
            scorecard['recommendations'].append('Long CCC - significant cash tied up in operations')

    # Overall score
    score = 0

    if scorecard['receivable_health'] == 'excellent':
        score += 30
    elif scorecard['receivable_health'] == 'good':
        score += 22
    elif scorecard['receivable_health'] == 'moderate':
        score += 12

    if scorecard['inventory_health'] == 'excellent':
        score += 30
    elif scorecard['inventory_health'] == 'good':
        score += 22
    elif scorecard['inventory_health'] == 'moderate':
        score += 12

    if scorecard['ccc_health'] == 'excellent':
        score += 40
    elif scorecard['ccc_health'] == 'good':
        score += 28
    elif scorecard['ccc_health'] == 'moderate':
        score += 15

    scorecard['overall_wc_score'] = min(100, score)

    return scorecard


def get_working_capital_analysis(workspace: Dict) -> Dict:
    """Main function to get working capital analysis"""

    metrics = extract_working_capital_metrics(workspace)
    wc = analyze_working_capital_components(metrics)
    scorecard = calculate_working_capital_scorecard(wc)

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'receivable_days_analysis': wc['receivable_days'],
        'inventory_days_analysis': wc['inventory_days'],
        'payable_days_analysis': wc['payable_days'],
        'cash_conversion_cycle_analysis': wc['cash_conversion_cycle'],
        'working_capital_scorecard': scorecard,
        'summary': {
            'receivable_health': scorecard['receivable_health'],
            'inventory_health': scorecard['inventory_health'],
            'ccc_health': scorecard['ccc_health'],
            'overall_wc_score': scorecard['overall_wc_score']
        }
    }
