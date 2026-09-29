"""
Core Services Layer for Khronos Research System

Single source of truth for all research, analysis, and decision logic.
Both REST API and internal workflows use these services.

Architecture:
  /api/research/analyze → ResearchService
  /api/research-trade/unified-flow → All services below
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from decimal import Decimal
from enum import Enum


# ════════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ════════════════════════════════════════════════════════════════════════════════

class DataFreshness(Enum):
    """How current is this data?"""
    CURRENT = "CURRENT"          # Updated today
    RECENT = "RECENT"            # Updated within 1 week
    STALE = "STALE"              # >1 week old
    VERY_STALE = "VERY_STALE"    # >1 month old


class TradeHorizon(Enum):
    """User's intended holding period"""
    INTRADAY = "INTRADAY"           # Hours
    SWING = "SWING"                 # 2-5 days
    SHORT_TERM = "SHORT_TERM"       # 1-4 weeks
    MEDIUM_TERM = "MEDIUM_TERM"     # 1-3 months
    LONG_TERM = "LONG_TERM"         # 3+ months


@dataclass
class MetricWithProvenance:
    """Every metric carries: value, source, timestamp, freshness"""
    value: float
    source: str  # "PSX", "Quarter2026", "Research", "Algorithm"
    as_of: datetime
    freshness: DataFreshness

    def is_usable_for_decision(self) -> bool:
        """Is this data fresh enough to use?"""
        return self.freshness in [DataFreshness.CURRENT, DataFreshness.RECENT]


@dataclass
class EvidenceCoverageScore:
    """Data completeness, not investment quality"""
    coverage_pct: float  # 0-100: % of sections with real data
    total_sections: int
    real_sections: int
    missing_evidence: List[str]
    data_freshness_score: float  # 0-100: how current is the data
    source_reliability: float  # 0-100: how reliable are the sources

    @property
    def overall_evidence_score(self) -> float:
        """Composite: (coverage + freshness + reliability) / 3"""
        return (self.coverage_pct + self.data_freshness_score + self.source_reliability) / 3


@dataclass
class ThesisComponents:
    """A formal trade thesis with all four required elements"""
    why: str                    # "Why am I buying this?"
    validation: str             # "What proves me right?"
    invalidation: str           # "What proves me wrong?"
    expected_catalyst: str      # "What catalyst am I waiting for?"
    holding_period: TradeHorizon
    key_assumptions: List[str]  # ["EPS growth", "sector momentum", "support holds"]


@dataclass
class DecisionGateResult:
    """Result of a decision gate check"""
    gate_name: str
    passed: bool
    issue: Optional[str]  # If failed, why?


# ════════════════════════════════════════════════════════════════════════════════
# SERVICES
# ════════════════════════════════════════════════════════════════════════════════

class ResearchService:
    """Fetch and evaluate 18-section research report"""

    @staticmethod
    def analyze(ticker: str) -> Dict:
        """
        Fetch research report from backend.
        Returns: {report, evidence_coverage_score, red_flags}
        """
        # TODO: Call actual research pipeline
        return {
            "report": {},
            "evidence_coverage": EvidenceCoverageScore(
                coverage_pct=83,
                total_sections=18,
                real_sections=15,
                missing_evidence=["Peer comparison", "Scenario analysis"],
                data_freshness_score=95,  # Very recent data
                source_reliability=92,
            ),
            "red_flags": ["Earnings announcement pending"],
        }


class FundamentalService:
    """Extract fundamental thesis from research and financials"""

    @staticmethod
    def analyze(ticker: str, research_report: Dict) -> Dict:
        """
        Analyze fundamentals: EPS trend, growth, quality, momentum
        Returns: {thesis_direction, strength, quality_score, momentum}
        """
        return {
            "eps_trend": "ACCELERATING",
            "growth_score": 75,  # 0-100
            "quality_score": 78,  # 0-100
            "financial_health": "STRONG",
            "strength": "POSITIVE",  # Direction of fundamental thesis
            "assumptions": ["Revenue growth sustained", "Margin stability"],
        }


class ValuationService:
    """Assess valuation: fair value, margin of safety"""

    @staticmethod
    def analyze(ticker: str, current_price: float) -> Dict:
        """
        Assess valuation: is price justified?
        Returns: {status, score, margin_of_safety, vs_historical}
        """
        return {
            "status": "FAIRLY_VALUED",
            "valuation_score": 65,  # 0-100
            "margin_of_safety": 5,  # % above fair value (negative = discount)
            "pe_vs_median": 1.12,  # 12% above 5-yr median
            "strength": "NEUTRAL",  # Valuation thesis direction
            "assumptions": ["P/E multiples normalize"],
        }


class TechnicalService:
    """Validate technical setup: entry > stop, support/resistance, trend"""

    @staticmethod
    def analyze(
        ticker: str,
        current_price: float,
        entry: float,
        stop: float,
        targets: List[float]
    ) -> Dict:
        """
        Validate technical thesis: entry/stop/targets, trend, momentum
        Returns: {setup_valid, trend, momentum_score, risk_points}
        """
        return {
            "entry_valid": entry > stop,
            "trend": "UPTREND",
            "momentum_score": 72,  # 0-100
            "support_level": 238,
            "resistance_level": 260,
            "breakout_pattern": "VALID",
            "strength": "POSITIVE",  # Technical thesis direction
            "assumptions": ["Breakout pattern holds", "Support remains intact"],
            "risk_points": ["Resistance at 260 could cap gains"],
        }


