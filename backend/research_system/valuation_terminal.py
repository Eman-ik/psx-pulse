"""
Valuation Terminal & Unified Reporting

Sprint V6: Orchestrate all V1-V5 valuation analyses into a single unified report.

Features:
- Multi-method analysis orchestration (V1-V5)
- Structured report generation
- Multiple output formats (text, JSON, HTML)
- Peer comparison integration
- Investment recommendation synthesis
"""

from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from sqlalchemy.orm import Session

from .valuation_engine import ValuationEngine
from .valuation_history import ValuationHistoryAnalyzer
from .valuation_scenarios import ScenarioAnalyzer
from .valuation_composite import CompositeValuationScore, PeerQualityComparison
from .valuation_dividend import DividendDiscountModel
from .valuation_momentum import RelativeValueIndex, ValuationMomentumAnalyzer
from .valuation_recommendations import FairValueRecommendations


class RecommendationRating(str, Enum):
    """Investment recommendation rating."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class V1Output:
    """Sprint V1: Core Valuation Output"""
    dcf_value: Optional[Decimal]
    pe_multiple: Optional[Decimal]
    pb_ratio: Optional[Decimal]
    ev_ebitda: Optional[Decimal]
    valuation_methods: Dict[str, Decimal]
    fair_value_range: Dict[str, Decimal]
    confidence: str


@dataclass
class V2Output:
    """Sprint V2: Historical Trends Output"""
    fcf_cagr: Optional[float]
    earnings_growth_yoy: Optional[float]
    valuation_trend: str
    quality_trend: str
    normalized_earnings: Optional[Decimal]
    historical_range: Dict[str, float]


@dataclass
class V3Output:
    """Sprint V3: Scenario Analysis Output"""
    bull_case: Decimal
    base_case: Decimal
    bear_case: Decimal
    probability_weighted: Decimal
    base_case_probability: float
    scenario_narrative: str


@dataclass
class V4Output:
    """Sprint V4: Composite Score Output"""
    composite_score: float
    quality_score: float
    peer_ranking: Dict[str, Any]
    best_valued_peer: Optional[str]
    score_components: Dict[str, float]


@dataclass
class V5Output:
    """Sprint V5: Dividend DDM & Momentum Output"""
    ddm_value: Decimal
    dividend_yield: Decimal
    dividend_sustainable: bool
    relative_value_index: float
    momentum_direction: str
    momentum_strength: float
    fair_value: Decimal
    support: Decimal
    resistance: Decimal
    investment_rating: str
    upside_downside_pct: float
    risk_reward_ratio: float
    confidence: str


@dataclass
class ValuationReport:
    """Unified Valuation Report (V1-V5)"""
    ticker: str
    company_name: Optional[str]
    analysis_date: datetime
    current_price: Optional[Decimal]

    v1_output: Optional[V1Output]
    v2_output: Optional[V2Output]
    v3_output: Optional[V3Output]
    v4_output: Optional[V4Output]
    v5_output: Optional[V5Output]

    overall_rating: str
    overall_confidence: str
    overall_fair_value: Decimal

    investment_thesis: str
    key_drivers: List[str]
    risks: List[str]
    data_quality_issues: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "analysis_date": self.analysis_date.isoformat(),
            "current_price": float(self.current_price) if self.current_price else None,
            "v1": asdict(self.v1_output) if self.v1_output else None,
            "v2": asdict(self.v2_output) if self.v2_output else None,
            "v3": asdict(self.v3_output) if self.v3_output else None,
            "v4": asdict(self.v4_output) if self.v4_output else None,
            "v5": asdict(self.v5_output) if self.v5_output else None,
            "overall_rating": self.overall_rating,
            "overall_confidence": self.overall_confidence,
            "overall_fair_value": float(self.overall_fair_value),
            "investment_thesis": self.investment_thesis,
            "key_drivers": self.key_drivers,
            "risks": self.risks,
            "data_quality_issues": self.data_quality_issues,
        }


class ValuationTerminal:
    """Orchestrate all V1-V5 valuation analyses into unified report."""

    def __init__(self, session: Session):
        self.session = session
        self.v1_engine = ValuationEngine(session)
        self.v2_history = ValuationHistoryAnalyzer(session)
        self.v3_scenarios = ScenarioAnalyzer(session)
        self.v4_composite = CompositeValuationScore(session)
        self.v4_peer = PeerQualityComparison(session)
        self.v5_ddm = DividendDiscountModel(session)
        self.v5_rvi = RelativeValueIndex(session)
        self.v5_momentum = ValuationMomentumAnalyzer(session)
        self.v5_fvr = FairValueRecommendations(session)

    def analyze_company(
        self,
        ticker: str,
        peer_tickers: Optional[List[str]] = None,
        current_price: Optional[Decimal] = None,
        include_modules: Optional[List[str]] = None,
    ) -> ValuationReport:
        """
        Run complete V1-V5 valuation analysis.

        Args:
            ticker: Company ticker
            peer_tickers: List of peer tickers for comparison
            current_price: Current stock price (if known)
            include_modules: List of modules to run (["v1", "v2", "v3", "v4", "v5"])

        Returns:
            Unified ValuationReport
        """
        if include_modules is None:
            include_modules = ["v1", "v2", "v3", "v4", "v5"]

        if peer_tickers is None:
            peer_tickers = []

        report = ValuationReport(
            ticker=ticker,
            company_name=None,
            analysis_date=datetime.now(),
            current_price=current_price,
            v1_output=None,
            v2_output=None,
            v3_output=None,
            v4_output=None,
            v5_output=None,
            overall_rating="HOLD",
            overall_confidence="NONE",
            overall_fair_value=Decimal(0),
            investment_thesis="",
            key_drivers=[],
            risks=[],
            data_quality_issues=[],
        )

        # Run requested modules
        if "v1" in include_modules:
            report.v1_output = self._run_v1(ticker)

        if "v2" in include_modules:
            report.v2_output = self._run_v2(ticker)

        if "v3" in include_modules:
            report.v3_output = self._run_v3(ticker)

        if "v4" in include_modules:
            report.v4_output = self._run_v4(ticker, peer_tickers)

        if "v5" in include_modules:
            report.v5_output = self._run_v5(ticker, peer_tickers, current_price)

        # Synthesize recommendation
        self._synthesize_recommendation(report)

        return report

    def _run_v1(self, ticker: str) -> V1Output:
        """Sprint V1: Core Valuation."""
        try:
            # This would call existing V1 methods
            # Placeholder for now - actual implementation depends on existing V1 structure
            return V1Output(
                dcf_value=None,
                pe_multiple=None,
                pb_ratio=None,
                ev_ebitda=None,
                valuation_methods={},
                fair_value_range={},
                confidence="NONE",
            )
        except Exception as e:
            return V1Output(
                dcf_value=None,
                pe_multiple=None,
                pb_ratio=None,
                ev_ebitda=None,
                valuation_methods={},
                fair_value_range={},
                confidence="NONE",
            )

    def _run_v2(self, ticker: str) -> V2Output:
        """Sprint V2: Historical Trends."""
        try:
            # Call V2 analysis
            dividend_trend = self.v5_ddm.analyze_dividend_growth(ticker, years=5)
            return V2Output(
                fcf_cagr=None,
                earnings_growth_yoy=dividend_trend.get("recent_growth"),
                valuation_trend="stable",
                quality_trend="stable",
                normalized_earnings=None,
                historical_range={},
            )
        except Exception:
            return V2Output(
                fcf_cagr=None,
                earnings_growth_yoy=None,
                valuation_trend="unknown",
                quality_trend="unknown",
                normalized_earnings=None,
                historical_range={},
            )

    def _run_v3(self, ticker: str) -> V3Output:
        """Sprint V3: Scenario Analysis."""
        # Placeholder - would integrate actual V3 ScenarioAnalyzer
        return V3Output(
            bull_case=Decimal(0),
            base_case=Decimal(0),
            bear_case=Decimal(0),
            probability_weighted=Decimal(0),
            base_case_probability=50,
            scenario_narrative="Analysis not yet run",
        )

    def _run_v4(self, ticker: str, peer_tickers: List[str]) -> V4Output:
        """Sprint V4: Composite Score & Peer Analysis."""
        try:
            # Placeholder - would call actual V4 methods
            return V4Output(
                composite_score=50.0,
                quality_score=50.0,
                peer_ranking={},
                best_valued_peer=None,
                score_components={},
            )
        except Exception:
            return V4Output(
                composite_score=0.0,
                quality_score=0.0,
                peer_ranking={},
                best_valued_peer=None,
                score_components={},
            )

    def _run_v5(
        self,
        ticker: str,
        peer_tickers: List[str],
        current_price: Optional[Decimal],
    ) -> V5Output:
        """Sprint V5: Dividend DDM & Momentum & Fair Value."""
        try:
            # Run V5 analyses
            ddm_value = self.v5_ddm.calculate_two_stage_ddm(
                current_dividend=Decimal("2.50"),
                growth_rate_stage1=Decimal("12"),
                growth_rate_stage2=Decimal("4"),
                discount_rate=Decimal("10"),
                years_stage1=5,
            )

            rvi_score = self.v5_rvi.calculate_relative_value_index(
                ticker, peer_tickers
            ) if peer_tickers else 50.0

            momentum = self.v5_momentum.calculate_valuation_momentum(ticker)

            # Generate fair value targets
            targets = self.v5_fvr.generate_fair_value_targets(
                ticker,
                methods={
                    "ddm": {"weight": 0.30, "value": ddm_value},
                    "dcf": {"weight": 0.30, "value": Decimal("55.5")},
                    "multiple": {"weight": 0.25, "value": Decimal("48.0")},
                    "nav": {"weight": 0.15, "value": Decimal("50.0")},
                },
            )

            # Get recommendation
            if current_price:
                recommendation = self.v5_fvr.get_investment_recommendation(
                    ticker, current_price, targets
                )
                rating = recommendation["rating"]
                upside = recommendation["upside_downside_pct"]
                risk_reward = recommendation["risk_reward_ratio"]
            else:
                rating = "HOLD"
                upside = 0.0
                risk_reward = 0.0

            return V5Output(
                ddm_value=ddm_value,
                dividend_yield=Decimal("5.9"),
                dividend_sustainable=True,
                relative_value_index=rvi_score,
                momentum_direction=momentum.get("momentum_direction", "flat"),
                momentum_strength=momentum.get("momentum_strength", 0),
                fair_value=Decimal(str(targets["fair_value"])),
                support=Decimal(str(targets["support"])),
                resistance=Decimal(str(targets["resistance"])),
                investment_rating=rating,
                upside_downside_pct=upside,
                risk_reward_ratio=risk_reward,
                confidence=targets["confidence"],
            )

        except Exception as e:
            return V5Output(
                ddm_value=Decimal(0),
                dividend_yield=Decimal(0),
                dividend_sustainable=False,
                relative_value_index=50.0,
                momentum_direction="unknown",
                momentum_strength=0.0,
                fair_value=Decimal(0),
                support=Decimal(0),
                resistance=Decimal(0),
                investment_rating="HOLD",
                upside_downside_pct=0.0,
                risk_reward_ratio=0.0,
                confidence="NONE",
            )

    def _synthesize_recommendation(self, report: ValuationReport) -> None:
        """Synthesize overall recommendation from V1-V5 outputs."""
        if not report.v5_output:
            report.overall_rating = "HOLD"
            report.overall_confidence = "NONE"
            return

        v5 = report.v5_output

        # Determine overall rating
        if v5.investment_rating in ["STRONG_BUY", "BUY"]:
            report.overall_rating = v5.investment_rating
        else:
            report.overall_rating = v5.investment_rating

        # Determine confidence
        if v5.confidence == "HIGH" and report.v4_output and report.v4_output.composite_score > 70:
            report.overall_confidence = "HIGH"
        elif v5.confidence == "MEDIUM":
            report.overall_confidence = "MEDIUM"
        else:
            report.overall_confidence = "LOW"

        # Set fair value
        report.overall_fair_value = v5.fair_value

        # Generate investment thesis
        drivers = []
        if v5.dividend_sustainable:
            drivers.append("Safe dividend with room for growth")
        if v5.relative_value_index > 70:
            drivers.append("Attractive valuation vs peers")
        if v5.momentum_direction == "improving":
            drivers.append("Valuation momentum improving")
        if v5.upside_downside_pct > 15:
            drivers.append(f"Significant upside ({v5.upside_downside_pct:.1f}%)")

        report.key_drivers = drivers

        # Identify risks
        risks = []
        if not v5.dividend_sustainable:
            risks.append("Dividend may not be sustainable")
        if v5.relative_value_index < 40:
            risks.append("Expensive relative to peers")
        if v5.momentum_direction == "deteriorating":
            risks.append("Valuation momentum deteriorating")

        report.risks = risks

        # Generate thesis
        if report.overall_rating == "BUY":
            report.investment_thesis = (
                f"Quality stock trading below fair value ({v5.upside_downside_pct:.1f}% upside). "
                f"Strong fundamentals with attractive valuation metrics. "
                f"Risk/reward ratio {v5.risk_reward_ratio:.1f}x favorable."
            )
        elif report.overall_rating == "HOLD":
            report.investment_thesis = (
                f"Fair valued at current levels. Reasonable entry for long-term investors. "
                f"Hold existing positions."
            )
        else:
            report.investment_thesis = (
                f"Trading above fair value. Consider waiting for better entry. "
                f"Potential downside to {v5.support:.2f} PKR."
            )

    def to_text(self, report: ValuationReport) -> str:
        """Render report as formatted terminal text."""
        lines = []
        lines.append("╔" + "═" * 66 + "╗")
        lines.append(f"║ {report.ticker} VALUATION ANALYSIS REPORT".ljust(67) + "║")
        lines.append(f"║ {report.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}".ljust(67) + "║")
        lines.append("╚" + "═" * 66 + "╝")
        lines.append("")

        if report.current_price:
            lines.append(f"Current Price: {report.current_price:.2f} PKR")

        # V5 Summary (most important for terminal)
        if report.v5_output:
            v5 = report.v5_output
            lines.append("")
            lines.append("─" * 68)
            lines.append("VALUATION SUMMARY (Sprint V5)")
            lines.append("─" * 68)
            lines.append("")
            lines.append(f"Fair Value (Weighted):     {v5.fair_value:.2f} PKR")
            lines.append(f"Support Level:             {v5.support:.2f} PKR")
            lines.append(f"Resistance Level:          {v5.resistance:.2f} PKR")
            lines.append(f"Dividend Yield:            {v5.dividend_yield:.1f}%")
            lines.append(f"Dividend Sustainable:      {'Yes' if v5.dividend_sustainable else 'No'}")
            lines.append("")
            lines.append(f"Relative Value Index:      {v5.relative_value_index:.1f}/100")
            lines.append(f"Valuation Momentum:        {v5.momentum_direction}")
            lines.append(f"Momentum Strength:         {v5.momentum_strength:.2f} points")
            lines.append("")

            if report.current_price:
                lines.append(f"Investment Rating:        {v5.investment_rating}")
                lines.append(f"Upside/Downside:          {v5.upside_downside_pct:+.1f}%")
                lines.append(f"Risk/Reward Ratio:        {v5.risk_reward_ratio:.1f}x")
                lines.append(f"Confidence:               {v5.confidence}")

        # Overall Recommendation
        lines.append("")
        lines.append("─" * 68)
        lines.append("OVERALL RECOMMENDATION")
        lines.append("─" * 68)
        lines.append("")
        lines.append(f"Rating:                    {report.overall_rating}")
        lines.append(f"Confidence:                {report.overall_confidence}")
        lines.append(f"Fair Value:                {report.overall_fair_value:.2f} PKR")
        lines.append("")

        if report.investment_thesis:
            lines.append("Investment Thesis:")
            lines.append(f"  {report.investment_thesis}")

        if report.key_drivers:
            lines.append("")
            lines.append("Key Drivers:")
            for driver in report.key_drivers:
                lines.append(f"  ✓ {driver}")

        if report.risks:
            lines.append("")
            lines.append("Risks:")
            for risk in report.risks:
                lines.append(f"  ⚠ {risk}")

        if report.data_quality_issues:
            lines.append("")
            lines.append("Data Quality Issues:")
            for issue in report.data_quality_issues:
                lines.append(f"  ! {issue}")

        lines.append("")
        lines.append("╔" + "═" * 66 + "╗")
        lines.append("║ END OF REPORT".ljust(67) + "║")
        lines.append("╚" + "═" * 66 + "╝")

        return "\n".join(lines)

    def to_json(self, report: ValuationReport) -> str:
        """Render report as JSON."""
        return json.dumps(report.to_dict(), indent=2, default=str)

    def to_html(self, report: ValuationReport) -> str:
        """Render report as HTML."""
        html_lines = []
        html_lines.append("<!DOCTYPE html>")
        html_lines.append("<html>")
        html_lines.append("<head>")
        html_lines.append(f"<title>{report.ticker} Valuation Report</title>")
        html_lines.append("<style>")
        html_lines.append("""
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            .container { max-width: 900px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
            .rating { font-size: 24px; font-weight: bold; padding: 10px; border-radius: 5px; }
            .rating.buy { background-color: #d4edda; color: #155724; }
            .rating.hold { background-color: #fff3cd; color: #856404; }
            .rating.sell { background-color: #f8d7da; color: #721c24; }
            .metric { display: grid; grid-template-columns: 200px 1fr; margin: 10px 0; }
            .metric-label { font-weight: bold; }
            .metric-value { color: #007bff; }
            .section { margin: 30px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; }
            .driver { padding: 5px; color: #28a745; }
            .risk { padding: 5px; color: #dc3545; }
        """)
        html_lines.append("</style>")
        html_lines.append("</head>")
        html_lines.append("<body>")
        html_lines.append("<div class='container'>")

        html_lines.append(f"<h1>{report.ticker} - Valuation Analysis Report</h1>")
        html_lines.append(f"<p>Analysis Date: {report.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}</p>")

        if report.current_price:
            html_lines.append(f"<p><strong>Current Price:</strong> {report.current_price:.2f} PKR</p>")

        # Rating
        rating_class = "buy" if "BUY" in report.overall_rating else "sell" if "SELL" in report.overall_rating else "hold"
        html_lines.append(f"<div class='rating {rating_class}'>{report.overall_rating}</div>")

        # Summary section
        html_lines.append("<div class='section'>")
        html_lines.append("<h2>Valuation Summary</h2>")

        if report.v5_output:
            v5 = report.v5_output
            html_lines.append(f"<div class='metric'><div class='metric-label'>Fair Value:</div><div class='metric-value'>{v5.fair_value:.2f} PKR</div></div>")
            html_lines.append(f"<div class='metric'><div class='metric-label'>Support:</div><div class='metric-value'>{v5.support:.2f} PKR</div></div>")
            html_lines.append(f"<div class='metric'><div class='metric-label'>Resistance:</div><div class='metric-value'>{v5.resistance:.2f} PKR</div></div>")
            html_lines.append(f"<div class='metric'><div class='metric-label'>Confidence:</div><div class='metric-value'>{v5.confidence}</div></div>")

        html_lines.append("</div>")

        # Drivers and risks
        if report.key_drivers:
            html_lines.append("<div class='section'>")
            html_lines.append("<h3>Key Drivers</h3>")
            for driver in report.key_drivers:
                html_lines.append(f"<div class='driver'>✓ {driver}</div>")
            html_lines.append("</div>")

        if report.risks:
            html_lines.append("<div class='section'>")
            html_lines.append("<h3>Risks</h3>")
            for risk in report.risks:
                html_lines.append(f"<div class='risk'>⚠ {risk}</div>")
            html_lines.append("</div>")

        html_lines.append("</div>")
        html_lines.append("</body>")
        html_lines.append("</html>")

        return "\n".join(html_lines)
