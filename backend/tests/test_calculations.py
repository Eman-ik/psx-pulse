"""Test Sprint 3 financial calculations.

Verify all calculations are deterministic, documented, and correctly use source facts.
"""
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import Company, Period, FinancialFact
from app.analysis.growth import GrowthCalculations
from app.analysis.profitability import ProfitabilityCalculations
from app.analysis.leverage import LeverageCalculations
from app.analysis.cashflow import CashFlowCalculations
from app.analysis.shareholder import ShareholderCalculations


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
def company_with_periods(test_db):
    """Create test company with two periods (current and prior year)."""
    company = Company(ticker="TEST", name="Test Company")
    test_db.add(company)
    test_db.commit()
    test_db.refresh(company)

    # Current period (FY2026)
    period_2026 = Period(
        company_id=company.id,
        period_type="annual",
        fiscal_year=2026,
        start_date=date(2025, 4, 1),
        end_date=date(2026, 3, 31),
    )
    test_db.add(period_2026)

    # Prior period (FY2025)
    period_2025 = Period(
        company_id=company.id,
        period_type="annual",
        fiscal_year=2025,
        start_date=date(2024, 4, 1),
        end_date=date(2025, 3, 31),
    )
    test_db.add(period_2025)
    test_db.commit()
    test_db.refresh(period_2026)
    test_db.refresh(period_2025)

    return {
        "company": company,
        "period_2026": period_2026,
        "period_2025": period_2025,
    }


class TestGrowthCalculations:
    """Test growth rate calculations."""

    def test_revenue_growth(self, test_db, company_with_periods):
        """Calculate revenue growth."""
        company = company_with_periods["company"]
        period_2026 = company_with_periods["period_2026"]
        period_2025 = company_with_periods["period_2025"]

        # Create facts
        revenue_2026 = FinancialFact(
            company_id=company.id,
            period_id=period_2026.id,
            metric="revenue",
            value=Decimal("12000"),
            validation_status="validated",
        )
        revenue_2025 = FinancialFact(
            company_id=company.id,
            period_id=period_2025.id,
            metric="revenue",
            value=Decimal("10000"),
            validation_status="validated",
        )
        test_db.add_all([revenue_2026, revenue_2025])
        test_db.commit()

        # Calculate: (12000 - 10000) / 10000 * 100 = 20%
        result = GrowthCalculations.calculate_revenue_growth(
            test_db, company.id, period_2026.id, period_2025.id
        )

        assert result["status"] == "complete"
        assert result["value"] == Decimal("20.00")
        assert len(result["source_facts"]) == 2

    def test_profit_growth(self, test_db, company_with_periods):
        """Calculate profit growth."""
        company = company_with_periods["company"]
        period_2026 = company_with_periods["period_2026"]
        period_2025 = company_with_periods["period_2025"]

        # Create facts
        ni_2026 = FinancialFact(
            company_id=company.id,
            period_id=period_2026.id,
            metric="net_income",
            value=Decimal("2000"),
            validation_status="validated",
        )
        ni_2025 = FinancialFact(
            company_id=company.id,
            period_id=period_2025.id,
            metric="net_income",
            value=Decimal("1600"),
            validation_status="validated",
        )
        test_db.add_all([ni_2026, ni_2025])
        test_db.commit()

        # Calculate: (2000 - 1600) / 1600 * 100 = 25%
        result = GrowthCalculations.calculate_profit_growth(
            test_db, company.id, period_2026.id, period_2025.id
        )

        assert result["status"] == "complete"
        assert result["value"] == Decimal("25.00")


