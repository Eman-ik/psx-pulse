"""Duration Basis Ingestion Normalizer — Auto-detect and normalize duration_basis during data loading.

Phase 2 implementation: When loading FinancialFacts, automatically:
1. Detect if quarterly data is discrete or YTD cumulative
2. Normalize YTD to discrete when appropriate
3. Store detection confidence
4. Flag ambiguous cases for review

This prevents silent analysis errors from mixing discrete and cumulative quarters.
"""

from datetime import date
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.db.models import FinancialFact
from app.analysis.period_duration import PeriodDurationDetector, PeriodDurationNormalizer


class DurationBasisDetector:
    """Detect duration basis for facts during ingestion."""

    def __init__(self, db: Session):
        self.db = db
        self.detector = PeriodDurationDetector()
        self.normalizer = PeriodDurationNormalizer()

    def detect_for_metric(
        self,
        issuer_id: int,
        metric: str,
        period_type: str,
    ) -> Tuple[str, str]:
        """Detect duration basis for a metric based on historical pattern.

        Args:
            issuer_id: Company ID
            metric: Line item (revenue, pat, etc.)
            period_type: "Q" or "FY"

        Returns:
            (duration_basis, detection_confidence)
            duration_basis: "discrete" | "ytd" | "point_in_time"
            detection_confidence: "high" | "medium" | "low"
        """
        # Point-in-time metrics are always point_in_time
        if metric in self.detector.POINT_IN_TIME_METRICS:
            return "point_in_time", "high"

        # For annual data, always discrete
        if period_type == "FY":
            return "discrete", "high"

        # For quarterly data, analyze pattern
        if period_type != "Q":
            return "discrete", "medium"  # Default for unknown period types

        # Get historical quarterly data for this metric
        historical = self._get_historical_quarters(issuer_id, metric)
        if len(historical) < 2:
            # Insufficient history, assume discrete
            return "discrete", "low"

        # Detect based on pattern
        basis = self.detector.detect_duration(metric, period_type, historical)

        # Confidence assessment
        confidence = self._assess_detection_confidence(historical, basis)

        return basis, confidence

    def _get_historical_quarters(
        self,
        issuer_id: int,
        metric: str,
        limit: int = 10,
    ) -> List[Tuple[date, float]]:
        """Get historical quarterly data for a metric, chronologically sorted."""
        rows = self.db.execute(
            select(FinancialFact.period_end, FinancialFact.value)
            .where(
                FinancialFact.issuer_id == issuer_id,
                FinancialFact.line_item == metric,
                FinancialFact.period_type == "quarterly",
                FinancialFact.superseded_by_id.is_(None),
            )
            .order_by(FinancialFact.period_end)
            .limit(limit)
        ).all()

        return [(period_end, float(value)) for period_end, value in rows]

    def _assess_detection_confidence(
        self,
        quarters: List[Tuple[date, float]],
        detected_basis: str,
    ) -> str:
        """Assess confidence in the detection."""
        if len(quarters) < 2:
            return "low"

        values = [v for _, v in quarters]

        if detected_basis == "ytd":
            # High confidence if strong monotonic increase
            increases = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
            ratio = increases / (len(values) - 1)

            if ratio >= 0.9:
                return "high"
            elif ratio >= 0.7:
                return "medium"
            else:
                return "low"

        else:  # discrete
            # High confidence if values vary (not monotonic)
            increases = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
            ratio = increases / (len(values) - 1)

            if ratio <= 0.5:  # Mixed increases/decreases
                return "high"
            elif ratio <= 0.7:
                return "medium"
            else:
                return "low"  # Looks YTD, not discrete

    def normalize_ytd_to_discrete(
        self,
        issuer_id: int,
        metric: str,
        period_end: date,
        current_value: float,
    ) -> Tuple[Optional[float], str]:
        """Convert YTD value to discrete equivalent if possible.

        Returns:
            (discrete_value, conversion_note)
        """
        # Get prior quarter
        prior_row = self.db.execute(
            select(FinancialFact)
            .where(
                FinancialFact.issuer_id == issuer_id,
                FinancialFact.line_item == metric,
                FinancialFact.period_type == "quarterly",
                FinancialFact.period_end < period_end,
                FinancialFact.superseded_by_id.is_(None),
            )
            .order_by(FinancialFact.period_end.desc())
            .limit(1)
        ).scalars().first()

        if prior_row is None:
            return None, "No prior quarter to normalize from"

        prior_value = float(prior_row.value)
        discrete = current_value - prior_value

        return discrete, f"Converted from YTD (was {current_value}, prior {prior_value})"


