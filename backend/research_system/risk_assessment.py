"""Risk Assessment - Comprehensive risk identification and evaluation"""

from typing import Dict, List


RISK_CATEGORIES = {
    'business_risk': {
        'description': 'Risks inherent to the business model and operations',
        'factors': ['Competition', 'Market share', 'Product obsolescence', 'Execution risk']
    },
    'financial_risk': {
        'description': 'Leverage, liquidity, and solvency risks',
        'factors': ['High debt', 'Low interest coverage', 'Tight liquidity', 'FCF concerns']
    },
    'currency_risk': {
        'description': 'Foreign exchange exposure affecting profits',
        'factors': ['Import costs', 'Export revenue', 'Foreign debt', 'Hedging gaps']
    },
    'commodity_risk': {
        'description': 'Exposure to commodity price volatility',
        'factors': ['Raw material costs', 'Oil/energy prices', 'Agricultural inputs']
    },
    'regulatory_risk': {
        'description': 'Changes in laws, regulations, or government policies',
        'factors': ['Tax changes', 'Environmental rules', 'Industry regulations', 'License risks']
    },
    'geopolitical_risk': {
        'description': 'Political, economic, or security risks in operating markets',
        'factors': ['Political instability', 'War/conflict', 'Economic sanctions', 'Trade tensions']
    },
    'customer_risk': {
        'description': 'Dependence on few customers',
        'factors': ['Top customer %', 'Contract terms', 'Customer concentration', 'Switching risk']
    },
    'supplier_risk': {
        'description': 'Dependence on key suppliers',
        'factors': ['Supply chain', 'Supplier concentration', 'Substitution risk']
    },
    'technology_risk': {
        'description': 'Disruption by new technology',
        'factors': ['Innovation disruption', 'Digital transformation', 'Legacy systems']
    },
    'management_risk': {
        'description': 'Quality and turnover of management',
        'factors': ['Key person dependency', 'Track record', 'Governance', 'Succession planning']
    },
    'liquidity_risk': {
        'description': 'Ability to trade shares at fair value',
        'factors': ['Trading volume', 'Bid-ask spread', 'Float size', 'Institutional holding']
    }
}


def assess_business_risk(workspace: Dict) -> Dict:
    """Assess business-specific risks"""

    assessment = {
        'risk_level': 'moderate',
        'factors': [],
        'score': 50
    }

    # Extract metrics
    market_cap = workspace.get('overview', {}).get('company', {}).get('market_cap')
    sector = workspace.get('overview', {}).get('company', {}).get('sector')

    # Commodity-heavy sectors have higher business risk
    high_risk_sectors = ['Fertilizer', 'Cement', 'Steel', 'Energy']
    if sector in high_risk_sectors:
        assessment['risk_level'] = 'elevated'
        assessment['factors'].append(f'{sector} sector - commodity exposure')
        assessment['score'] = 65

    return assessment


def assess_financial_risk(workspace: Dict) -> Dict:
    """Assess financial and leverage risks"""

    assessment = {
        'risk_level': 'low',
        'factors': [],
        'score': 30
    }

    financials = workspace.get('overview', {}).get('financials', {})

    # Check debt levels
    debt_to_equity = workspace.get('overview', {}).get('company', {}).get('debt_to_equity')

    if debt_to_equity and debt_to_equity > 1.0:
        assessment['risk_level'] = 'elevated'
        assessment['factors'].append(f'High leverage: D/E {debt_to_equity:.2f}')
        assessment['score'] = 70

    return assessment


def identify_key_risks(workspace: Dict) -> List[Dict]:
    """Identify and rank key risks"""

    risks = []

    # Business risk
    biz_risk = assess_business_risk(workspace)
    risks.append({
        'category': 'Business Risk',
        'level': biz_risk['risk_level'],
        'description': RISK_CATEGORIES['business_risk']['description'],
        'specific_risks': biz_risk['factors'],
        'score': biz_risk['score']
    })

    # Financial risk
    fin_risk = assess_financial_risk(workspace)
    risks.append({
        'category': 'Financial Risk',
        'level': fin_risk['risk_level'],
        'description': RISK_CATEGORIES['financial_risk']['description'],
        'specific_risks': fin_risk['factors'],
        'score': fin_risk['score']
    })

    # Sort by score (descending)
    risks.sort(key=lambda x: x['score'], reverse=True)

    return risks


def get_risk_assessment(workspace: Dict) -> Dict:
    """Main function to get risk assessment"""

    key_risks = identify_key_risks(workspace)

    # Overall risk score
    avg_risk_score = sum(r['score'] for r in key_risks) / len(key_risks) if key_risks else 50

    if avg_risk_score < 40:
        overall_risk = 'low'
    elif avg_risk_score < 60:
        overall_risk = 'moderate'
    elif avg_risk_score < 75:
        overall_risk = 'elevated'
    else:
        overall_risk = 'high'

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'key_risks': key_risks,
        'risk_assessment': {
            'overall_risk_level': overall_risk,
            'average_risk_score': avg_risk_score,
            'risk_categories': list(RISK_CATEGORIES.keys())
        },
        'summary': {
            'overall_risk_level': overall_risk,
            'top_risk': key_risks[0]['category'] if key_risks else 'unknown',
            'average_risk_score': avg_risk_score
        }
    }
