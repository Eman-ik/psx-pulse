"""Evidence Context — single source of truth for what data exists and what claims are supported.

All intelligence engines consume this instead of querying the database independently.
This ensures:
- No engine makes unsupported claims
- Confidence and coverage are tracked separately from assessment
- Cross-engine consistency can be validated
- Data gaps are transparent to the user
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from datetime import date
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.models import FinancialFact


class ClaimType(str, Enum):
    """Canonical claim types. Used for both PROHIBITED_CLAIMS validation and can_claim() checks."""

    VALUATION = "valuation"
    EARNINGS_QUALITY_HIGH = "earnings_quality_high"
    DIVIDEND_SUSTAINABLE = "dividend_sustainable"
    COMPANY_SPECIFIC_CONCENTRATION = "company_specific_concentration"
    STRONG_CASH_GENERATION = "strong_cash_generation"


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

    # PROHIBITED CLAIMS when data is missing (must match ClaimType enum and claim_requirements keys)
    PROHIBITED_CLAIMS = {
        ClaimType.VALUATION: ["cheap", "expensive", "undervalued", "overvalued", "priced in", "re-rating", "current valuation"],
        ClaimType.EARNINGS_QUALITY_HIGH: ["high earnings quality", "quality score > 80"],
        ClaimType.DIVIDEND_SUSTAINABLE: ["dividend sustainability", "dividend safe", "distribution growth"],
        ClaimType.COMPANY_SPECIFIC_CONCENTRATION: ["customer concentration", "supplier concentration", "market share"],
        ClaimType.STRONG_CASH_GENERATION: ["backed by cash", "cash generation strong"],
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

        # Period alignment tracking
        self._period_types: Dict[date, str] = {}  # {period_end: "FY"|"Q"|"TTM"}

        # Load all available data
        self._load_metrics()
        self._compute_confidence()
        self._detect_period_types()

    def _detect_period_types(self) -> None:
        """
        Period types are now loaded from database (FinancialFact.period_type).
        This method is kept as a placeholder for any missing periods.
        """
        # For any period_end that wasn't set during _load_metrics(),
        # default to "Unknown" rather than guessing from date
        all_periods = set()
        for metric in self.metrics.values():
            all_periods.update(metric.periods)

        for period_end in all_periods:
            if period_end not in self._period_types:
                # Period exists in data but period_type wasn't in FinancialFact
                # This indicates incomplete data ingestion
                self._period_types[period_end] = "Unknown"

    def get_period_type(self, period_end: date) -> str:
        """Get the type of period: 'FY', 'Q', or 'Other'."""
        return self._period_types.get(period_end, "Unknown")

    def get_aligned_values(
        self,
        required_metrics: List[str],
        optional_metrics: Optional[List[str]] = None,
        period_type: str = "FY",
        limit: int = 3,
    ) -> List[Dict[str, any]]:
        """Get aligned values for metrics from the same period.

        Args:
            required_metrics: Must exist in period for it to be included
            optional_metrics: Included if present, skipped if missing
            period_type: "FY", "Q", "HY", or "TTM"
            limit: Number of most recent periods to return

        Returns:
            List of dicts: [{period_end, metric1, metric2, ...}, ...]
            Only includes periods where ALL required metrics have data.
            Optional metrics are attached when available.
        """
        if optional_metrics is None:
            optional_metrics = []

        if period_type not in ["FY", "Q", "HY", "TTM"]:
            return []

        # Check that all required metrics exist
        for metric_name in required_metrics:
            if metric_name not in self.metrics:
                return []

        # Collect all periods with required metrics
        aligned_data = {}

        # First pass: add required metrics
        for metric_name in required_metrics:
            metric = self.metrics[metric_name]
            for period_end, value in metric.values.items():
                if self.get_period_type(period_end) == period_type:
                    if period_end not in aligned_data:
                        aligned_data[period_end] = {"period_end": period_end}
                    aligned_data[period_end][metric_name] = value

        # Filter to periods with ALL required metrics
        complete_periods = [
            data for data in aligned_data.values()
            if len(data) >= len(required_metrics) + 1  # +1 for period_end
        ]

        # Second pass: attach optional metrics where available
        for metric_name in optional_metrics:
            if metric_name in self.metrics:
                metric = self.metrics[metric_name]
                for period_data in complete_periods:
                    period_end = period_data["period_end"]
                    if period_end in metric.values:
                        period_data[metric_name] = metric.values[period_end]

        # Sort by period_end descending and limit
        complete_periods.sort(key=lambda x: x["period_end"], reverse=True)
        return complete_periods[:limit]

    def get_aligned_series(
        self,
        required_metrics: List[str],
        optional_metrics: Optional[List[str]] = None,
        period_type: str = "FY",
    ) -> Dict[str, List[float]]:
        """Get aligned time series for metrics (same periods only).

        Returns:
            {metric_name: [values in chronological order], ...}
            Only includes periods where ALL required metrics have data.
        """
        if optional_metrics is None:
            optional_metrics = []

        all_metrics = required_metrics + optional_metrics
        aligned = self.get_aligned_values(required_metrics, optional_metrics, period_type, limit=100)
        if not aligned:
            return {m: [] for m in all_metrics}

        result = {m: [] for m in all_metrics}
        # Sort chronologically (oldest first)
        for period_data in reversed(aligned):
            for metric in all_metrics:
                if metric in period_data:
                    result[metric].append(period_data[metric])

        return result

    def _load_metrics(self) -> None:
        """Scan database and build complete metric inventory in one query."""
        # Single query: fetch all metrics with period_type and scope from database
        rows = self.db.execute(
            select(
                FinancialFact.line_item,
                FinancialFact.period_start,
                FinancialFact.period_end,
                FinancialFact.period_type,
                FinancialFact.scope,
                FinancialFact.value
            )
            .where(
                FinancialFact.issuer_id == self.issuer_id,
                FinancialFact.superseded_by_id.is_(None),
            )
            .order_by(FinancialFact.line_item, FinancialFact.period_end)
        ).all()

        # Normalize period_type from database values to canonical form
        PERIOD_TYPE_MAP = {
            "annual": "FY",
            "quarterly": "Q",
            "half_year": "HY",
            "ttm": "TTM",
        }

        # Group by metric name in Python (zero queries, single pass)
        metrics_dict: Dict[str, Dict[date, float]] = defaultdict(dict)
        for line_item, period_start, period_end, period_type, scope, value in rows:
            if value is not None:
                # Store the database period type (not guessed from date)
                normalized_type = PERIOD_TYPE_MAP.get(period_type, "Unknown")
                self._period_types[period_end] = normalized_type
                metrics_dict[line_item][period_end] = float(value)

        # Build MetricCoverage objects
        for metric_name, values in metrics_dict.items():
            self.metrics[metric_name] = MetricCoverage(metric_name, values)

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

    def can_claim(self, claim_type, verbose: bool = False) -> bool:
        """Whether an engine is permitted to make a specific type of claim.

        Args:
            claim_type: A ClaimType enum value or string (converted to enum)
            verbose: Whether to return reason with result

        Returns:
            bool or (bool, str) if verbose
        """
        # Convert string to enum if needed
        if isinstance(claim_type, str):
            try:
                claim_type = ClaimType(claim_type)
            except ValueError:
                # Unknown claim type — safest to deny it
                if verbose:
                    return False, f"Unknown claim type: {claim_type}"
                return False

        # Map claim types to required metrics (must match PROHIBITED_CLAIMS keys exactly)
        claim_requirements = {
            ClaimType.VALUATION: ["pe_ratio"],
            ClaimType.EARNINGS_QUALITY_HIGH: ["profit_after_tax", "operating_cash_flow"],
            ClaimType.DIVIDEND_SUSTAINABLE: ["profit_after_tax", "operating_cash_flow", "dividend_per_share"],
            ClaimType.COMPANY_SPECIFIC_CONCENTRATION: ["customer_concentration"],
            ClaimType.STRONG_CASH_GENERATION: ["operating_cash_flow"],
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
        # Use is not None to preserve explicit 0 values
        self.data_coverage = (
            data_coverage
            if data_coverage is not None
            else self.context.domain_status(self.engine_name)["coverage_pct"]
        )
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