class FactDurationTagger:
    """Tag FinancialFact objects with duration_basis before storage."""

    def __init__(self, db: Session):
        self.db = db
        self.detector = DurationBasisDetector(db)

    def tag_fact(self, fact: FinancialFact) -> Tuple[FinancialFact, Dict]:
        """Add duration_basis to a fact based on detection.

        Args:
            fact: FinancialFact object (not yet committed)

        Returns:
            (fact_with_duration_tagged, metadata)
        """
        # Detect duration basis
        basis, confidence = self.detector.detect_for_metric(
            issuer_id=fact.issuer_id,
            metric=fact.line_item,
            period_type=fact.period_type,
        )

        # Set on fact
        fact.duration_basis = basis

        metadata = {
            "duration_basis": basis,
            "detection_confidence": confidence,
            "normalized": False,
            "notes": [],
        }

        # If YTD and flow metric, optionally normalize
        if basis == "ytd" and fact.period_type == "quarterly":
            if fact.line_item in DurationBasisDetector().detector.FLOW_METRICS:
                discrete_value, note = self.detector.normalize_ytd_to_discrete(
                    issuer_id=fact.issuer_id,
                    metric=fact.line_item,
                    period_end=fact.period_end,
                    current_value=float(fact.value),
                )

                if discrete_value is not None:
                    # Store original as reference, use discrete for analysis
                    metadata["normalized"] = True
                    metadata["original_value"] = float(fact.value)
                    metadata["normalized_value"] = discrete_value
                    metadata["notes"].append(note)
                    # Note: Don't actually replace fact.value; keep original as source truth
                    # Normalization happens at analysis time, not storage time

        return fact, metadata

    def batch_tag_facts(
        self,
        facts: List[FinancialFact],
    ) -> List[Tuple[FinancialFact, Dict]]:
        """Tag multiple facts for batch ingestion."""
        results = []
        for fact in facts:
            tagged_fact, metadata = self.tag_fact(fact)
            results.append((tagged_fact, metadata))
        return results


class IngestionValidator:
    """Validate ingestion with duration basis awareness."""

    @staticmethod
    def validate_period_consistency(
        facts: List[FinancialFact],
    ) -> Tuple[bool, List[str]]:
        """Check that facts for same period don't mix duration bases.

        Returns:
            (is_valid, issues)
        """
        issues = []

        # Group by period
        by_period = {}
        for fact in facts:
            key = (fact.period_end, fact.period_type)
            if key not in by_period:
                by_period[key] = []
            by_period[key].append(fact)

        # Check each period
        for (period_end, period_type), period_facts in by_period.items():
            # Get duration bases
            bases = set(f.duration_basis for f in period_facts if f.duration_basis)

            if len(bases) > 1:
                metrics_by_basis = {}
                for fact in period_facts:
                    basis = fact.duration_basis or "unknown"
                    if basis not in metrics_by_basis:
                        metrics_by_basis[basis] = []
                    metrics_by_basis[basis].append(fact.line_item)

                issue = (
                    f"Period {period_end} ({period_type}): Mixed duration bases: "
                    + "; ".join(f"{basis} ({', '.join(metrics)})" for basis, metrics in metrics_by_basis.items())
                )
                issues.append(issue)

        return len(issues) == 0, issues

    @staticmethod
    def validate_ytd_pairs(
        facts: List[FinancialFact],
    ) -> Tuple[bool, List[str]]:
        """For YTD quarterly data, verify we can normalize to discrete.

        Returns:
            (is_valid, warnings)
        """
        warnings = []

        # Group quarterly YTD by metric
        ytd_by_metric = {}
        for fact in facts:
            if fact.period_type == "quarterly" and fact.duration_basis == "ytd":
                metric = fact.line_item
                if metric not in ytd_by_metric:
                    ytd_by_metric[metric] = []
                ytd_by_metric[metric].append(fact)

        # Check each metric
        for metric, metric_facts in ytd_by_metric.items():
            sorted_facts = sorted(metric_facts, key=lambda f: f.period_end)

            # For normalization, need consecutive quarter pairs
            for i, fact in enumerate(sorted_facts[1:]):
                prior = sorted_facts[i]
                # Check if consecutive quarters (roughly 3 months apart)
                days_diff = (fact.period_end - prior.period_end).days
                if days_diff < 80 or days_diff > 100:  # Allow 80-100 days (roughly 3 months)
                    warnings.append(
                        f"YTD metric '{metric}': {prior.period_end} to {fact.period_end} "
                        f"({days_diff} days) may not be consecutive quarters"
                    )

        return True, warnings  # Always valid, but may have warnings
