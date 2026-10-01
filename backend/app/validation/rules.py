"""Data validation rules for financial facts.

Enforced before storage: Extract → Normalize → Validate → Store or Flag
"""
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from app.models import FinancialFact


ACCEPTABLE_VARIANCE = 0.005  # 0.5%
CASH_FLOW_VARIANCE = 0.01  # 1%
EPS_VARIANCE = 0.02  # 2%


class FinancialFactValidator:
    """Validates financial facts against accounting standards and consistency rules."""

    @staticmethod
    def validate_balance_sheet_identity(
        assets: Decimal,
        liabilities: Decimal,
        equity: Decimal,
    ) -> Tuple[bool, Optional[str]]:
        """Validate: Assets ≈ Liabilities + Equity (±0.5% variance)."""
        if not all([assets, liabilities, equity]):
            return False, "Missing balance sheet components"

        assets_f = float(assets)
        total_liabilities_equity = float(liabilities) + float(equity)

        if total_liabilities_equity == 0:
            return False, "Total liabilities + equity is zero"

        variance = abs((assets_f - total_liabilities_equity) / assets_f)
        is_valid = variance <= ACCEPTABLE_VARIANCE

        if not is_valid:
            return False, f"Balance sheet imbalance: {variance * 100:.2f}% variance"

        return True, None

    @staticmethod
    def validate_unit_consistency(facts: List[FinancialFact]) -> Tuple[bool, Optional[str]]:
        """Validate: All facts use same unit (don't mix PKR and PKR million)."""
        if not facts:
            return True, None

        units = set(f.unit for f in facts if f.unit)
        if len(units) > 1:
            return False, f"Mixed units detected: {units}"

        return True, None

    @staticmethod
    def validate_consolidation_consistency(
        facts: List[FinancialFact],
    ) -> Tuple[bool, Optional[str]]:
        """Validate: All facts use same consolidation type (consolidated or unconsolidated)."""
        if not facts:
            return True, None

        consolidations = set(f.consolidation_type for f in facts)
        if len(consolidations) > 1:
            return False, f"Mixed consolidation types: {consolidations}"

        return True, None

    @staticmethod
    def validate_cash_flow_reconciliation(
        opening_cash: Decimal,
        operating_cf: Decimal,
        investing_cf: Decimal,
        financing_cf: Decimal,
        closing_cash: Decimal,
    ) -> Tuple[bool, Optional[str]]:
        """Validate: Opening Cash + Total CF ≈ Closing Cash (±1% variance)."""
        if not all([opening_cash, closing_cash]):
            return False, "Missing opening or closing cash"

        opening_f = float(opening_cash)
        closing_f = float(closing_cash)

        total_cf = float(operating_cf or 0) + float(investing_cf or 0) + float(financing_cf or 0)
        calculated_closing = opening_f + total_cf

        if closing_f == 0:
            return False, "Closing cash is zero"

        variance = abs((calculated_closing - closing_f) / closing_f)
        is_valid = variance <= CASH_FLOW_VARIANCE

        if not is_valid:
            return False, f"Cash flow reconciliation failed: {variance * 100:.2f}% variance"

        return True, None

    @staticmethod
    def validate_eps_calculation(
        net_income: Decimal,
        weighted_shares: Decimal,
        reported_eps: Decimal,
    ) -> Tuple[bool, Optional[str]]:
        """Validate: Net Income / Weighted Shares ≈ Reported EPS (±2% variance)."""
        if not all([net_income, weighted_shares, reported_eps]):
            return False, "Missing EPS calculation components"

        weighted_shares_f = float(weighted_shares)
        if weighted_shares_f == 0:
            return False, "Weighted shares is zero"

        calculated_eps = float(net_income) / weighted_shares_f
        reported_eps_f = float(reported_eps)

        if reported_eps_f == 0:
            return False, "Reported EPS is zero"

        variance = abs((calculated_eps - reported_eps_f) / reported_eps_f)
        is_valid = variance <= EPS_VARIANCE

        if not is_valid:
            return False, f"EPS calculation mismatch: {variance * 100:.2f}% variance"

        return True, None

    @staticmethod
    def validate_range_checks(metric: str, value: Decimal) -> Tuple[bool, Optional[str]]:
        """Validate: Value is within reasonable range for metric type."""
        value_f = float(value)

        # Percentages should be 0-100
        if metric in ["gross_margin", "operating_margin", "net_margin", "roe", "roa", "debt_equity"]:
            if value_f < -200 or value_f > 200:
                return False, f"{metric} value {value_f}% is outside acceptable range"

        # Ratios should be positive
        if metric in ["debt_equity", "current_ratio", "interest_coverage", "dividend_yield"]:
            if value_f < 0:
                return False, f"{metric} should be positive, got {value_f}"

        return True, None

    @staticmethod
    def validate_period_completeness(
        facts: List[FinancialFact],
    ) -> Tuple[bool, Optional[str]]:
        """Validate: Period has all required core metrics."""
        required_metrics = {
            "revenue",
            "gross_profit",
            "operating_profit",
            "net_income",
            "total_assets",
            "total_liabilities",
            "total_equity",
            "operating_cash_flow",
        }

        extracted_metrics = {f.metric for f in facts}
        missing = required_metrics - extracted_metrics

        if missing:
            return False, f"Missing required metrics: {missing}"

        return True, None


def validate_financial_fact(
    metric: str,
    value: Decimal,
    unit: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Validate a single financial fact before storage."""
    # Value must not be None
    if value is None:
        return False, "Value cannot be None"

    # Range checks
    is_valid, msg = FinancialFactValidator.validate_range_checks(metric, value)
    if not is_valid:
        return False, msg

    return True, None
