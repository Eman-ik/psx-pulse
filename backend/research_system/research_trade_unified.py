"""Module 7: Unified Research-to-Trade Flow - Orchestrates research + trading decision"""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum
from datetime import datetime
import sys
from pathlib import Path

# Add parent dirs to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class EntryRecommendation(str, Enum):
    """Decision recommendations based on confidence score"""
    ENTER = "ENTER"
    CAUTION = "CAUTION"
    WAIT = "WAIT"
    AVOID = "AVOID"


@dataclass
class ResearchQuality:
    """Research completeness and quality assessment"""
    total_sections: int
    sections_with_data: int
    quality_score: float
    missing_sections: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'total_sections': self.total_sections,
            'sections_with_data': self.sections_with_data,
            'quality_score': self.quality_score,
            'missing_sections': self.missing_sections
        }


@dataclass
class ConfidenceBreakdown:
    """Detailed confidence scoring breakdown (0-100 each)"""
    research_quality: float
    technical_context: float
    market_context: float
    fundamental_context: float
    valuation_context: float
    events_context: float
    
    def weighted_score(self) -> float:
        """Calculate weighted average confidence"""
        return (
            (self.research_quality * 0.15) +
            (self.technical_context * 0.20) +
            (self.market_context * 0.20) +
            (self.fundamental_context * 0.15) +
            (self.valuation_context * 0.15) +
            (self.events_context * 0.15)
        )
    
    def to_dict(self) -> Dict:
        return {
            'research_quality': self.research_quality,
            'technical_context': self.technical_context,
            'market_context': self.market_context,
            'fundamental_context': self.fundamental_context,
            'valuation_context': self.valuation_context,
            'events_context': self.events_context,
            'weighted_score': round(self.weighted_score(), 1)
        }


