"""Evidence Context — single source of truth for what data exists and what claims are supported.

All intelligence engines consume this instead of querying the database independently.
This ensures:
- No engine makes unsupported claims
- Confidence and coverage are tracked separately from assessment
- Cross-engine consistency can be validated
- Data gaps are transparent to the user
"""

from typing import Dict, List, Optional, Set
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.models import FinancialFact


class MetricCoverage:
    """Coverage of a single metric across periods."""

    def __init__(self, metric: str, values: Dict[date, float]):
        self.metric = metric
        self.values = values  # {period_end: value}
        self.periods = sorted(values.keys()) if values else []
        self.latest_period = self.periods[-1] if self.periods else None
        self.latest_value = values.get(self.latest_period) if self.latest_period else None
        self.count = len(values)

    def exists(self) -> bool:
        """Whether this metric has any data."""
        return self.count > 0

    def has_multiple_periods(self) -> bool:
        """Whether we have at least 2 periods for comparison."""
        return self.count >= 2

    def get_value(self, period_end: date) -> Optional[float]:
        """Get value for a specific period."""
        return self.values.get(period_end)

    def series(self, limit: int = 10) -> List[float]:
        """Get latest N values as a list."""
        recent = sorted(self.values.items(), key=lambda x: x[0], reverse=True)[:limit]
        return [v for _, v in reversed(recent)]


class ResearchContext:
    """Complete evidence inventory for an issuer.

    Scans database on creation and builds a comprehensive map of:
    - What metrics exist
    - What periods are available
    - What data is missing
    - What claims are therefore prohibited
    - Confidence levels for each analysis domain
    """

    # CRITICAL METRICS required for high-confidence analysis in each domain
    CRITICAL_METRICS = {
        "business_health": ["revenue", "profit_after_tax", "total_debt", "total_equity"],
        "what_changed": ["revenue", "gross_profit", "finance_cost"],
        "earnings_quality": ["profit_after_tax", "operating_cash_flow"],
        "bull_bear_case": ["revenue", "profit_after_tax", "gross_profit", "total_debt"],
        "red_flags": ["revenue", "profit_after_tax", "operating_cash_flow", "accounts_receivable", "inventory"],
        "valuation": ["pe_ratio", "pb_ratio"],
        "dividend_sustainability": ["profit_after_tax", "operating_cash_flow", "dividend_per_share"],
        "customer_concentration": ["customer_concentration"],
    }

    # PROHIBITED CLAIMS when data is missing
    PROHIBITED_CLAIMS = {
        "valuation": ["cheap", "expensive", "undervalued", "overvalued", "priced in", "re-rating", "current valuation"],
        "earnings_quality_high": ["high earnings quality", "quality score > 80"],
        "dividend_sustainable": ["dividend sustainability", "dividend safe", "distribution growth"],
        "company_specific_risk": ["customer concentration", "supplier concentration", "market share"],
        "ocf_backed_earnings": ["backed by cash", "cash generation strong"],
    }

    def __init__(self, db: Session, issuer_id: int):
        self.db = db
        self.issuer_id = issuer_id
        self.as_of_date = date.today()

        # Metric inventory: {metric_name: MetricCoverage}
        self.metrics: Dict[str, MetricCoverage] = {}

        # Analysis domain confidence
        self.domain_confidence: Dict[str, Dict] = {}

        # Track what's missing for transparency
        self.missing_metrics: Set[str] = set()

        # Load all available data
        self._load_metrics()
        self._compute_confidence()

    def _load_metrics(self) -> None:
        """Scan database and build complete metric inventory."""
        # Get all distinct metrics for this issuer
        metric_names = self.db.execute(
            select(FinancialFact.line_item)
            .where(FinancialFact.issuer_id == self.issuer_id)
            .distinct()
        ).scalars().all()

        for metric in metric_names:
            rows = self.db.execute(
                select(FinancialFact.period_end, FinancialFact.value)
                .where(
                    FinancialFact.issuer_id == self.issuer_id,
                    FinancialFact.line_item == metric,
                    FinancialFact.superseded_by_id.is_(None),
                )
                .order_by(FinancialFact.period_end)
            ).all()

            values = {period_end: float(value) for period_end, value in rows if value is not None}
            self.metrics[metric] = MetricCoverage(metric, values)

    def _compute_confidence(self) -> None:
        """For each analysis domain, compute what we can and cannot claim."""
        for domain, critical_metrics in self.CRITICAL_METRICS.items():
            available = [m for m in critical_metrics if self.metrics.get(m, MetricCoverage(m, {})).exists()]
            missing = [m for m in critical_metrics if m not in available]

            coverage_pct = int((len(available) / len(critical_metrics)) * 100) if critical_metrics else 0

            if coverage_pct >= 90:
                confidence = "High"
            elif coverage_pct >= 60:
                confidence = "Medium"
            else:
                confidence = "Low"

            self.domain_confidence[domain] = {
                "confidence": confidence,
                "coverage_pct": coverage_pct,
                "available_count": len(available),
                "required_count": len(critical_metrics),
                "available": available,
                "missing": missing,
            }

            # Track globally missing metrics
            for metric in missing:
                self.missing_metrics.add(metric)

    def get_metric(self, name: str) -> Optional[MetricCoverage]:
        """Get metric by name."""
        return self.metrics.get(name)

    def has_metric(self, name: str, required: bool = False) -> bool:
        """Check if metric exists. Optionally require it."""
        exists = name in self.metrics and self.metrics[name].exists()
        if required and not exists:
            self.missing_metrics.add(name)
        return exists

    def get_value(self, metric: str, period_end: Optional[date] = None) -> Optional[float]:
        """Get latest or specific-period value for a metric."""
        if metric not in self.metrics:
            return None

        cov = self.metrics[metric]
        if period_end:
            return cov.get_value(period_end)
        else:
            return cov.latest_value

    def get_series(self, metric: str, periods: int = 10) -> List[float]:
        """Get latest N values for a metric."""
        if metric not in self.metrics:
            return []
        return self.metrics[metric].series(periods)

    def can_claim(self, claim_type: str, verbose: bool = False) -> bool:
        """Whether an engine is permitted to make a specific type of claim.

        Args:
            claim_type: One of the keys in PROHIBITED_CLAIMS
            verbose: Whether to return reason with result

        Returns:
            bool or (bool, str) if verbose
        """
        # Map claim types to required metrics
        claim_requirements = {
            "valuation": ["pe_ratio"],
            "earnings_quality_high": ["profit_after_tax", "operating_cash_flow"],
            "dividend_sustainable": ["profit_after_tax", "operating_cash_flow", "dividend_per_share"],
            "company_specific_concentration": ["customer_concentration"],
            "strong_cash_generation": ["operating_cash_flow"],
        }

        required = claim_requirements.get(claim_type, [])
        missing = [m for m in required if not self.has_metric(m)]

        allowed = len(missing) == 0

        if verbose:
            reason = ""
            if not allowed:
                reason = f"Missing critical metrics: {', '.join(missing)}"
            return allowed, reason

        return allowed

    def domain_status(self, domain: str) -> Dict:
        """Get confidence and coverage for an analysis domain."""
        return self.domain_confidence.get(domain, {
            "confidence": "Unknown",
            "coverage_pct": 0,
            "available": [],
            "missing": [],
        })

    def summary(self) -> Dict:
        """High-level summary of data availability."""
        return {
            "issuer_id": self.issuer_id,
            "as_of": self.as_of_date.isoformat(),
            "metrics_available": len(self.metrics),
            "metrics_with_data": sum(1 for m in self.metrics.values() if m.exists()),
            "periods_available": len(set(
                period
                for metric in self.metrics.values()
                for period in metric.periods
            )),
            "latest_period": max(
                (p for metric in self.metrics.values() for p in metric.periods),
                default=None
            ),
            "missing_critical_metrics": sorted(self.missing_metrics),
            "domain_confidence": self.domain_confidence,
        }

    def confidence_summary(self) -> str:
        """Human-readable confidence summary."""
        lines = []
        for domain, status in sorted(self.domain_confidence.items()):
            conf = status.get("confidence", "Unknown")
            cov = status.get("coverage_pct", 0)
            missing = status.get("missing", [])

            if missing:
                lines.append(f"{domain}: {conf} ({cov}%) | Missing: {', '.join(missing)}")
            else:
                lines.append(f"{domain}: {conf} ({cov}%)")

        return "\n".join(lines)

    def validate_engine_output(self, engine_name: str, output: Dict) -> Dict:
        """Validate that an engine's output doesn't make prohibited claims.

        Returns:
            {
                "valid": bool,
                "issues": [list of contradictions found],
                "warnings": [list of low-confidence claims],
            }
        """
        issues = []
        warnings = []

        # Extract narrative/thesis text from output
        narrative_fields = ["narrative", "thesis", "bull_thesis", "bear_thesis", "critical_debate"]
        all_text = " ".join(
            output.get(field, "")
            for field in narrative_fields
            if isinstance(output.get(field), str)
        ).lower()

        # Check for prohibited claims
        for claim_type, prohibited_words in self.PROHIBITED_CLAIMS.items():
            allowed, reason = self.can_claim(claim_type, verbose=True)

            if not allowed:
                for word in prohibited_words:
                    if word.lower() in all_text:
                        issues.append(
                            f"Prohibited claim '{word}' found in {engine_name} "
                            f"but {reason}"
                        )

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }


