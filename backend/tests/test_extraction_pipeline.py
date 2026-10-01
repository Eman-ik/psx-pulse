"""Test Sprint 2 extraction pipeline.

Verifies: Raw → Normalize → Validate → Store workflow
"""
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import Company, Period, Source, FinancialFact
from app.etl.extraction_pipeline import (
    RawFinancialFact,
    ExtractionPipeline,
)
from app.etl.lucky_cement_setup import setup_lucky_cement_data


@pytest.fixture
def test_db():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def luck_data(test_db):
    """Create LUCK company and periods."""
    return setup_lucky_cement_data(test_db)


class TestValueNormalization:
    """Test numeric value normalization."""

    def test_simple_integer(self):
        """Simple integer should normalize."""
        value, error = ExtractionPipeline.normalize_value("100")
        assert value == Decimal("100")
        assert error is None

    def test_decimal_value(self):
        """Decimal values should preserve precision."""
        value, error = ExtractionPipeline.normalize_value("123.45")
        assert value == Decimal("123.45")
        assert error is None

    def test_comma_separated(self):
        """Comma-separated numbers should be cleaned."""
        value, error = ExtractionPipeline.normalize_value("1,234,567.89")
        assert value == Decimal("1234567.89")
        assert error is None

    def test_parentheses_negative(self):
        """Parentheses indicate negative numbers."""
        value, error = ExtractionPipeline.normalize_value("(100)")
        assert value == Decimal("-100")
        assert error is None

    def test_parentheses_with_decimals(self):
        """Parentheses with decimals."""
        value, error = ExtractionPipeline.normalize_value("(123.45)")
        assert value == Decimal("-123.45")
        assert error is None

    def test_empty_value_fails(self):
        """Empty value should fail."""
        value, error = ExtractionPipeline.normalize_value("")
        assert value is None
        assert "Empty" in error

    def test_invalid_value_fails(self):
        """Non-numeric value should fail."""
        value, error = ExtractionPipeline.normalize_value("abc")
        assert value is None
        assert "Cannot parse" in error


class TestMetricNormalization:
    """Test metric name normalization."""

    def test_lowercase(self):
        """Convert to lowercase."""
        metric = ExtractionPipeline.normalize_metric("Revenue")
        assert metric == "revenue"

    def test_spaces_to_underscore(self):
        """Spaces become underscores."""
        metric = ExtractionPipeline.normalize_metric("Operating Profit")
        assert metric == "operating_profit"

    def test_dashes_to_underscore(self):
        """Dashes become underscores."""
        metric = ExtractionPipeline.normalize_metric("Cash-Flow")
        assert metric == "cash_flow"

    def test_multiple_spaces(self):
        """Multiple spaces handled."""
        metric = ExtractionPipeline.normalize_metric("Total  Assets")
        assert metric == "total__assets"


class TestFactNormalization:
    """Test complete fact normalization."""

    def test_normalize_valid_fact(self):
        """Valid raw fact normalizes."""
        raw = RawFinancialFact(
            metric="Revenue",
            value="1,000,000",
            unit="PKR",
            statement_type="income_statement",
            source_page=5,
        )
        normalized, error = ExtractionPipeline.normalize_fact(raw)
        assert error is None
        assert normalized.metric == "revenue"
        assert normalized.value == Decimal("1000000")
        assert normalized.unit == "PKR"
        assert normalized.source_page == 5

    def test_normalize_negative_profit(self):
        """Negative values should work."""
        raw = RawFinancialFact(
            metric="Net Income",
            value="(50,000)",
            unit="PKR",
        )
        normalized, error = ExtractionPipeline.normalize_fact(raw)
        assert error is None
        assert normalized.value == Decimal("-50000")

    def test_normalize_invalid_metric_fails(self):
        """Unknown metric should fail."""
        raw = RawFinancialFact(
            metric="Unknown Metric",
            value="100",
        )
        normalized, error = ExtractionPipeline.normalize_fact(raw)
        assert normalized is None
        assert "Unknown metric" in error

    def test_normalize_invalid_value_fails(self):
        """Invalid value should fail."""
        raw = RawFinancialFact(
            metric="Revenue",
            value="not a number",
        )
        normalized, error = ExtractionPipeline.normalize_fact(raw)
        assert normalized is None


