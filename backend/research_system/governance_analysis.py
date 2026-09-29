"""Management & Corporate Governance Analysis - Risk assessment of governance quality"""

from typing import Dict, List


GOVERNANCE_RISK_FACTORS = {
    'sponsor_ownership': {
        'description': 'Sponsor/promoter ownership concentration',
        'high_risk': '< 10% or > 70%',
        'optimal': '25-50%'
    },
    'related_party_transactions': {
        'description': 'RPT scrutiny and transparency',
        'risk_indicator': 'Significant undisclosed RPT'
    },
    'dilution_history': {
        'description': 'Share dilution pattern',
        'risk_indicator': 'Repeated rights issues or large bonus shares'
    },
    'audit_quality': {
        'description': 'Auditor changes and qualifications',
        'risk_indicator': 'Frequent auditor changes or qualified opinions'
    },
    'regulatory_compliance': {
        'description': 'Regulatory penalties and late filings',
        'risk_indicator': 'Repeated late filings or regulatory breaches'
    },
    'insider_transactions': {
        'description': 'Insider selling/buying patterns',
        'risk_indicator': 'Consistent insider selling or buying'
    },
    'dividend_consistency': {
        'description': 'Dividend payment consistency',
        'positive_indicator': 'Consistent dividend increases'
    }
}


def assess_ownership_structure(workspace: Dict) -> Dict:
    """Assess ownership concentration and control structure"""

    assessment = {
        'sponsor_concentration': 'unknown',
        'free_float': None,
        'public_holding': None,
        'concentration_risk': 'unknown'
    }

    company = workspace.get('overview', {}).get('company', {})
    free_float = company.get('free_float')

    if free_float:
        assessment['free_float'] = free_float
        sponsor_hold = 100 - free_float
        assessment['public_holding'] = free_float

        if free_float < 20:
            assessment['concentration_risk'] = 'high'
            assessment['sponsor_concentration'] = 'very_concentrated'
        elif free_float < 40:
            assessment['concentration_risk'] = 'moderate'
            assessment['sponsor_concentration'] = 'concentrated'
        else:
            assessment['concentration_risk'] = 'low'
            assessment['sponsor_concentration'] = 'well_distributed'

    return assessment


def assess_governance_quality(workspace: Dict) -> Dict:
    """Assess overall governance quality"""

    assessment = {
        'governance_risk_level': 'moderate',
        'red_flags': [],
        'positive_factors': [],
        'governance_score': 50
    }

    # Ownership assessment
    ownership = assess_ownership_structure(workspace)

    if ownership['concentration_risk'] == 'high':
        assessment['red_flags'].append('High ownership concentration - minority shareholder risk')
        assessment['governance_score'] -= 20
    elif ownership['concentration_risk'] == 'moderate':
        assessment['red_flags'].append('Moderate ownership concentration - monitor decisions')
        assessment['governance_score'] -= 10
    else:
        assessment['positive_factors'].append('Well-distributed ownership supports governance')
        assessment['governance_score'] += 15

    # Free float assessment
    if ownership.get('free_float') and ownership['free_float'] > 30:
        assessment['positive_factors'].append('Adequate free float for liquidity')
        assessment['governance_score'] += 10

    # Regulatory compliance
    assessment['red_flags'].append('Verify: no recent qualified audit opinions')
    assessment['red_flags'].append('Verify: no regulatory penalties')
    assessment['red_flags'].append('Verify: consistent financial reporting timeline')

    # Risk level
    if assessment['governance_score'] >= 70:
        assessment['governance_risk_level'] = 'low'
    elif assessment['governance_score'] >= 50:
        assessment['governance_risk_level'] = 'moderate'
    else:
        assessment['governance_risk_level'] = 'high'

    return assessment


def get_governance_analysis(workspace: Dict) -> Dict:
    """Main function for governance analysis"""

    ownership = assess_ownership_structure(workspace)
    governance = assess_governance_quality(workspace)

    return {
        'success': True,
        'ticker': workspace.get('ticker'),
        'ownership_structure': ownership,
        'governance_assessment': governance,
        'risk_factors': GOVERNANCE_RISK_FACTORS,
        'summary': {
            'governance_risk_level': governance['governance_risk_level'],
            'governance_score': governance['governance_score'],
            'red_flags': governance['red_flags'],
            'positive_factors': governance['positive_factors']
        }
    }