class ContextualizedOutput:
    """Standard wrapper for all engine outputs that includes evidence context."""

    def __init__(self, engine_name: str, context: ResearchContext):
        self.engine_name = engine_name
        self.context = context
        self.assessment = None
        self.score = None
        self.confidence = None
        self.data_coverage = None
        self.missing_critical = []
        self.narrative = None

    def set_assessment(
        self,
        assessment: str,
        score: float,
        narrative: str,
        confidence: Optional[str] = None,
        data_coverage: Optional[int] = None,
    ) -> None:
        """Set the output with automatic confidence calculation if not provided."""
        self.assessment = assessment
        self.score = score
        self.narrative = narrative
        self.confidence = confidence or self.context.domain_status(self.engine_name)["confidence"]
        self.data_coverage = data_coverage or self.context.domain_status(self.engine_name)["coverage_pct"]
        self.missing_critical = self.context.domain_status(self.engine_name).get("missing", [])

    def to_dict(self) -> Dict:
        """Convert to structured output with evidence context."""
        return {
            "status": "complete",
            "assessment": self.assessment,
            "score": self.score,
            "confidence": self.confidence,
            "data_coverage_pct": self.data_coverage,
            "missing_critical_metrics": self.missing_critical,
            "narrative": self.narrative,
        }

    def validate(self) -> Dict:
        """Check for contradictions with context."""
        return self.context.validate_engine_output(self.engine_name, self.to_dict())
