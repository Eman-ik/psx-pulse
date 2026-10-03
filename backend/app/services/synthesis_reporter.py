"""Step 25: Synthesis Reporter — Generate comprehensive analysis reports.

Multi-company analysis synthesis:
- Aggregate research across companies
- Executive dashboard summaries
- Report generation (JSON-ready for PDF/email)
- Investment recommendations
- Comparative insights

Input: Individual company analyses
Output: ComprehensiveReport (multi-company summary)
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CompanyReportSummary:
    """Single company summary in report."""

    ticker: str
    company_name: str
    sector: str
    recommendation: str  # Strong Buy, Buy, Hold, Sell, Strong Sell
    confidence: float  # 0-100%
    thesis: str  # Main investment thesis
    valuation_assessment: str = "Neutral"  # Undervalued, Fair, Overvalued
    risk_rating: str = "Medium"  # Low, Medium, High, Very High

    key_strengths: List[str] = field(default_factory=list)
    key_risks: List[str] = field(default_factory=list)
    target_price: Optional[float] = None
    upside_downside_pct: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "sector": self.sector,
            "recommendation": self.recommendation,
            "confidence": round(self.confidence, 1),
            "thesis": self.thesis,
            "strengths": self.key_strengths,
            "risks": self.key_risks,
            "valuation": self.valuation_assessment,
            "risk": self.risk_rating,
            "target_price": round(self.target_price, 2) if self.target_price else None,
            "upside_downside": round(self.upside_downside_pct, 1) if self.upside_downside_pct else None,
        }


@dataclass
class ComprehensiveReport:
    """Complete multi-company analysis report."""

    title: str
    report_date: str
    analysis_period: str

    companies: List[CompanyReportSummary] = field(default_factory=list)

    # Summary statistics
    total_companies: int = 0
    average_confidence: float = 50.0
    bull_case_count: int = 0  # Buy or Strong Buy
    bear_case_count: int = 0  # Sell or Strong Sell
    neutral_count: int = 0  # Hold

    # Executive summary
    executive_summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    sector_analysis: Dict[str, List[str]] = field(default_factory=dict)  # sector -> tickers

    # Investment summary
    portfolio_recommendations: List[str] = field(default_factory=list)
    top_pick: Optional[str] = None
    highest_risk: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "report_date": self.report_date,
            "analysis_period": self.analysis_period,
            "total_companies": self.total_companies,
            "average_confidence": round(self.average_confidence, 1),
            "recommendation_summary": {
                "bull": self.bull_case_count,
                "neutral": self.neutral_count,
                "bear": self.bear_case_count,
            },
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "companies": [c.to_dict() for c in self.companies],
            "top_pick": self.top_pick,
            "highest_risk": self.highest_risk,
            "portfolio_recommendations": self.portfolio_recommendations,
        }


class SynthesisReporter:
    """Generates comprehensive analysis reports."""

    def __init__(self):
        """Initialize synthesis reporter."""
        self.logger = logging.getLogger(__name__)

    def generate_report(
        self,
        title: str,
        analysis_period: str,
        company_summaries: List[CompanyReportSummary],
    ) -> Optional[ComprehensiveReport]:
        """Generate comprehensive report from company summaries.

        Args:
            title: Report title
            analysis_period: Analysis period (e.g., "Q4 2024", "Oct 2024")
            company_summaries: List of individual company summaries

        Returns:
            ComprehensiveReport with aggregated analysis
        """
        try:
            if not company_summaries:
                return None

            report = ComprehensiveReport(
                title=title,
                report_date=datetime.now().strftime("%Y-%m-%d"),
                analysis_period=analysis_period,
                companies=company_summaries,
                total_companies=len(company_summaries),
            )

            # Calculate summary statistics
            confidences = [c.confidence for c in company_summaries]
            report.average_confidence = (
                sum(confidences) / len(confidences)
                if confidences
                else 50.0
            )

            # Count recommendations
            for company in company_summaries:
                if company.recommendation in ["Buy", "Strong Buy"]:
                    report.bull_case_count += 1
                elif company.recommendation in ["Sell", "Strong Sell"]:
                    report.bear_case_count += 1
                else:
                    report.neutral_count += 1

            # Sector breakdown
            for company in company_summaries:
                if company.sector not in report.sector_analysis:
                    report.sector_analysis[company.sector] = []
                report.sector_analysis[company.sector].append(company.ticker)

            # Find top pick and highest risk
            report.top_pick = self._find_top_pick(company_summaries)
            report.highest_risk = self._find_highest_risk(company_summaries)

            # Generate key findings
            report.key_findings = self._generate_key_findings(
                report, company_summaries
            )

            # Generate executive summary
            report.executive_summary = self._generate_executive_summary(
                report, company_summaries
            )

            # Generate portfolio recommendations
            report.portfolio_recommendations = (
                self._generate_portfolio_recommendations(report)
            )

            self.logger.info(
                f"Generated report: {title} ({len(company_summaries)} companies, "
                f"{report.bull_case_count} bull, {report.bear_case_count} bear)"
            )
            return report

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return None

    @staticmethod
    def _find_top_pick(
        companies: List[CompanyReportSummary],
    ) -> Optional[str]:
        """Find highest confidence buy recommendation."""
        buy_candidates = [
            c
            for c in companies
            if c.recommendation in ["Buy", "Strong Buy"]
        ]

        if not buy_candidates:
            return None

        return max(buy_candidates, key=lambda c: c.confidence).ticker

    @staticmethod
    def _find_highest_risk(
        companies: List[CompanyReportSummary],
    ) -> Optional[str]:
        """Find highest risk company."""
        high_risk = [
            c
            for c in companies
            if c.risk_rating in ["High", "Very High"]
        ]

        if not high_risk:
            return None

        return high_risk[0].ticker

    @staticmethod
    def _generate_key_findings(
        report: ComprehensiveReport,
        companies: List[CompanyReportSummary],
    ) -> List[str]:
        """Generate key findings."""
        findings = []

        # Finding 1: Overall sentiment
        if report.bull_case_count > report.bear_case_count:
            findings.append(
                f"Bullish bias: {report.bull_case_count}/{report.total_companies} "
                f"companies recommended for purchase"
            )
        elif report.bear_case_count > report.bull_case_count:
            findings.append(
                f"Bearish bias: {report.bear_case_count}/{report.total_companies} "
                f"companies rated sell or below"
            )
        else:
            findings.append(
                f"Mixed sentiment: {report.bull_case_count} bull, "
                f"{report.bear_case_count} bear, {report.neutral_count} neutral"
            )

        # Finding 2: Sector composition
        if report.sector_analysis:
            largest_sector = max(
                report.sector_analysis.items(),
                key=lambda x: len(x[1]),
            )
            findings.append(
                f"Largest sector: {largest_sector[0]} ({len(largest_sector[1])} companies)"
            )

        # Finding 3: Valuation
        undervalued = sum(
            1 for c in companies if c.valuation_assessment == "Undervalued"
        )
        if undervalued > 0:
            findings.append(
                f"{undervalued} companies trading at undervalued levels"
            )

        # Finding 4: Risk
        high_risk = sum(
            1 for c in companies if c.risk_rating == "Very High"
        )
        if high_risk > 0:
            findings.append(
                f"Warning: {high_risk} companies have very high risk profile"
            )

        return findings

    @staticmethod
    def _generate_executive_summary(
        report: ComprehensiveReport,
        companies: List[CompanyReportSummary],
    ) -> str:
        """Generate executive summary text."""
        avg_conf = report.average_confidence
        confidence_level = (
            "High" if avg_conf > 75
            else "Moderate" if avg_conf > 60
            else "Low"
        )

        summary = (
            f"This analysis covers {report.total_companies} companies "
            f"during {report.analysis_period}. "
            f"Overall confidence in recommendations is {confidence_level} "
            f"({avg_conf:.0f}%). "
        )

        if report.bull_case_count > 0:
            summary += (
                f"We identify {report.bull_case_count} compelling buying "
                f"opportunities. "
            )

        if report.highest_risk:
            summary += (
                f"Investors should carefully consider risks associated with "
                f"{report.highest_risk}, which faces elevated challenges."
            )

        return summary

    @staticmethod
    def _generate_portfolio_recommendations(
        report: ComprehensiveReport,
    ) -> List[str]:
        """Generate portfolio construction recommendations."""
        recommendations = []

        if report.top_pick:
            recommendations.append(
                f"Core holding: {report.top_pick} represents highest conviction opportunity"
            )

        if report.bull_case_count >= 2:
            recommendations.append(
                "Consider building diversified long position across recommended buy cases"
            )

        if report.bear_case_count > 0:
            recommendations.append(
                "Maintain underweight or avoid positions rated sell"
            )

        recommendations.append(
            f"Monitor {report.total_companies} positions for changing fundamentals"
        )

        return recommendations