class TestProfitabilityCalculations:
    """Test profitability ratio calculations."""

    def test_gross_margin(self, test_db, company_with_periods):
        """Calculate gross profit margin."""
        company = company_with_periods["company"]
        period = company_with_periods["period_2026"]

        # Create facts: Revenue 1000, Gross Profit 400 → 40% margin
        revenue = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="revenue",
            value=Decimal("1000"),
            validation_status="validated",
        )
        gp = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="gross_profit",
            value=Decimal("400"),
            validation_status="validated",
        )
        test_db.add_all([revenue, gp])
        test_db.commit()

        result = ProfitabilityCalculations.calculate_gross_margin(
            test_db, company.id, period.id
        )

        assert result["status"] == "complete"
        assert result["value"] == Decimal("40.00")

    def test_roe(self, test_db, company_with_periods):
        """Calculate return on equity."""
        company = company_with_periods["company"]
        period_2026 = company_with_periods["period_2026"]
        period_2025 = company_with_periods["period_2025"]

        # Net Income 100, Opening Equity 500, Closing Equity 600
        # Average Equity = 550, ROE = 100/550 * 100 = 18.18%
        ni = FinancialFact(
            company_id=company.id,
            period_id=period_2026.id,
            metric="net_income",
            value=Decimal("100"),
            validation_status="validated",
        )
        equity_2026 = FinancialFact(
            company_id=company.id,
            period_id=period_2026.id,
            metric="total_equity",
            value=Decimal("600"),
            validation_status="validated",
        )
        equity_2025 = FinancialFact(
            company_id=company.id,
            period_id=period_2025.id,
            metric="total_equity",
            value=Decimal("500"),
            validation_status="validated",
        )
        test_db.add_all([ni, equity_2026, equity_2025])
        test_db.commit()

        result = ProfitabilityCalculations.calculate_roe(
            test_db, company.id, period_2026.id, period_2025.id
        )

        assert result["status"] == "complete"
        assert float(result["value"]) == pytest.approx(18.18, 0.01)


class TestLeverageCalculations:
    """Test leverage ratio calculations."""

    def test_current_ratio(self, test_db, company_with_periods):
        """Calculate current ratio."""
        company = company_with_periods["company"]
        period = company_with_periods["period_2026"]

        # Current Assets 1000, Current Liabilities 500 → Ratio 2.0
        ca = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="current_assets",
            value=Decimal("1000"),
            validation_status="validated",
        )
        cl = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="current_liabilities",
            value=Decimal("500"),
            validation_status="validated",
        )
        test_db.add_all([ca, cl])
        test_db.commit()

        result = LeverageCalculations.calculate_current_ratio(
            test_db, company.id, period.id
        )

        assert result["status"] == "complete"
        assert result["value"] == Decimal("2.00")

    def test_debt_to_equity(self, test_db, company_with_periods):
        """Calculate debt-to-equity ratio."""
        company = company_with_periods["company"]
        period = company_with_periods["period_2026"]

        # Long-term Debt 300, Total Equity 1000 → Ratio 0.3
        debt = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="long_term_debt",
            value=Decimal("300"),
            validation_status="validated",
        )
        equity = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="total_equity",
            value=Decimal("1000"),
            validation_status="validated",
        )
        test_db.add_all([debt, equity])
        test_db.commit()

        result = LeverageCalculations.calculate_debt_to_equity(
            test_db, company.id, period.id
        )

        assert result["status"] == "complete"
        assert result["value"] == Decimal("0.30")


class TestCashFlowCalculations:
    """Test cash flow calculations."""

    def test_fcf(self, test_db, company_with_periods):
        """Calculate free cash flow."""
        company = company_with_periods["company"]
        period = company_with_periods["period_2026"]

        # Operating CF 2000, Investing CF -800 → FCF = 1200
        ocf = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="operating_cash_flow",
            value=Decimal("2000"),
            validation_status="validated",
        )
        icf = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="investing_cash_flow",
            value=Decimal("-800"),
            validation_status="validated",
        )
        test_db.add_all([ocf, icf])
        test_db.commit()

        result = CashFlowCalculations.calculate_fcf(
            test_db, company.id, period.id
        )

        assert result["status"] == "complete"
        assert result["value"] == Decimal("1200.00")

    def test_fcf_margin(self, test_db, company_with_periods):
        """Calculate FCF margin."""
        company = company_with_periods["company"]
        period = company_with_periods["period_2026"]

        # Operating CF 2000, Investing CF -800 → FCF 1200
        # Revenue 10000 → FCF Margin 12%
        ocf = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="operating_cash_flow",
            value=Decimal("2000"),
            validation_status="validated",
        )
        icf = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="investing_cash_flow",
            value=Decimal("-800"),
            validation_status="validated",
        )
        revenue = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="revenue",
            value=Decimal("10000"),
            validation_status="validated",
        )
        test_db.add_all([ocf, icf, revenue])
        test_db.commit()

        result = CashFlowCalculations.calculate_fcf_margin(
            test_db, company.id, period.id
        )

        assert result["status"] == "complete"
        assert result["value"] == Decimal("12.00")


