"""Test data validation rules.

Verifies validation functions catch errors and edge cases correctly.
"""
import pytest
from decimal import Decimal

from app.validation import FinancialFactValidator, validate_financial_fact


class TestBalanceSheetValidation:
    """Test balance sheet identity validation."""

    def test_balanced_sheet_passes(self):
        """Balanced sheet should pass."""
        assets = Decimal("1000")
        liabilities = Decimal("600")
        equity = Decimal("400")

        is_valid, msg = FinancialFactValidator.validate_balance_sheet_identity(
            assets, liabilities, equity
        )
        assert is_valid is True
        assert msg is None

    def test_slightly_imbalanced_within_tolerance(self):
        """Balance sheet with <0.5% variance should pass."""
        assets = Decimal("1000")
        liabilities = Decimal("600")
        equity = Decimal("401")  # 1% over

        is_valid, msg = FinancialFactValidator.validate_balance_sheet_identity(
            assets, liabilities, equity
        )
        assert is_valid is True

    def test_imbalanced_exceeds_tolerance(self):
        """Balance sheet with >0.5% variance should fail."""
        assets = Decimal("1000")
        liabilities = Decimal("600")
        equity = Decimal("350")  # 5% under

        is_valid, msg = FinancialFactValidator.validate_balance_sheet_identity(
            assets, liabilities, equity
        )
        assert is_valid is False
        assert "imbalance" in msg.lower()

    def test_missing_component_fails(self):
        """Missing balance sheet component should fail."""
        is_valid, msg = FinancialFactValidator.validate_balance_sheet_identity(
            None, Decimal("600"), Decimal("400")
        )
        assert is_valid is False


class TestUnitConsistency:
    """Test unit consistency validation."""

    def test_consistent_units_pass(self):
        """Consistent units should pass."""
        from app.models import FinancialFact
        from datetime import date

        facts = [
            FinancialFact(metric="revenue", unit="PKR"),
            FinancialFact(metric="profit", unit="PKR"),
        ]

        is_valid, msg = FinancialFactValidator.validate_unit_consistency(facts)
        assert is_valid is True

    def test_mixed_units_fail(self):
        """Mixed units should fail."""
        from app.models import FinancialFact

        facts = [
            FinancialFact(metric="revenue", unit="PKR"),
            FinancialFact(metric="profit", unit="PKR million"),
        ]

        is_valid, msg = FinancialFactValidator.validate_unit_consistency(facts)
        assert is_valid is False
        assert "Mixed units" in msg


class TestConsolidationConsistency:
    """Test consolidation type consistency validation."""

    def test_consistent_consolidation_passes(self):
        """Consistent consolidation should pass."""
        from app.models import FinancialFact

        facts = [
            FinancialFact(metric="revenue", consolidation_type="consolidated"),
            FinancialFact(metric="profit", consolidation_type="consolidated"),
        ]

        is_valid, msg = FinancialFactValidator.validate_consolidation_consistency(facts)
        assert is_valid is True

    def test_mixed_consolidation_fails(self):
        """Mixed consolidation types should fail."""
        from app.models import FinancialFact

        facts = [
            FinancialFact(metric="revenue", consolidation_type="consolidated"),
            FinancialFact(metric="profit", consolidation_type="unconsolidated"),
        ]

        is_valid, msg = FinancialFactValidator.validate_consolidation_consistency(facts)
        assert is_valid is False
        assert "Mixed consolidation" in msg


