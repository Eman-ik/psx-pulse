"""Cross-Engine Consistency Validator — ensures engines don't contradict each other.

Runs after all 9 engines execute and flags logical contradictions.
"""

from typing import Dict, List, Tuple
from app.analysis.evidence_context import ResearchContext


class ConsistencyValidator:
    """Validates logical consistency across all intelligence engines."""

    def __init__(self, context: ResearchContext, all_outputs: Dict[str, Dict]):
        """
        Args:
            context: Shared ResearchContext (source of truth for data)
            all_outputs: {engine_name: engine_output}
        """
        self.context = context
        self.outputs = all_outputs
        self.contradictions: List[Dict] = []
        self.warnings: List[Dict] = []

    def validate_all(self) -> Dict:
        """Run all consistency checks."""
        self._check_earnings_quality_consistency()
        self._check_valuation_consistency()
        self._check_dividend_consistency()
        self._check_receivables_consistency()
        self._check_risk_claims()
        self._check_catalyst_mock_data()

        return {
            "contradictions_found": len(self.contradictions),
            "warnings_found": len(self.warnings),
            "contradictions": self.contradictions,
            "warnings": self.warnings,
            "overall_valid": len(self.contradictions) == 0,
        }

    def _flag_contradiction(
        self,
        engines: List[str],
        claim1: str,
        claim2: str,
        reason: str,
    ) -> None:
        """Flag a logical contradiction."""
        self.contradictions.append({
            "engines": engines,
            "claims": [claim1, claim2],
            "reason": reason,
            "severity": "high",
        })

    def _flag_warning(
        self,
        engine: str,
        claim: str,
        issue: str,
    ) -> None:
        """Flag a low-confidence claim that needs review."""
        self.warnings.append({
            "engine": engine,
            "claim": claim,
            "issue": issue,
            "severity": "medium",
        })

    # ========================================================================
    # CHECK 1: Earnings Quality vs. Business Health
    # ========================================================================
    def _check_earnings_quality_consistency(self) -> None:
        """
        Business Health and Earnings Quality should not contradict.

        Rule: If Earnings Quality says confidence is Low, Business Health
        cannot claim "strong earnings" or "earnings quality: Weak" alongside
        an earnings_quality assessment of High.
        """
        bh = self.outputs.get("business_health", {})
        eq = self.outputs.get("earnings_quality", {})

        bh_eq_assessment = bh.get("components", {}).get("earnings_quality")
        eq_confidence = eq.get("confidence", "").lower()
        eq_assessment = eq.get("assessment", "").lower()

        # Contradiction: BH says "Weak" but EQ says "High"
        if bh_eq_assessment == "Weak" and "high" in eq_assessment:
            if eq_confidence == "high":
                # This is a real contradiction - EQ shouldn't claim High confidence
                # when BH already noted weakness
                self._flag_contradiction(
                    ["business_health", "earnings_quality"],
                    f"Business Health: earnings_quality = Weak",
                    f"Earnings Quality: assessment = High (confidence: {eq_confidence})",
                    "Cannot have both 'weak' and 'high' quality simultaneously. "
                    "Earnings Quality should acknowledge Business Health's concern.",
                )
            elif eq_confidence == "low":
                # This is fine - both are appropriately cautious
                pass

        # Contradiction: EQ confidence is Low but claims High quality
        if eq_confidence == "low" and "high" in eq_assessment:
            self._flag_contradiction(
                ["earnings_quality"],
                f"Quality assessment: High",
                f"Confidence: Low",
                "Cannot claim High quality with Low confidence. "
                "Assessment should be 'Moderate' or 'Moderate (provisional)'.",
            )

        # Contradiction: Missing critical data but High confidence
        missing = eq.get("missing_critical_metrics", [])
        if missing and eq_confidence == "high":
            self._flag_warning(
                "earnings_quality",
                f"Assessment: {eq_assessment}",
                f"Missing critical metrics {missing} should prevent High confidence.",
            )

    # ========================================================================
    # CHECK 2: Valuation Claims without Valuation Data
    # ========================================================================
    def _check_valuation_consistency(self) -> None:
        """
        No valuation language allowed if PE/PB data missing.

        Prohibited words: cheap, expensive, undervalued, overvalued,
        priced in, re-rating, current valuation, fair value, discount, premium.
        """
        valuation = self.outputs.get("valuation_context", {})
        bull = self.outputs.get("bull_bear_case", {}).get("bull_case", {})
        bear = self.outputs.get("bull_bear_case", {}).get("bear_case", {})

        val_status = valuation.get("status", "")
        val_assessment = valuation.get("assessment", "").lower()

        # If valuation is unavailable, flag any valuation language elsewhere
        if val_status == "unavailable" or "unavailable" in val_assessment:
            prohibited_words = [
                "valuation", "cheap", "expensive", "undervalued", "overvalued",
                "priced", "re-rating", "fair value", "discount", "premium",
            ]

            bull_thesis = bull.get("thesis", "").lower()
            for word in prohibited_words:
                if word in bull_thesis:
                    self._flag_contradiction(
                        ["valuation_context", "bull_bear_case"],
                        "Valuation unavailable (missing PE/PB)",
                        f"Bull case uses '{word}'",
                        "Valuation language prohibited when PE/PB data missing.",
                    )

            bear_thesis = bear.get("thesis", "").lower()
            for word in prohibited_words:
                if word in bear_thesis:
                    self._flag_contradiction(
                        ["valuation_context", "bull_bear_case"],
                        "Valuation unavailable (missing PE/PB)",
                        f"Bear case uses '{word}'",
                        "Valuation language prohibited when PE/PB data missing.",
                    )

    # ========================================================================
    # CHECK 3: Dividend Sustainability Claims
    # ========================================================================
    def _check_dividend_consistency(self) -> None:
        """
        Cannot claim dividend sustainability without OCF + DPS data.

        Required: operating_cash_flow, dividend_per_share, profit_after_tax
        """
        has_ocf = self.context.has_metric("operating_cash_flow")
        has_dps = self.context.has_metric("dividend_per_share")
        has_pat = self.context.has_metric("profit_after_tax")

        can_claim_dividend = has_ocf and has_dps and has_pat

        # Check for unsupported dividend claims
        bull = self.outputs.get("bull_bear_case", {}).get("bull_case", {})
        bull_thesis = bull.get("thesis", "").lower()

        if not can_claim_dividend:
            if "dividend" in bull_thesis:
                missing = []
                if not has_ocf:
                    missing.append("operating_cash_flow")
                if not has_dps:
                    missing.append("dividend_per_share")

                self._flag_contradiction(
                    ["bull_bear_case", "valuation_context"],
                    f"Dividend claim in bull case",
                    f"Missing: {', '.join(missing)}",
                    "Cannot claim dividend sustainability without required metrics.",
                )

    # ========================================================================
    # CHECK 4: Receivables Analysis
    # ========================================================================
    def _check_receivables_consistency(self) -> None:
        """
        "What Changed" detected receivable deterioration but claims
        "no offsetting concerns."
        """
        what_changed = self.outputs.get("what_changed", {})
        negative = what_changed.get("negative_changes", [])
        interpretation = what_changed.get("interpretation", "").lower()

        has_receivable_concern = any("receivable" in n.lower() for n in negative)
        no_concerns = "no offsetting" in interpretation or "no concerns" in interpretation

        if has_receivable_concern and no_concerns:
            self._flag_contradiction(
                ["what_changed"],
                "Negative change detected: receivable days deteriorating",
                "Interpretation: no offsetting concerns",
                "Deteriorating receivables ARE an offsetting concern. "
                "Should say: 'Operations improved but receivable quality declined.'",
            )

    # ========================================================================
    # CHECK 5: Risk Claims without Evidence
    # ========================================================================
    def _check_risk_claims(self) -> None:
        """
        Risk engine should not claim company-specific risks it cannot prove.

        Example: "customer concentration" claim when customer_concentration metric missing.
        """
        risk = self.outputs.get("risk_engine", {})
        all_risks = risk.get("all_risks", [])

        for risk_item in all_risks:
            title = risk_item.get("title", "").lower()
            category = risk_item.get("category", "").lower()

            # Company-specific risks require specific metrics
            company_specific_metrics = {
                "customer concentration": "customer_concentration",
                "supplier concentration": "supplier_concentration",
                "market share": "market_share",
            }

            for risk_name, required_metric in company_specific_metrics.items():
                if risk_name in title and not self.context.has_metric(required_metric):
                    self._flag_contradiction(
                        ["risk_engine"],
                        f"Risk claimed: {title}",
                        f"Missing metric: {required_metric}",
                        f"Company-specific '{risk_name}' cannot be claimed without {required_metric} data. "
                        f"Should be labeled 'Sector-level structural risk' instead.",
                    )

    # ========================================================================
    # CHECK 6: Mock Data in Production
    # ========================================================================
    def _check_catalyst_mock_data(self) -> None:
        """
        Catalyst engine should not show mock data to users.
        """
        catalysts = self.outputs.get("catalyst_engine", {})

        # Check if this is marked as mock
        # (In real implementation, would check data source)
        if catalysts.get("_uses_mock_data"):
            self._flag_contradiction(
                ["catalyst_engine"],
                "Catalyst data from mock sources",
                "Production user-facing output",
                "Mock catalysts must not appear in production. "
                "Gate output with: if uses_mock: return 'Catalysts unavailable'",
            )

    # ========================================================================
    # UTILITY: Generate Human-Readable Report
    # ========================================================================
    def report(self) -> str:
        """Human-readable consistency report."""
        lines = [
            "=" * 80,
            "CROSS-ENGINE CONSISTENCY REPORT",
            "=" * 80,
        ]

        if not self.contradictions and not self.warnings:
            lines.append("\n✅ No contradictions detected.\n")
            return "\n".join(lines)

        if self.contradictions:
            lines.append(f"\n❌ CONTRADICTIONS FOUND: {len(self.contradictions)}\n")
            for i, c in enumerate(self.contradictions, 1):
                lines.append(f"{i}. {' ↔ '.join(c['engines'])}")
                lines.append(f"   {c['claims'][0]}")
                lines.append(f"   {c['claims'][1]}")
                lines.append(f"   → {c['reason']}\n")

        if self.warnings:
            lines.append(f"\n⚠️  WARNINGS: {len(self.warnings)}\n")
            for i, w in enumerate(self.warnings, 1):
                lines.append(f"{i}. {w['engine']}")
                lines.append(f"   Claim: {w['claim']}")
                lines.append(f"   Issue: {w['issue']}\n")

        lines.append("=" * 80)
        return "\n".join(lines)