class MarketSectorService:
    """Assess market regime and sector alignment"""

    @staticmethod
    def analyze(ticker: str, sector: str) -> Dict:
        """
        Market regime, sector trend, breadth
        Returns: {regime, sector_trend, regime_strength}
        """
        return {
            "market_regime": "BULLISH",
            "market_health": 72,  # 0-100
            "sector_trend": "UPTREND",
            "sector_momentum": 68,  # 0-100
            "sector_participation": 75,  # % of sector stocks above MA20
            "strength": "SUPPORTIVE",  # Market thesis direction
            "assumptions": ["Sector rotation continues", "Market support remains"],
        }


class EventsService:
    """Assess catalyst and event risk"""

    @staticmethod
    def analyze(ticker: str) -> Dict:
        """
        Upcoming events, catalyst timing, risk
        Returns: {events, catalyst_risk_score, entry_recommendation}
        """
        return {
            "upcoming_events": [
                {"type": "EARNINGS", "days_away": 5, "importance": 10}
            ],
            "catalyst_risk": 60,  # 0-100, higher = more risky
            "nearest_event": "Earnings announcement - 5 days",
            "entry_recommendation": "CAUTION",  # Can enter but know the risk
            "strength": "MODERATE",
            "assumptions": ["Earnings support thesis"],
        }


class DecisionGatesEngine:
    """Decision gates: is this trade even worth considering?"""

    @staticmethod
    def validate_gates(
        evidence_score: EvidenceCoverageScore,
        entry: float,
        stop: float,
        targets: List[float],
        risk_reward_ratio: float,
        avg_daily_volume: float,
        position_value: float,
        market_regime: str,
        catalyst_risk: float
    ) -> List[DecisionGateResult]:
        """
        Run through decision gates in order.
        Each gate can fail independently.
        """
        gates = []

        # Gate 1: Data Integrity
        gate1 = DecisionGateResult(
            gate_name="Data Integrity",
            passed=evidence_score.coverage_pct >= 70,
            issue=None if evidence_score.coverage_pct >= 70 else f"Coverage too low: {evidence_score.coverage_pct}%"
        )
        gates.append(gate1)

        # Gate 2: Trade Validity
        entry_valid = entry > stop
        rr_valid = risk_reward_ratio >= 1.5
        liquidity_pct = position_value / (avg_daily_volume * entry) if avg_daily_volume > 0 else 100
        liquidity_valid = liquidity_pct <= 0.10  # Position < 10% of daily volume

        gate2_passed = entry_valid and rr_valid and liquidity_valid
        gate2_issues = []
        if not entry_valid:
            gate2_issues.append("Entry must be > Stop")
        if not rr_valid:
            gate2_issues.append(f"R:R too low: {risk_reward_ratio:.1f}:1 (min 1.5:1)")
        if not liquidity_valid:
            gate2_issues.append(f"Position too large: {liquidity_pct:.1%} of daily volume")

        gate2 = DecisionGateResult(
            gate_name="Trade Validity",
            passed=gate2_passed,
            issue=" | ".join(gate2_issues) if gate2_issues else None
        )
        gates.append(gate2)

        # Gate 3: Hard Risks
        hard_risks = []
        if catalyst_risk > 70:
            hard_risks.append("High catalyst risk (earnings imminent)")
        if market_regime == "CRASH":
            hard_risks.append("Market in CRASH regime")

        gate3 = DecisionGateResult(
            gate_name="Hard Risks",
            passed=len(hard_risks) == 0,
            issue=" | ".join(hard_risks) if hard_risks else None
        )
        gates.append(gate3)

        return gates


class TradeThesisEngine:
    """Synthesize all analyses into a coherent trade thesis"""

    @staticmethod
    def synthesize(
        fundamental_strength: str,
        valuation_strength: str,
        technical_strength: str,
        market_strength: str,
        catalyst_risk: float,
        evidence_score: EvidenceCoverageScore,
        gates: List[DecisionGateResult]
    ) -> Dict:
        """
        Combine all signals into:
        - Overall thesis direction
        - Confidence score (0-100, NOT a recommendation)
        - Bull case, bear case, invalidation
        """

        # Check if all gates passed
        gates_passed = all(g.passed for g in gates)

        if not gates_passed:
            return {
                "thesis_valid": False,
                "reason": "Decision gates failed",
                "confidence": 0,
            }

        # Score each pillar
        pillar_scores = {
            "Fundamental": {"STRONG": 85, "POSITIVE": 70, "NEUTRAL": 50, "NEGATIVE": 30, "WEAK": 15}.get(fundamental_strength, 50),
            "Valuation": {"STRONG": 85, "POSITIVE": 70, "NEUTRAL": 50, "NEGATIVE": 30, "WEAK": 15}.get(valuation_strength, 50),
            "Technical": {"POSITIVE": 75, "NEUTRAL": 50, "NEGATIVE": 25}.get(technical_strength, 50),
            "Market": {"SUPPORTIVE": 75, "NEUTRAL": 50, "HEADWIND": 25}.get(market_strength, 50),
        }

        # Adjust for catalyst risk
        risk_adjustment = -catalyst_risk / 2  # High risk reduces confidence

        # Confidence is average of pillars adjusted for risk
        confidence = sum(pillar_scores.values()) / len(pillar_scores) + risk_adjustment
        confidence = max(0, min(100, confidence))  # Clamp 0-100

        return {
            "thesis_valid": True,
            "pillar_scores": pillar_scores,
            "confidence_score": confidence,
            "evidence_coverage": evidence_score.overall_evidence_score,
            "gates_passed": True,
            "bull_case": "EPS momentum, dividend support, technical breakout",
            "bear_case": "Valuation above median, earnings risk, sector rotation",
            "invalidation": "Close below support (238), EPS miss, sector breakdown",
        }
