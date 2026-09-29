"""Tests for Module 7: Unified Research-to-Trade Flow"""

import pytest
from research_system.research_trade_unified import (
    ConfidenceBreakdown,
    EntryRecommendation,
    ResearchQuality,
    ResearchTradeUnifiedFlow,
    create_unified_response
)


class TestConfidenceBreakdown:
    """Test confidence scoring logic"""
    
    def test_weighted_score_calculation(self):
        confidence = ConfidenceBreakdown(
            research_quality=80,
            technical_context=75,
            market_context=70,
            fundamental_context=85,
            valuation_context=80,
            events_context=70
        )
        
        score = confidence.weighted_score()
        expected = (80*0.15 + 75*0.20 + 70*0.20 + 85*0.15 + 80*0.15 + 70*0.15)
        assert abs(score - expected) < 0.1
    
    def test_high_confidence(self):
        confidence = ConfidenceBreakdown(85, 90, 85, 90, 85, 90)
        assert confidence.weighted_score() > 87
    
    def test_low_confidence(self):
        confidence = ConfidenceBreakdown(40, 50, 45, 50, 45, 50)
        assert confidence.weighted_score() < 48


class TestResearchQuality:
    """Test research quality calculation"""
    
    def test_complete_data(self):
        company_data = {
            'ticker': 'FFC',
            'legal_name': 'Fauji Fertilizer',
            'sector': 'Fertilizer',
            'market_cap': 1e11,
            'stock_price': 500,
            'revenue': 100000,
            'pat': 20000,
            'eps': 10,
            'roe': 25,
            'net_margin': 20,
            'debt_to_equity': 0.5,
            'pe_ratio': 50,
            'dividend_yield': 5,
            'shares_outstanding': 1e9,
            'free_float': 40
        }
        
        quality = ResearchTradeUnifiedFlow.calculate_research_quality(company_data)
        assert quality.quality_score == 100
        assert quality.missing_sections == []
    
    def test_partial_data(self):
        company_data = {
            'ticker': 'FFC',
            'legal_name': 'Fauji Fertilizer',
            'sector': 'Fertilizer',
            'market_cap': 1e11,
            'stock_price': 500,
        }
        
        quality = ResearchTradeUnifiedFlow.calculate_research_quality(company_data)
        assert quality.quality_score < 50
        assert len(quality.missing_sections) > 0


class TestEntryRecommendation:
    """Test entry recommendation logic"""
    
    def test_strong_enter(self):
        rec = ResearchTradeUnifiedFlow.calculate_entry_recommendation(
            unified_confidence=85,
            calculator_has_warnings=False,
            market_regime="NEUTRAL"
        )
        assert rec == EntryRecommendation.ENTER
    
    def test_caution_high_confidence(self):
        rec = ResearchTradeUnifiedFlow.calculate_entry_recommendation(
            unified_confidence=85,
            calculator_has_warnings=False,
            market_regime="BEARISH_BROAD"
        )
        assert rec == EntryRecommendation.CAUTION
    
    def test_wait_low_confidence(self):
        rec = ResearchTradeUnifiedFlow.calculate_entry_recommendation(
            unified_confidence=50,
            calculator_has_warnings=False
        )
        assert rec == EntryRecommendation.WAIT
    
    def test_avoid_crash(self):
        rec = ResearchTradeUnifiedFlow.calculate_entry_recommendation(
            unified_confidence=90,
            calculator_has_warnings=False,
            market_regime="CRASH"
        )
        assert rec == EntryRecommendation.AVOID
    
    def test_avoid_warnings(self):
        rec = ResearchTradeUnifiedFlow.calculate_entry_recommendation(
            unified_confidence=60,
            calculator_has_warnings=True
        )
        assert rec == EntryRecommendation.AVOID


class TestUnifiedFlow:
    """Test complete unified flow"""
    
    def test_unified_response_structure(self):
        company_data = {
            'ticker': 'FFC',
            'legal_name': 'Fauji Fertilizer',
            'stock_price': 500,
            'market_cap': 1e11,
            'eps': 10,
            'roe': 25,
            'pe_ratio': 50,
            'net_margin': 20,
            'debt_to_equity': 0.5,
            'dividend_yield': 5,
            'revenue': 100000,
            'pat': 20000,
            'shares_outstanding': 1e9,
            'free_float': 40
        }
        
        calculator = {
            'position_sizing': {'shares': 100},
            'has_warnings': False,
            'market_regime': 'NEUTRAL',
            'events_recommendation': 'NEUTRAL'
        }
        
        confidence = ConfidenceBreakdown(80, 75, 70, 85, 80, 70)
        quality = ResearchTradeUnifiedFlow.calculate_research_quality(company_data)
        
        response = create_unified_response(
            'FFC',
            company_data,
            calculator,
            confidence,
            quality
        )
        
        assert response['success'] is True
        assert response['ticker'] == 'FFC'
        assert 'unified_confidence_score' in response
        assert 'entry_recommendation' in response
        assert 'key_reasons' in response
        assert len(response['key_reasons']) > 0
