"""Module 7: Unified Research-to-Trade Flow - Orchestrates research + trading decision"""

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum


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