class TestShareholderCalculations:
    """Test shareholder metrics."""

    def test_payout_ratio(self, test_db, company_with_periods):
        """Calculate dividend payout ratio."""
        company = company_with_periods["company"]
        period = company_with_periods["period_2026"]

        # DPS 5, EPS 20 → Payout Ratio 25%
        dps = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="dividend_per_share",
            value=Decimal("5"),
            validation_status="validated",
        )
        eps = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="earnings_per_share",
            value=Decimal("20"),
            validation_status="validated",
        )
        test_db.add_all([dps, eps])
        test_db.commit()

        result = ShareholderCalculations.calculate_payout_ratio(
            test_db, company.id, period.id
        )

        assert result["status"] == "complete"
        assert result["value"] == Decimal("25.00")

    def test_dividend_yield(self, test_db, company_with_periods):
        """Calculate dividend yield."""
        company = company_with_periods["company"]
        period = company_with_periods["period_2026"]

        # DPS 5, Current Price 100 → Yield 5%
        dps = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="dividend_per_share",
            value=Decimal("5"),
            validation_status="validated",
        )
        test_db.add(dps)
        test_db.commit()

        result = ShareholderCalculations.calculate_dividend_yield(
            test_db, company.id, period.id, Decimal("100")
        )

        assert result["status"] == "complete"
        assert result["value"] == Decimal("5.00")


class TestLineageTracking:
    """Test that calculations properly track source facts."""

    def test_roe_lineage(self, test_db, company_with_periods):
        """Verify ROE tracks all source fact IDs."""
        company = company_with_periods["company"]
        period_2026 = company_with_periods["period_2026"]
        period_2025 = company_with_periods["period_2025"]

        ni = FinancialFact(
            company_id=company.id,
            period_id=period_2026.id,
            metric="net_income",
            value=Decimal("100"),
            validation_status="validated",
        )
        eq_2026 = FinancialFact(
            company_id=company.id,
            period_id=period_2026.id,
            metric="total_equity",
            value=Decimal("600"),
            validation_status="validated",
        )
        eq_2025 = FinancialFact(
            company_id=company.id,
            period_id=period_2025.id,
            metric="total_equity",
            value=Decimal("500"),
            validation_status="validated",
        )
        test_db.add_all([ni, eq_2026, eq_2025])
        test_db.commit()

        result = ProfitabilityCalculations.calculate_roe(
            test_db, company.id, period_2026.id, period_2025.id
        )

        # Verify all 3 facts are tracked
        assert len(result["source_facts"]) == 3
        assert ni.id in result["source_facts"]
        assert eq_2026.id in result["source_facts"]
        assert eq_2025.id in result["source_facts"]


class TestMissingData:
    """Test calculations handle missing data gracefully."""

    def test_missing_fact_returns_incomplete(self, test_db, company_with_periods):
        """Missing fact should return incomplete status."""
        company = company_with_periods["company"]
        period = company_with_periods["period_2026"]

        # No financial facts created

        result = ProfitabilityCalculations.calculate_gross_margin(
            test_db, company.id, period.id
        )

        assert result["status"] == "incomplete"
        assert result["value"] is None

    def test_zero_denominator_returns_incomplete(self, test_db, company_with_periods):
        """Zero denominator should return incomplete status."""
        company = company_with_periods["company"]
        period = company_with_periods["period_2026"]

        # Revenue is zero
        revenue = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="revenue",
            value=Decimal("0"),
            validation_status="validated",
        )
        gp = FinancialFact(
            company_id=company.id,
            period_id=period.id,
            metric="gross_profit",
            value=Decimal("100"),
            validation_status="validated",
        )
        test_db.add_all([revenue, gp])
        test_db.commit()

        result = ProfitabilityCalculations.calculate_gross_margin(
            test_db, company.id, period.id
        )

        assert result["status"] == "incomplete"
        assert result["value"] is None
