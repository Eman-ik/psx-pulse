"""Sprint 2: Financial fact extraction pipeline.

Pipeline: PDF → Text extraction → Table detection → Fact normalization

For MVP, starting with manual extraction (CSV/JSON format) to establish
validation + storage patterns. Automated PDF extraction added later.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models import Company, Period, Source, FinancialFact
from app.validation import validate_financial_fact


@dataclass
class RawFinancialFact:
    """Raw extracted fact before normalization."""
    metric: str
    value: str  # String to preserve original
    unit: str = "PKR"
    statement_type: str = "income_statement"
    consolidation_type: str = "consolidated"
    source_page: Optional[int] = None
    extraction_method: str = "manual"


@dataclass
class NormalizedFinancialFact:
    """Normalized fact ready for storage."""
    metric: str
    value: Decimal
    unit: str
    currency: str
    statement_type: str
    consolidation_type: str
    source_page: Optional[int]
    extraction_method: str
    validation_status: str  # pending, validated, flagged, rejected
    validation_notes: Optional[str] = None


class ExtractionPipeline:
    """Extract → Normalize → Validate → Store financial facts."""

    @staticmethod
    def normalize_value(raw_value: str) -> Tuple[Optional[Decimal], Optional[str]]:
        """Convert string to Decimal, handle common formats.

        Returns: (value, error_message)
        """
        if not raw_value or raw_value.strip() == "":
            return None, "Empty value"

        # Remove commas and whitespace
        cleaned = raw_value.replace(",", "").replace(" ", "").strip()

        # Handle parentheses for negative numbers
        is_negative = cleaned.startswith("(") and cleaned.endswith(")")
        if is_negative:
            cleaned = cleaned[1:-1]

        try:
            value = Decimal(cleaned)
            if is_negative:
                value = -value
            return value, None
        except Exception as e:
            return None, f"Cannot parse '{raw_value}': {str(e)}"

    @staticmethod
    def normalize_metric(raw_metric: str) -> str:
        """Normalize metric name to snake_case."""
        return raw_metric.lower().replace(" ", "_").replace("-", "_")

    @staticmethod
    def normalize_fact(raw: RawFinancialFact) -> Tuple[Optional[NormalizedFinancialFact], Optional[str]]:
        """Normalize raw fact to standard format.

        Returns: (normalized_fact, error_message)
        """
        # Parse value
        value, value_error = ExtractionPipeline.normalize_value(raw.value)
        if value is None:
            return None, value_error

        # Normalize metric name
        metric = ExtractionPipeline.normalize_metric(raw.metric)

        # Validate metric name (must be a known financial metric)
        known_metrics = {
            # Income statement
            "revenue", "sales", "gross_profit", "gross_margin",
            "cost_of_sales", "cost_of_goods_sold", "cogs",
            "operating_profit", "operating_margin", "operating_expense",
            "net_income", "net_margin", "net_profit", "profit_after_tax",
            "other_income", "finance_cost", "interest_expense", "tax_expense",
            "earnings_per_share", "eps",
            # Balance sheet
            "total_assets", "current_assets", "non_current_assets",
            "total_liabilities", "current_liabilities", "non_current_liabilities",
            "total_equity", "shareholders_equity", "retained_earnings",
            "share_capital", "reserves",
            "inventory", "accounts_receivable", "receivables",
            "cash_and_cash_equivalents", "cash",
            "accounts_payable", "payables",
            "debt", "total_debt", "long_term_debt", "short_term_debt",
            # Cash flow
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "free_cash_flow", "fcf", "cash_from_operations",
            # Other
            "weighted_shares_outstanding", "weighted_shares",
            "dividends_paid", "dividend_per_share",
        }

        if metric not in known_metrics:
            return None, f"Unknown metric: {metric}"

        normalized = NormalizedFinancialFact(
            metric=metric,
            value=value,
            unit=raw.unit,
            currency="PKR",
            statement_type=raw.statement_type,
            consolidation_type=raw.consolidation_type,
            source_page=raw.source_page,
            extraction_method=raw.extraction_method,
            validation_status="pending",
            validation_notes=None,
        )

        return normalized, None

    @staticmethod
    def validate_fact(fact: NormalizedFinancialFact) -> Tuple[str, Optional[str]]:
        """Validate normalized fact.

        Returns: (validation_status, validation_notes)
        """
        is_valid, error_msg = validate_financial_fact(
            fact.metric, fact.value, fact.unit
        )

        if is_valid:
            return "validated", None
        else:
            return "flagged", error_msg

    @staticmethod
    def store_fact(
        db: Session,
        company_id: int,
        period_id: int,
        source_id: int,
        fact: NormalizedFinancialFact,
    ) -> Tuple[Optional[FinancialFact], Optional[str]]:
        """Store fact in database.

        Returns: (stored_fact, error_message)
        """
        # Check if fact already exists
        existing = db.query(FinancialFact).filter(
            FinancialFact.company_id == company_id,
            FinancialFact.period_id == period_id,
            FinancialFact.metric == fact.metric,
            FinancialFact.consolidation_type == fact.consolidation_type,
        ).first()

        if existing:
            return None, f"Duplicate fact: {fact.metric} already exists for this period"

        # Validate fact
        validation_status, validation_notes = ExtractionPipeline.validate_fact(fact)

        # Store
        financial_fact = FinancialFact(
            company_id=company_id,
            period_id=period_id,
            metric=fact.metric,
            value=fact.value,
            unit=fact.unit,
            currency=fact.currency,
            statement_type=fact.statement_type,
            consolidation_type=fact.consolidation_type,
            source_id=source_id,
            source_page=fact.source_page,
            extraction_method=fact.extraction_method,
            validation_status=validation_status,
            validation_notes=validation_notes,
        )
        db.add(financial_fact)
        db.commit()
        db.refresh(financial_fact)

        return financial_fact, None

    @staticmethod
    def process_raw_facts(
        db: Session,
        company_id: int,
        period_id: int,
        source_id: int,
        raw_facts: List[RawFinancialFact],
    ) -> dict:
        """Process list of raw facts through pipeline.

        Returns: {
            'stored': List[FinancialFact],
            'flagged': List[{fact, error}],
            'skipped': List[{raw_fact, error}],
            'stats': {total, stored, flagged, skipped}
        }
        """
        stored = []
        flagged = []
        skipped = []

        for raw_fact in raw_facts:
            # Normalize
            normalized, norm_error = ExtractionPipeline.normalize_fact(raw_fact)
            if normalized is None:
                skipped.append({"raw_fact": raw_fact, "error": norm_error})
                continue

            # Store
            stored_fact, store_error = ExtractionPipeline.store_fact(
                db, company_id, period_id, source_id, normalized
            )
            if stored_fact is None:
                skipped.append({"raw_fact": raw_fact, "error": store_error})
                continue

            # Track result
            if stored_fact.validation_status == "flagged":
                flagged.append({"fact": stored_fact, "reason": stored_fact.validation_notes})
            else:
                stored.append(stored_fact)

        return {
            "stored": stored,
            "flagged": flagged,
            "skipped": skipped,
            "stats": {
                "total": len(raw_facts),
                "stored": len(stored),
                "flagged": len(flagged),
                "skipped": len(skipped),
            },
        }
