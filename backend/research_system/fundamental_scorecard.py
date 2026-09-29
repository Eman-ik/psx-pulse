"""Normalized Fundamental Scorecard - Systematic quantitative model of company quality"""

from typing import Dict, Optional


# Sector-adjusted scoring weights
SECTOR_WEIGHTS = {
    'FERTILIZER': {
        'revenue_growth': 0.07,
        'eps_growth': 0.08,
        'roe': 0.08,
        'roic': 0.08,
        'margins': 0.07,
        'cash_flow_quality': 0.10,
        'balance_sheet': 0.10,
        'earnings_stability': 0.08,
        'dividend_quality': 0.07,
        'valuation': 0.12,
        'governance': 0.08,
        'business_quality': 0.02
    },
    'CEMENT': {
        'revenue_growth': 0.06,
        'eps_growth': 0.07,
        'roe': 0.09,
        'roic': 0.09,
        'margins': 0.08,
        'cash_flow_quality': 0.09,
        'balance_sheet': 0.12,
        'earnings_stability': 0.07,
        'dividend_quality': 0.06,
        'valuation': 0.13,
        'governance': 0.07,
        'business_quality': 0.02
    }
}


def get_sector_weights(sector: Optional[str]) -> Dict:
    """Get sector-adjusted weights"""
    if sector and sector.upper() in SECTOR_WEIGHTS:
        return SECTOR_WEIGHTS[sector.upper()]
    # Default weights
    return SECTOR_WEIGHTS['FERTILIZER']


def score_revenue_growth(growth_rate: Optional[float]) -> float:
    """Score revenue growth (0-10 scale)"""
    if not growth_rate:
        return 5.0

    if growth_rate > 20:
        return 10.0
    elif growth_rate > 15:
        return 9.0
    elif growth_rate > 10:
        return 8.0
    elif growth_rate > 5:
        return 6.0
    elif growth_rate > 0:
        return 4.0
    else:
        return 2.0


def score_roe(roe: Optional[float]) -> float:
    """Score Return on Equity (0-10 scale)"""
    if not roe:
        return 5.0

    if roe > 25:
        return 10.0
    elif roe > 20:
        return 9.0
    elif roe > 15:
        return 8.0
    elif roe > 10:
        return 6.0
    elif roe > 5:
        return 4.0
    else:
        return 2.0


def score_valuation(pe_ratio: Optional[float], growth_rate: Optional[float]) -> float:
    """Score valuation (0-10 scale) - PEG ratio concept"""
    if not pe_ratio or not growth_rate or growth_rate <= 0:
        return 5.0

    peg = pe_ratio / growth_rate if growth_rate > 0 else pe_ratio

    if peg < 0.8:
        return 10.0
    elif peg < 1.0:
        return 8.0
    elif peg < 1.5:
        return 6.0
    elif peg < 2.0:
        return 4.0
    else:
        return 2.0


def score_balance_sheet(debt_to_equity: Optional[float], interest_coverage: Optional[float]) -> float:
    """Score balance sheet strength (0-10 scale)"""
    if not debt_to_equity and not interest_coverage:
        return 5.0

    score = 5.0

    if debt_to_equity:
        if debt_to_equity < 0.5:
            score += 2.5
        elif debt_to_equity < 1.0:
            score += 1.5
        elif debt_to_equity > 1.5:
            score -= 2.0

    if interest_coverage:
        if interest_coverage > 5:
            score += 2.5
        elif interest_coverage < 2:
            score -= 2.0

    return min(10.0, max(0.0, score))


def score_cash_flow_quality(ocf_to_ni: Optional[float]) -> float:
    """Score cash flow quality (0-10 scale)"""
    if not ocf_to_ni:
        return 5.0

    if ocf_to_ni > 100:
        return 10.0
    elif ocf_to_ni > 80:
        return 8.0
    elif ocf_to_ni > 60:
        return 6.0
    elif ocf_to_ni > 40:
        return 4.0
    else:
        return 2.0


def calculate_fundamental_score(workspace: Dict) -> Dict:
    """Calculate comprehensive fundamental scorecard"""

    company = workspace.get('overview', {}).get('company', {})
    sector = company.get('sector')
    weights = get_sector_weights(sector)

    # Extract metrics
    revenue_growth = company.get('revenue_growth', 0)
    eps_growth = company.get('eps_growth', 0)
    roe = company.get('roe', 0)
    roic = company.get('roic', 0)
    net_margin = company.get('net_margin', 0)
    pe_ratio = company.get('pe_ratio', 0)
    debt_to_equity = company.get('debt_to_equity', 0)

    # Score each component
    scores = {
        'revenue_growth': score_revenue_growth(revenue_growth),
        'eps_growth': score_revenue_growth(eps_growth),
        'roe': score_roe(roe),
        'roic': score_roe(roic),
        'margins': score_revenue_growth(net_margin),
        'cash_flow_quality': 6.0,  # Placeholder
        'balance_sheet': score_balance_sheet(debt_to_equity, None),
        'earnings_stability': 6.0,  # Placeholder
        'dividend_quality': 6.0,  # Placeholder
        'valuation': score_valuation(pe_ratio, revenue_growth),
        'governance': 6.0,  # Placeholder
        'business_quality': 6.0  # Placeholder
    }

    # Calculate weighted score
    total_score = 0.0
    for component, weight in weights.items():
        component_score = scores.get(component, 5.0)
        total_score += component_score * weight

    # Overall rating
    if total_score >= 8.0:
        rating = 'Exceptional'
    elif total_score >= 7.0:
        rating = 'Strong'
    elif total_score >= 6.0:
        rating = 'Good'
    elif total_score >= 5.0:
        rating = 'Fair'
    else:
        rating = 'Weak'

    return {
        'component_scores': scores,
        'weighted_scores': {k: scores[k] * weights[k] for k in scores},
        'total_score': round(total_score, 1),
        'overall_rating': rating,
        'weights_used': weights
    }


def get_fundamental_scorecard(workspace: Dict) -> Dict:
    """Main function for fundamental scorecard"""

    scorecard = calculate_fundamental_score(workspace)

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'fundamental_scorecard': scorecard,
        'summary': {
            'total_score': scorecard['total_score'],
            'overall_rating': scorecard['overall_rating'],
            'sector': workspace.get('overview', {}).get('company', {}).get('sector', 'Unknown')
        }
    }