class ResearchTradeUnifiedFlow:
    """Orchestrates unified research-to-trade decision flow"""
    
    @staticmethod
    def calculate_research_quality(company_data: Dict) -> ResearchQuality:
        """Calculate research quality score based on data completeness"""
        critical_fields = [
            'ticker', 'legal_name', 'sector', 'market_cap',
            'stock_price', 'revenue', 'pat', 'eps',
            'roe', 'net_margin', 'debt_to_equity', 'pe_ratio', 
            'dividend_yield', 'shares_outstanding', 'free_float'
        ]
        
        sections_with_data = sum(
            1 for field in critical_fields 
            if field in company_data and company_data[field] is not None
        )
        
        quality_score = (sections_with_data / len(critical_fields)) * 100
        
        missing_sections = [
            field for field in critical_fields 
            if field not in company_data or company_data[field] is None
        ]
        
        return ResearchQuality(
            total_sections=len(critical_fields),
            sections_with_data=sections_with_data,
            quality_score=quality_score,
            missing_sections=missing_sections
        )
    
    @staticmethod
    def calculate_entry_recommendation(
        unified_confidence: float,
        calculator_has_warnings: bool,
        market_regime: str = "NEUTRAL",
        events_recommendation: str = "NEUTRAL"
    ) -> EntryRecommendation:
        """Generate entry recommendation based on confidence and context"""
        if market_regime == "CRASH":
            return EntryRecommendation.AVOID
        
        if calculator_has_warnings and unified_confidence < 70:
            return EntryRecommendation.AVOID
        
        if events_recommendation == "AVOID":
            if unified_confidence < 75:
                return EntryRecommendation.AVOID
        
        if unified_confidence >= 75:
            if market_regime == "BEARISH_BROAD":
                return EntryRecommendation.CAUTION
            return EntryRecommendation.ENTER
        elif unified_confidence >= 60:
            return EntryRecommendation.CAUTION
        else:
            return EntryRecommendation.WAIT
    
    @staticmethod
    def build_key_reasons(confidence: ConfidenceBreakdown) -> List[str]:
        """Build human-readable key reasons"""
        scores = [
            ('Research Quality', confidence.research_quality, 15),
            ('Technical Context', confidence.technical_context, 20),
            ('Market Context', confidence.market_context, 20),
            ('Fundamental Context', confidence.fundamental_context, 15),
            ('Valuation Context', confidence.valuation_context, 15),
            ('Events Context', confidence.events_context, 15),
        ]

        scores.sort(key=lambda x: x[1], reverse=True)

        reasons = []
        for name, score, weight in scores[:3]:
            weighted_points = (score / 100) * weight
            reasons.append(f"{name}: {score:.0f}/100 ({weighted_points:.1f} pts)")

        return reasons

    @staticmethod
    def orchestrate_full_flow(
        ticker: str,
        entry: float,
        stop: float,
        targets: List[float],
        portfolio_value: float,
        risk_percent: float,
        trade_horizon: Any = None
    ) -> Dict[str, Any]:
        """
        Complete orchestration: research + calculator + contexts -> unified decision
        """
        from app.db.session import SessionLocal
        from app.db.models import Security, FinancialFact
        from sqlalchemy import select

        db = SessionLocal()

        try:
            # Step 1: Fetch security and issuer
            security = db.query(Security).filter_by(symbol=ticker.upper()).first()
            if not security:
                raise ValueError(f"Company {ticker} not found")

            issuer = security.issuer

            # Step 2: Fetch financial facts
            facts = db.query(FinancialFact).filter_by(
                issuer_id=issuer.id
            ).all()

            # Map facts to company data
            company_data = {
                'ticker': ticker.upper(),
                'legal_name': issuer.name or ticker,
                'sector': 'UNKNOWN',
            }

            for fact in facts:
                key_map = {
                    'Revenue': 'revenue',
                    'Profit After Tax': 'pat',
                    'Earnings Per Share': 'eps',
                    'Return on Equity': 'roe',
                    'Net Profit Margin': 'npm',
                    'Debt to Equity Ratio': 'debt_to_equity',
                    'Price to Earnings Ratio': 'pe_ratio',
                    'Return on Assets': 'roa',
                    'Current Ratio': 'current_ratio',
                    'Quick Ratio': 'quick_ratio',
                    'Book Value Per Share': 'bvps',
                    'Dividend Per Share': 'dps',
                    'Price to Book Ratio': 'pb_ratio',
                    'Total Assets': 'total_assets',
                    'Total Equity': 'equity',
                    'Total Debt': 'debt',
                }

                if fact.line_item in key_map:
                    company_data[key_map[fact.line_item]] = float(fact.value)

            # Step 3: Calculate research quality
            research_quality = ResearchTradeUnifiedFlow.calculate_research_quality(company_data)

            # Step 4: Calculate confidence scores (each 0-100)
            # These are simplified for now - real implementation would use detailed analysis
            technical_score = 65.0  # Placeholder
            market_score = 60.0      # Placeholder
            fundamental_score = float(company_data.get('roe', 0)) * 100 if company_data.get('roe') else 50.0
            valuation_score = 70.0   # Placeholder
            events_score = 75.0      # Placeholder

            confidence = ConfidenceBreakdown(
                research_quality=research_quality.quality_score,
                technical_context=min(100, technical_score),
                market_context=min(100, market_score),
                fundamental_context=min(100, fundamental_score),
                valuation_context=min(100, valuation_score),
                events_context=min(100, events_score),
            )

            # Step 5: Run calculator (simplified)
            risk_per_share = abs(entry - stop)
            position_size = int((portfolio_value * risk_percent / 100) / risk_per_share) if risk_per_share > 0 else 0
            capital_required = position_size * entry
            max_loss = position_size * risk_per_share
            allocation_pct = (capital_required / portfolio_value * 100) if portfolio_value > 0 else 0

            calculator_output = {
                'risk_metrics': {
                    'position_size': position_size,
                    'capital_required': capital_required,
                    'risk_per_share': risk_per_share,
                    'max_loss': max_loss,
                    'allocation_pct': allocation_pct,
                },
                'warnings': [],
                'market_regime': 'NEUTRAL',
                'events_recommendation': 'NEUTRAL',
                'has_warnings': False,
            }

            # Check for warnings
            if position_size > portfolio_value * 0.5:
                calculator_output['warnings'].append("Position size > 50% of portfolio")
                calculator_output['has_warnings'] = True

            if allocation_pct > 10:
                calculator_output['warnings'].append(f"Capital required {allocation_pct:.1f}% of portfolio")
                calculator_output['has_warnings'] = True

            # Step 6: Build response
            unified_confidence = confidence.weighted_score()
            recommendation = ResearchTradeUnifiedFlow.calculate_entry_recommendation(
                unified_confidence=unified_confidence,
                calculator_has_warnings=calculator_output['has_warnings'],
                market_regime=calculator_output.get('market_regime', 'NEUTRAL'),
                events_recommendation=calculator_output.get('events_recommendation', 'NEUTRAL')
            )

            key_reasons = ResearchTradeUnifiedFlow.build_key_reasons(confidence)

            # Step 7: Decision gates
            gates = [
                {'gate_name': 'Data Integrity', 'passed': research_quality.quality_score > 50, 'issue': None if research_quality.quality_score > 50 else 'Insufficient data'},
                {'gate_name': 'Price Validity', 'passed': entry > stop and any(t > entry for t in targets), 'issue': None if entry > stop and any(t > entry for t in targets) else 'Invalid price setup'},
                {'gate_name': 'Position Sizing', 'passed': not calculator_output['has_warnings'], 'issue': None if not calculator_output['has_warnings'] else ', '.join(calculator_output['warnings'])},
            ]

            gates_passed = all(g['passed'] for g in gates)

            # Step 8: Build thesis
            thesis = {
                'thesis_valid': gates_passed and unified_confidence >= 60,
                'reason': None if gates_passed else ' | '.join(g['issue'] for g in gates if not g['passed']),
                'pillar_scores': {
                    'Fundamental': fundamental_score,
                    'Valuation': valuation_score,
                    'Technical': technical_score,
                    'Market': market_score,
                },
                'confidence_score': unified_confidence,
                'evidence_coverage': research_quality.quality_score,
                'gates_passed': gates_passed,
                'bull_case': f"Strong revenue base (PKR {company_data.get('revenue', 0):,.0f}M), ROE {company_data.get('roe', 0):.1%}",
                'bear_case': f"Valuation concerns at P/E {company_data.get('pe_ratio', 0):.1f}x, D/E ratio {company_data.get('debt_to_equity', 0):.2f}x",
                'invalidation': "Earnings miss, sector headwinds, or technical breakdown below support",
            }

            return {
                'gates': gates,
                'gates_passed': gates_passed,
                'evidence_score': {
                    'coverage_pct': research_quality.quality_score,
                    'total_sections': research_quality.total_sections,
                    'real_sections': research_quality.sections_with_data,
                    'missing_evidence': research_quality.missing_sections,
                    'data_freshness_score': 85.0,  # Simplified
                    'source_reliability': 90.0,     # Simplified
                    'overall_evidence_score': research_quality.quality_score,
                },
                'thesis': thesis,
                'calculator': {
                    'risk_metrics': calculator_output['risk_metrics'],
                    'warnings': calculator_output['warnings'],
                },
                'ready_to_trade': gates_passed and unified_confidence >= 75,
                'confidence': unified_confidence,
                'timestamp': datetime.now().isoformat(),
            }

        finally:
            db.close()


