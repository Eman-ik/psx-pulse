"""Cash Flow Health Analysis - OCF, FCF, cash conversion quality"""

from typing import Dict, List, Optional, Tuple


def calculate_fcf(operating_cash_flow: Optional[float], capex: Optional[float]) -> Optional[float]:
    """Calculate Free Cash Flow (OCF - CapEx)"""
    if not operating_cash_flow or not capex:
        return None
    return operating_cash_flow - capex


def calculate_fcf_yield(fcf: Optional[float], market_cap: Optional[float]) -> Optional[float]:
    """Calculate FCF Yield (FCF / Market Cap * 100)"""
    if not fcf or not market_cap or market_cap <= 0:
        return None
    return (fcf / market_cap) * 100


def calculate_cash_conversion(operating_cash_flow: Optional[float], net_income: Optional[float]) -> Optional[float]:
    """Calculate Cash Conversion Ratio (OCF / Net Income * 100)"""
    if not operating_cash_flow or not net_income or net_income == 0:
        return None
    return (operating_cash_flow / net_income) * 100


def calculate_capex_to_revenue(capex: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """Calculate CapEx-to-Revenue ratio"""
    if not capex or not revenue or revenue <= 0:
        return None
    return (capex / revenue) * 100


def extract_cash_flow_metrics(workspace: Dict) -> Dict:
    """Extract cash flow data from workspace"""
    financials = workspace.get('overview', {}).get('financials', {})

    metrics = {
        'operating_cash_flow': None,
        'investing_cash_flow': None,
        'financing_cash_flow': None,
        'capex': None,
        'net_income': None,
        'revenue': None,
        'market_cap': None,
    }

    for key, series in financials.items():
        key_lower = key.lower()

        if 'operating' in key_lower and 'cash' in key_lower:
            metrics['operating_cash_flow'] = series
        elif 'investing' in key_lower and 'cash' in key_lower:
            metrics['investing_cash_flow'] = series
        elif 'financing' in key_lower and 'cash' in key_lower:
            metrics['financing_cash_flow'] = series
        elif 'capex' in key_lower or ('capital' in key_lower and 'expenditure' in key_lower):
            metrics['capex'] = series
        elif 'net' in key_lower and ('income' in key_lower or 'profit' in key_lower):
            metrics['net_income'] = series
        elif 'revenue' in key_lower:
            metrics['revenue'] = series

    # Market cap from overview
    overview = workspace.get('overview', {})
    if overview:
        # Try to get from issuer data or calculate from price * shares
        market_cap_series = financials.get('market_cap')
        if market_cap_series:
            metrics['market_cap'] = market_cap_series

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


def analyze_cash_generation(metrics: Dict) -> Dict:
    """Analyze operating cash flow and quality"""

    ocf_series = metrics.get('operating_cash_flow')
    ni_series = metrics.get('net_income')
    capex_series = metrics.get('capex')
    revenue_series = metrics.get('revenue')

    result = {
        'operating_cash_flow': {},
        'free_cash_flow': {},
        'cash_conversion': {},
        'capex_intensity': {}
    }

    # Operating Cash Flow Analysis
    if ocf_series:
        ocf_latest = get_latest_value(ocf_series)
        result['operating_cash_flow']['current'] = ocf_latest

        ocf_values = get_values_by_periods(ocf_series, 5)
        if len(ocf_values) >= 2:
            result['operating_cash_flow']['trend'] = ocf_values
            first_ocf = ocf_values[0][0]
            latest_ocf = ocf_values[-1][0]

            if first_ocf > 0:
                growth = ((latest_ocf / first_ocf) - 1) * 100
                result['operating_cash_flow']['growth_pct'] = growth
                result['operating_cash_flow']['direction'] = 'improving' if growth > 5 else 'declining' if growth < -5 else 'stable'

    # Free Cash Flow Analysis
    if ocf_series and capex_series:
        ocf_latest = get_latest_value(ocf_series)
        capex_latest = get_latest_value(capex_series)

        if ocf_latest and capex_latest:
            fcf = calculate_fcf(ocf_latest, capex_latest)
            result['free_cash_flow']['current'] = fcf

            ocf_values = get_values_by_periods(ocf_series, 5)
            capex_values = get_values_by_periods(capex_series, 5)

            if len(ocf_values) > 0 and len(capex_values) > 0:
                fcf_values = []
                for i, (ocf, period) in enumerate(ocf_values):
                    if i < len(capex_values):
                        capex = capex_values[i][0]
                        fcf_val = calculate_fcf(ocf, capex)
                        if fcf_val is not None:
                            fcf_values.append({'period': period, 'fcf': fcf_val})

                if len(fcf_values) >= 2:
                    result['free_cash_flow']['trend'] = fcf_values
                    first_fcf = fcf_values[0]['fcf']
                    latest_fcf = fcf_values[-1]['fcf']

                    if first_fcf > 0 and latest_fcf > 0:
                        fcf_growth = ((latest_fcf / first_fcf) - 1) * 100
                        result['free_cash_flow']['growth_pct'] = fcf_growth

                    result['free_cash_flow']['status'] = 'positive' if latest_fcf > 0 else 'negative'

    # Cash Conversion Quality
    if ocf_series and ni_series:
        ocf_latest = get_latest_value(ocf_series)
        ni_latest = get_latest_value(ni_series)

        if ocf_latest and ni_latest:
            conversion = calculate_cash_conversion(ocf_latest, ni_latest)
            result['cash_conversion']['current'] = conversion

            # Quality assessment
            if conversion and conversion >= 100:
                result['cash_conversion']['quality'] = 'excellent'
                result['cash_conversion']['note'] = 'OCF exceeds reported earnings - strong quality'
            elif conversion and conversion >= 80:
                result['cash_conversion']['quality'] = 'good'
                result['cash_conversion']['note'] = 'OCF closely tracking earnings'
            elif conversion and conversion >= 50:
                result['cash_conversion']['quality'] = 'moderate'
                result['cash_conversion']['note'] = 'Some divergence between profit and cash'
            else:
                result['cash_conversion']['quality'] = 'poor'
                result['cash_conversion']['note'] = 'Significant gap between profit and cash flow'

            # Trend analysis
            ocf_values = get_values_by_periods(ocf_series, 5)
            ni_values = get_values_by_periods(ni_series, 5)

            if len(ocf_values) > 0 and len(ni_values) > 0:
                conversion_values = []
                for i, (ocf, period) in enumerate(ocf_values):
                    if i < len(ni_values):
                        ni = ni_values[i][0]
                        conv_val = calculate_cash_conversion(ocf, ni)
                        if conv_val is not None:
                            conversion_values.append({'period': period, 'ratio': conv_val})

                if len(conversion_values) >= 2:
                    result['cash_conversion']['trend'] = conversion_values
                    first_conv = conversion_values[0]['ratio']
                    latest_conv = conversion_values[-1]['ratio']
                    change = latest_conv - first_conv
                    result['cash_conversion']['trend_direction'] = 'improving' if change > 2 else 'declining' if change < -2 else 'stable'

    # CapEx Intensity
    if capex_series and revenue_series:
        capex_latest = get_latest_value(capex_series)
        revenue_latest = get_latest_value(revenue_series)

        if capex_latest and revenue_latest:
            capex_intensity = calculate_capex_to_revenue(capex_latest, revenue_latest)
            result['capex_intensity']['current'] = capex_intensity

            # Intensity classification
            if capex_intensity and capex_intensity < 3:
                result['capex_intensity']['level'] = 'low'
            elif capex_intensity and capex_intensity < 8:
                result['capex_intensity']['level'] = 'moderate'
            else:
                result['capex_intensity']['level'] = 'high'

    return result


def calculate_cash_flow_scorecard(cash_gen: Dict) -> Dict:
    """Generate overall cash flow health scorecard"""

    scorecard = {
        'ocf_health': 'unknown',
        'fcf_health': 'unknown',
        'conversion_quality': 'unknown',
        'overall_cash_flow_score': 0,
        'recommendations': []
    }

    # OCF health
    ocf_current = cash_gen.get('operating_cash_flow', {}).get('current')
    ocf_direction = cash_gen.get('operating_cash_flow', {}).get('direction')

    if ocf_current is not None:
        if ocf_current > 0:
            if ocf_direction == 'improving':
                scorecard['ocf_health'] = 'excellent'
                scorecard['recommendations'].append('Operating cash flow strong and growing')
            else:
                scorecard['ocf_health'] = 'good'
                scorecard['recommendations'].append('Solid operating cash generation')
        else:
            scorecard['ocf_health'] = 'weak'
            scorecard['recommendations'].append('Negative operating cash flow - investigate operations')

    # FCF health
    fcf_current = cash_gen.get('free_cash_flow', {}).get('current')
    fcf_status = cash_gen.get('free_cash_flow', {}).get('status')

    if fcf_current is not None:
        if fcf_status == 'positive':
            scorecard['fcf_health'] = 'excellent'
            scorecard['recommendations'].append('Positive FCF available for dividends/debt reduction')
        else:
            scorecard['fcf_health'] = 'weak'
            scorecard['recommendations'].append('Negative FCF - CapEx exceeding operating cash')

    # Cash conversion quality
    conversion_quality = cash_gen.get('cash_conversion', {}).get('quality')
    if conversion_quality == 'excellent':
        scorecard['conversion_quality'] = 'excellent'
    elif conversion_quality == 'good':
        scorecard['conversion_quality'] = 'good'
    elif conversion_quality == 'moderate':
        scorecard['conversion_quality'] = 'moderate'
    else:
        scorecard['conversion_quality'] = 'weak'

    # Overall score (0-100)
    score = 0

    if scorecard['ocf_health'] == 'excellent':
        score += 35
    elif scorecard['ocf_health'] == 'good':
        score += 25
    elif scorecard['ocf_health'] == 'weak':
        score += 5

    if scorecard['fcf_health'] == 'excellent':
        score += 35
    elif scorecard['fcf_health'] == 'good':
        score += 25
    elif scorecard['fcf_health'] == 'weak':
        score += 5

    if scorecard['conversion_quality'] == 'excellent':
        score += 30
    elif scorecard['conversion_quality'] == 'good':
        score += 22
    elif scorecard['conversion_quality'] == 'moderate':
        score += 12
    else:
        score += 3

    scorecard['overall_cash_flow_score'] = min(100, score)

    return scorecard


def get_cash_flow_health_analysis(workspace: Dict) -> Dict:
    """Main function to get complete cash flow health analysis"""

    metrics = extract_cash_flow_metrics(workspace)
    cash_gen = analyze_cash_generation(metrics)
    scorecard = calculate_cash_flow_scorecard(cash_gen)

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'operating_cash_flow_analysis': cash_gen['operating_cash_flow'],
        'free_cash_flow_analysis': cash_gen['free_cash_flow'],
        'cash_conversion_analysis': cash_gen['cash_conversion'],
        'capex_intensity_analysis': cash_gen['capex_intensity'],
        'cash_flow_scorecard': scorecard,
        'summary': {
            'ocf_health': scorecard['ocf_health'],
            'fcf_health': scorecard['fcf_health'],
            'conversion_quality': scorecard['conversion_quality'],
            'overall_cash_flow_score': scorecard['overall_cash_flow_score']
        }
    }
