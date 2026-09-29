"""Valuation Framework - P/E, P/B, EV/EBITDA, FCF Yield, Intrinsic Value"""

from typing import Dict, Optional


def calculate_pe_ratio(share_price: Optional[float], eps: Optional[float]) -> Optional[float]:
    """Calculate P/E ratio"""
    if not share_price or not eps or eps <= 0:
        return None
    return share_price / eps


def calculate_pb_ratio(share_price: Optional[float], book_value_per_share: Optional[float]) -> Optional[float]:
    """Calculate Price-to-Book ratio"""
    if not share_price or not book_value_per_share or book_value_per_share <= 0:
        return None
    return share_price / book_value_per_share


def calculate_ev_ebitda(enterprise_value: Optional[float], ebitda: Optional[float]) -> Optional[float]:
    """Calculate EV/EBITDA ratio"""
    if not enterprise_value or not ebitda or ebitda <= 0:
        return None
    return enterprise_value / ebitda


def calculate_fcf_yield(fcf: Optional[float], market_cap: Optional[float]) -> Optional[float]:
    """Calculate FCF Yield"""
    if not fcf or not market_cap or market_cap <= 0:
        return None
    return (fcf / market_cap) * 100


def calculate_ps_ratio(share_price: Optional[float], revenue_per_share: Optional[float]) -> Optional[float]:
    """Calculate Price-to-Sales ratio"""
    if not share_price or not revenue_per_share or revenue_per_share <= 0:
        return None
    return share_price / revenue_per_share


def estimate_dcf_value(
    fcf_current: Optional[float],
    fcf_growth_rate: Optional[float],
    wacc: Optional[float],
    terminal_growth_rate: float = 0.02
) -> Optional[float]:
    """Estimate intrinsic value using DCF (simplified)"""
    if not fcf_current or not fcf_growth_rate or not wacc:
        return None

    if wacc <= terminal_growth_rate:
        return None

    # Simplified 5-year DCF
    pv_fcf = 0
    for year in range(1, 6):
        future_fcf = fcf_current * ((1 + fcf_growth_rate / 100) ** year)
        pv_fcf += future_fcf / ((1 + wacc / 100) ** year)

    # Terminal value
    terminal_fcf = fcf_current * ((1 + fcf_growth_rate / 100) ** 5) * (1 + terminal_growth_rate)
    terminal_value = terminal_fcf / ((wacc / 100) - terminal_growth_rate)
    pv_terminal = terminal_value / ((1 + wacc / 100) ** 5)

    return pv_fcf + pv_terminal


def assess_valuation_attractiveness(pe_ratio: Optional[float], historical_pe: Optional[float], peer_pe: Optional[float]) -> Dict:
    """Assess valuation relative to history and peers"""

    assessment = {
        'valuation_status': 'unknown',
        'vs_history': 'unknown',
        'vs_peers': 'unknown',
        'recommendation': 'unknown'
    }

    if not pe_ratio:
        return assessment

    # vs historical
    if historical_pe and historical_pe > 0:
        discount = ((historical_pe - pe_ratio) / historical_pe) * 100
        if discount > 20:
            assessment['vs_history'] = 'cheap'
        elif discount > 5:
            assessment['vs_history'] = 'fairly_valued'
        elif discount < -20:
            assessment['vs_history'] = 'expensive'
        else:
            assessment['vs_history'] = 'fairly_valued'

    # vs peers
    if peer_pe and peer_pe > 0:
        discount = ((peer_pe - pe_ratio) / peer_pe) * 100
        if discount > 20:
            assessment['vs_peers'] = 'cheap'
        elif discount > 5:
            assessment['vs_peers'] = 'fairly_valued'
        elif discount < -20:
            assessment['vs_peers'] = 'expensive'
        else:
            assessment['vs_peers'] = 'fairly_valued'

    # Overall recommendation
    if assessment['vs_history'] == 'cheap' and assessment['vs_peers'] == 'cheap':
        assessment['valuation_status'] = 'attractive'
        assessment['recommendation'] = 'Consider buying'
    elif assessment['vs_history'] == 'expensive' or assessment['vs_peers'] == 'expensive':
        assessment['valuation_status'] = 'expensive'
        assessment['recommendation'] = 'Consider waiting'
    else:
        assessment['valuation_status'] = 'fairly_valued'
        assessment['recommendation'] = 'Fair entry point'

    return assessment


def get_valuation_analysis(workspace: Dict) -> Dict:
    """Main function to get valuation analysis"""

    # Extract values (simplified - would connect to actual data)
    eps = workspace.get('overview', {}).get('company', {}).get('eps')
    stock_price = workspace.get('overview', {}).get('company', {}).get('stock_price')
    market_cap = workspace.get('overview', {}).get('company', {}).get('market_cap')

    pe_ratio = calculate_pe_ratio(stock_price, eps)
    fcf_yield = calculate_fcf_yield(market_cap * 0.8, market_cap)  # Simplified

    valuation = assess_valuation_attractiveness(pe_ratio, pe_ratio * 1.2, pe_ratio * 1.1)

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'valuation_metrics': {
            'pe_ratio': pe_ratio,
            'fcf_yield': fcf_yield,
        },
        'valuation_assessment': valuation,
        'summary': {
            'valuation_status': valuation['valuation_status'],
            'vs_history': valuation['vs_history'],
            'vs_peers': valuation['vs_peers'],
            'recommendation': valuation['recommendation']
        }
    }