class TestCashFlowValidation:
    """Test cash flow reconciliation."""

    def test_balanced_cash_flow_passes(self):
        """Balanced cash flow should pass."""
        opening_cash = Decimal("100")
        operating_cf = Decimal("50")
        investing_cf = Decimal("-20")
        financing_cf = Decimal("-10")
        closing_cash = Decimal("120")

        is_valid, msg = FinancialFactValidator.validate_cash_flow_reconciliation(
            opening_cash, operating_cf, investing_cf, financing_cf, closing_cash
        )
        assert is_valid is True

    def test_cf_within_tolerance_passes(self):
        """Cash flow with <1% variance should pass."""
        opening_cash = Decimal("100")
        operating_cf = Decimal("50")
        investing_cf = Decimal("-20")
        financing_cf = Decimal("-10")
        closing_cash = Decimal("120.5")  # 0.5% over

        is_valid, msg = FinancialFactValidator.validate_cash_flow_reconciliation(
            opening_cash, operating_cf, investing_cf, financing_cf, closing_cash
        )
        assert is_valid is True

    def test_cf_exceeds_tolerance_fails(self):
        """Cash flow with >1% variance should fail."""
        opening_cash = Decimal("100")
        operating_cf = Decimal("50")
        investing_cf = Decimal("-20")
        financing_cf = Decimal("-10")
        closing_cash = Decimal("110")  # 8% under (should be 120)

        is_valid, msg = FinancialFactValidator.validate_cash_flow_reconciliation(
            opening_cash, operating_cf, investing_cf, financing_cf, closing_cash
        )
        assert is_valid is False


class TestEPSValidation:
    """Test EPS calculation validation."""

    def test_correct_eps_passes(self):
        """Correct EPS calculation should pass."""
        net_income = Decimal("100")
        weighted_shares = Decimal("50")  # 100/50 = 2
        reported_eps = Decimal("2.0")

        is_valid, msg = FinancialFactValidator.validate_eps_calculation(
            net_income, weighted_shares, reported_eps
        )
        assert is_valid is True

    def test_eps_within_tolerance_passes(self):
        """EPS within 2% tolerance should pass."""
        net_income = Decimal("100")
        weighted_shares = Decimal("50")  # 100/50 = 2.0
        reported_eps = Decimal("2.02")  # 1% difference

        is_valid, msg = FinancialFactValidator.validate_eps_calculation(
            net_income, weighted_shares, reported_eps
        )
        assert is_valid is True

    def test_eps_exceeds_tolerance_fails(self):
        """EPS with >2% variance should fail."""
        net_income = Decimal("100")
        weighted_shares = Decimal("50")  # 100/50 = 2.0
        reported_eps = Decimal("2.1")  # 5% difference

        is_valid, msg = FinancialFactValidator.validate_eps_calculation(
            net_income, weighted_shares, reported_eps
        )
        assert is_valid is False


class TestRangeChecks:
    """Test metric range validation."""

    def test_valid_margin_passes(self):
        """Valid margin (0-100) should pass."""
        is_valid, msg = FinancialFactValidator.validate_range_checks(
            "gross_margin", Decimal("35.5")
        )
        assert is_valid is True

    def test_negative_margin_passes(self):
        """Negative margin (loss) should pass."""
        is_valid, msg = FinancialFactValidator.validate_range_checks(
            "net_margin", Decimal("-5.0")
        )
        assert is_valid is True

    def test_extreme_margin_fails(self):
        """Extreme margin (>200%) should fail."""
        is_valid, msg = FinancialFactValidator.validate_range_checks(
            "gross_margin", Decimal("250")
        )
        assert is_valid is False

    def test_positive_ratio_passes(self):
        """Positive ratio should pass."""
        is_valid, msg = FinancialFactValidator.validate_range_checks(
            "debt_equity", Decimal("1.5")
        )
        assert is_valid is True

    def test_negative_ratio_fails(self):
        """Negative ratio should fail."""
        is_valid, msg = FinancialFactValidator.validate_range_checks(
            "current_ratio", Decimal("-0.5")
        )
        assert is_valid is False


class TestFinancialFactValidation:
    """Test single financial fact validation."""

    def test_valid_fact_passes(self):
        """Valid financial fact should pass."""
        is_valid, msg = validate_financial_fact(
            "revenue", Decimal("123400.00"), "PKR"
        )
        assert is_valid is True
        assert msg is None

    def test_none_value_fails(self):
        """None value should fail."""
        is_valid, msg = validate_financial_fact(
            "revenue", None, "PKR"
        )
        assert is_valid is False

    def test_invalid_metric_range_fails(self):
        """Metric outside valid range should fail."""
        is_valid, msg = validate_financial_fact(
            "gross_margin", Decimal("300"), "%"
        )
        assert is_valid is False