def create_unified_response(
    ticker: str,
    company_data: Dict,
    calculator_output: Dict,
    confidence_breakdown: ConfidenceBreakdown,
    research_quality: ResearchQuality
) -> Dict:
    """Create unified research-trade flow response"""
    unified_confidence = confidence_breakdown.weighted_score()
    
    recommendation = ResearchTradeUnifiedFlow.calculate_entry_recommendation(
        unified_confidence=unified_confidence,
        calculator_has_warnings=calculator_output.get('has_warnings', False),
        market_regime=calculator_output.get('market_regime', 'NEUTRAL'),
        events_recommendation=calculator_output.get('events_recommendation', 'NEUTRAL')
    )
    
    key_reasons = ResearchTradeUnifiedFlow.build_key_reasons(confidence_breakdown)
    
    return {
        'success': True,
        'ticker': ticker,
        'company': company_data,
        'calculator': calculator_output,
        'research_quality': research_quality.to_dict(),
        'confidence_breakdown': confidence_breakdown.to_dict(),
        'unified_confidence_score': round(unified_confidence, 1),
        'entry_recommendation': recommendation.value,
        'key_reasons': key_reasons,
        'decision_context': {
            'market_regime': calculator_output.get('market_regime', 'NEUTRAL'),
            'position_sizing': calculator_output.get('position_sizing', {}),
            'warnings': calculator_output.get('warnings', [])
        }
    }
