"""Peer Comparison Analysis - Contextualize valuation and metrics vs peers"""

from typing import Dict, List, Optional


def analyze_peer_metrics(workspace: Dict) -> Dict:
    """Analyze company metrics relative to peers"""

    peers = workspace.get('overview', {}).get('peers', [])
    ticker = workspace.get('ticker')

    analysis = {
        'company_ticker': ticker,
        'peer_count': len(peers),
        'metric_rankings': {},
        'relative_valuation': {},
        'quality_comparison': {}
    }

    if not peers:
        return analysis

    # Extract company data
    company_data = workspace.get('overview', {}).get('company', {})

    # Key metrics to compare
    metrics = {
        'roe': [p.get('roe') for p in peers if p.get('roe')],
        'pe_ratio': [p.get('pe_ratio') for p in peers if p.get('pe_ratio')],
        'net_margin': [p.get('net_profit_margin') for p in peers if p.get('net_profit_margin')],
        'debt_to_equity': [p.get('debt_to_equity') for p in peers if p.get('debt_to_equity')],
    }

    # Calculate peer medians and company ranking
    for metric, values in metrics.items():
        if values:
            sorted_values = sorted(values)
            median = sorted_values[len(sorted_values)//2]
            avg = sum(values) / len(values)

            analysis['metric_rankings'][metric] = {
                'peer_median': median,
                'peer_average': avg,
                'peer_count': len(values),
                'rank_info': f'Company compares to {len(values)} peers'
            }

    return analysis


def calculate_relative_valuation(workspace: Dict) -> Dict:
    """Calculate relative valuation metrics"""

    assessment = {
        'premium_discount': {},
        'quality_vs_price': {},
        'investment_case': 'unknown'
    }

    company = workspace.get('overview', {}).get('company', {})
    peers = workspace.get('overview', {}).get('peers', [])

    if not peers or not company:
        return assessment

    # Get company PE and ROE
    company_pe = company.get('pe_ratio')
    company_roe = company.get('roe')

    if not peers:
        return assessment

    # Compare to peer PE
    peer_pes = [p.get('pe_ratio') for p in peers if p.get('pe_ratio')]
    if peer_pes and company_pe:
        avg_peer_pe = sum(peer_pes) / len(peer_pes)
        pe_discount = ((avg_peer_pe - company_pe) / avg_peer_pe * 100) if avg_peer_pe else 0

        assessment['premium_discount']['pe_comparison'] = {
            'company_pe': company_pe,
            'peer_avg_pe': avg_peer_pe,
            'discount_pct': pe_discount
        }

    # Quality vs price
    if company_roe:
        peer_roes = [p.get('roe') for p in peers if p.get('roe')]
        if peer_roes:
            avg_peer_roe = sum(peer_roes) / len(peer_roes)

            if company_pe and avg_peer_pe:
                roe_premium = ((company_roe - avg_peer_roe) / avg_peer_roe * 100) if avg_peer_roe else 0
                pe_discount_pct = pe_discount

                if roe_premium > 10 and pe_discount_pct > 10:
                    assessment['investment_case'] = 'attractive'
                elif roe_premium < -10 and pe_discount_pct < -10:
                    assessment['investment_case'] = 'concerning'
                else:
                    assessment['investment_case'] = 'fairly_valued'

    return assessment


def get_peer_comparison_analysis(workspace: Dict) -> Dict:
    """Main function for peer comparison"""

    metrics = analyze_peer_metrics(workspace)
    valuation = calculate_relative_valuation(workspace)

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'peer_metrics': metrics,
        'relative_valuation': valuation,
        'summary': {
            'peers_in_universe': metrics['peer_count'],
            'investment_case': valuation['investment_case'],
            'valuation_context': 'Company metrics contextualized vs peer group'
        }
    }