class TestFactValidation:
    """Test fact validation after normalization."""

    def test_valid_revenue_passes(self):
        """Valid revenue passes validation."""
        raw = RawFinancialFact(
            metric="Revenue",
            value="1,000,000",
        )
        normalized, _ = ExtractionPipeline.normalize_fact(raw)
        status, notes = ExtractionPipeline.validate_fact(normalized)
        assert status == "validated"
        assert notes is None

    def test_extreme_margin_flags(self):
        """Extreme margin (>200%) gets flagged."""
        raw = RawFinancialFact(
            metric="Gross Margin",
            value="300",  # 300% is unrealistic
        )
        normalized, _ = ExtractionPipeline.normalize_fact(raw)
        status, notes = ExtractionPipeline.validate_fact(normalized)
        assert status == "flagged"
        assert notes is not None


class TestFactStorage:
    """Test storing facts in database."""

    def test_store_simple_fact(self, test_db, luck_data):
        """Store single fact."""
        company = luck_data["company"]
        period = luck_data["periods"]["annual"][2026]

        # Create source
        source = Source(
            company_id=company.id,
            source_type="annual_report",
            title="Annual Report 2026",
        )
        test_db.add(source)
        test_db.commit()

        # Create normalized fact
        raw = RawFinancialFact(
            metric="Revenue",
            value="100,000,000",
            source_page=5,
        )
        normalized, _ = ExtractionPipeline.normalize_fact(raw)

        # Store
        stored, error = ExtractionPipeline.store_fact(
            test_db, company.id, period.id, source.id, normalized
        )

        assert error is None
        assert stored.id is not None
        assert stored.metric == "revenue"
        assert stored.value == Decimal("100000000")
        assert stored.validation_status == "validated"

    def test_duplicate_fact_fails(self, test_db, luck_data):
        """Duplicate fact should fail."""
        company = luck_data["company"]
        period = luck_data["periods"]["annual"][2026]

        # Create source
        source = Source(
            company_id=company.id,
            source_type="annual_report",
            title="Annual Report 2026",
        )
        test_db.add(source)
        test_db.commit()

        # Store first fact
        raw = RawFinancialFact(metric="Revenue", value="100,000,000")
        normalized, _ = ExtractionPipeline.normalize_fact(raw)
        ExtractionPipeline.store_fact(
            test_db, company.id, period.id, source.id, normalized
        )

        # Try to store duplicate
        stored, error = ExtractionPipeline.store_fact(
            test_db, company.id, period.id, source.id, normalized
        )

        assert stored is None
        assert "Duplicate" in error


class TestPipelineProcessing:
    """Test complete pipeline processing."""

    def test_process_list_of_facts(self, test_db, luck_data):
        """Process multiple facts through pipeline."""
        company = luck_data["company"]
        period = luck_data["periods"]["annual"][2026]

        # Create source
        source = Source(
            company_id=company.id,
            source_type="annual_report",
            title="Annual Report 2026",
        )
        test_db.add(source)
        test_db.commit()

        # Create raw facts
        raw_facts = [
            RawFinancialFact(metric="Revenue", value="1,000,000", source_page=5),
            RawFinancialFact(metric="Cost of Sales", value="600,000", source_page=5),
            RawFinancialFact(metric="Gross Profit", value="400,000", source_page=6),
            RawFinancialFact(metric="Operating Profit", value="200,000", source_page=6),
            RawFinancialFact(metric="Net Income", value="150,000", source_page=7),
        ]

        # Process through pipeline
        result = ExtractionPipeline.process_raw_facts(
            test_db, company.id, period.id, source.id, raw_facts
        )

        # Verify
        assert result["stats"]["total"] == 5
        assert result["stats"]["stored"] == 5
        assert result["stats"]["flagged"] == 0
        assert result["stats"]["skipped"] == 0
        assert len(result["stored"]) == 5

        # Verify stored in database
        stored_facts = test_db.query(FinancialFact).filter(
            FinancialFact.company_id == company.id,
            FinancialFact.period_id == period.id,
        ).all()
        assert len(stored_facts) == 5

    def test_process_with_errors(self, test_db, luck_data):
        """Process facts with some errors."""
        company = luck_data["company"]
        period = luck_data["periods"]["annual"][2026]

        source = Source(
            company_id=company.id,
            source_type="annual_report",
            title="Annual Report 2026",
        )
        test_db.add(source)
        test_db.commit()

        # Mix of valid and invalid facts
        raw_facts = [
            RawFinancialFact(metric="Revenue", value="1,000,000"),
            RawFinancialFact(metric="Unknown Metric", value="100"),
            RawFinancialFact(metric="Profit", value="not a number"),
            RawFinancialFact(metric="Net Income", value="150,000"),
        ]

        result = ExtractionPipeline.process_raw_facts(
            test_db, company.id, period.id, source.id, raw_facts
        )

        # 2 stored, 2 skipped
        assert result["stats"]["stored"] == 2
        assert result["stats"]["skipped"] == 2
        assert len(result["skipped"]) == 2
