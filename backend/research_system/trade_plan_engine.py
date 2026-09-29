"""
Trade Planning Engine - Module 6, Sprint R1

Core position sizing and risk calculation engine.
Answers the 10 critical questions before capital deployment.

Components:
- Entry/Stop/Target calculation
- Risk per share
- Position sizing (max loss method)
- Capital required
- Portfolio allocation
- Risk/Reward ratios (multiple targets)
- Liquidity constraint checking
- Warning engine (non-blocking flags)
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from decimal import Decimal


# ════════════════════════════════════════════════════════════════════════════════
# ENUMS & CONSTANTS
# ════════════════════════════════════════════════════════════════════════════════

class TradeType(str, Enum):
    """Trade classification."""
    MOMENTUM = "MOMENTUM"
    BREAKOUT = "BREAKOUT"
    VALUE = "VALUE"
    MEAN_REVERSION = "MEAN_REVERSION"
    EVENT = "EVENT"
    DIVIDEND = "DIVIDEND"
    LONG_TERM_ACCUMULATION = "LONG_TERM_ACCUMULATION"
    MANUAL = "MANUAL"


class TimeHorizon(str, Enum):
    """Trade time horizon."""
    INTRADAY = "INTRADAY"           # 1-5 days
    SWING = "SWING"                 # 1-4 weeks
    SHORT_TERM = "SHORT_TERM"       # 1-3 months
    MEDIUM_TERM = "MEDIUM_TERM"     # 3-12 months
    LONG_TERM = "LONG_TERM"         # 1Y+


class StopType(str, Enum):
    """Stop-loss methodology."""
    TECHNICAL = "TECHNICAL"           # Below support level
    ATR = "ATR"                       # Multiple of ATR
    PERCENTAGE = "PERCENTAGE"         # Simple % risk
    MANUAL = "MANUAL"                 # User-defined
    THESIS_INVALIDATION = "THESIS_INVALIDATION"  # Specific break condition


class LiquidityCategory(str, Enum):
    """Position liquidity impact."""
    LOW = "LOW"              # < 2% of ADV20
    MODERATE = "MODERATE"    # 2-5% of ADV20
    HIGH = "HIGH"            # 5-15% of ADV20
    VERY_HIGH = "VERY_HIGH"  # > 15% of ADV20


class TradeStatus(str, Enum):
    """Trade plan lifecycle."""
    DRAFT = "DRAFT"                       # Initial creation
    WATCHING = "WATCHING"                 # Monitoring for entry
    READY = "READY"                       # Approved, waiting trigger
    ENTERED = "ENTERED"                   # Position active
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED" # Partial exits taken
    CLOSED = "CLOSED"                     # Position fully exited
    CANCELLED = "CANCELLED"               # Plan abandoned
    STOPPED_OUT = "STOPPED_OUT"           # Hit stop-loss


# ════════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class EntryZone:
    """Entry price zone (not single point)."""
    low: float              # Entry zone minimum
    high: float             # Entry zone maximum
    planned_entry: float    # Specific entry within zone


@dataclass
class RiskMetrics:
    """Core risk calculations."""
    risk_per_share: float   # Entry - Stop
    max_loss: float         # Portfolio × Risk%
    position_size: int      # Shares to buy
    capital_required: float # Position Size × Entry
    allocation_pct: float   # Capital Required / Portfolio × 100


@dataclass
class RiskRewardRatio:
    """R/R calculation for single target."""
    target_price: float
    reward_per_share: float  # Target - Entry
    ratio: float             # Reward / Risk (e.g., 3.0 for 1:3)


@dataclass
class CalculatorInput:
    """Input parameters for trade plan calculation."""
    # Entry/Exit levels
    entry_price: float              # Planned entry
    stop_price: float               # Stop-loss
    target_prices: List[float]      # Target levels (1, 2, 3)

    # Portfolio risk
    portfolio_value: float          # Total portfolio size (PKR)
    risk_percent: float             # Risk per trade (e.g., 1.0 = 1%)

    # Optional constraints
    max_position_percent: float = 20.0     # Max % of portfolio
    max_position_liquidity_pct: float = 5.0  # Max % of ADV20

    # Optional context
    adv20_value: Optional[float] = None    # Average daily value (PKR)
    atr: Optional[float] = None            # ATR for stop calculation


@dataclass
class CalculatorOutput:
    """Complete risk calculation output."""
    # Entry/Stop/Target
    entry_zone: EntryZone
    stop_price: float
    target_prices: List[float]

    # Risk metrics
    risk_metrics: RiskMetrics

    # R/R ratios (one per target)
    risk_reward_ratios: List[RiskRewardRatio]

    # Constraints applied
    position_size_before_caps: int  # Risk-based sizing
    concentration_cap_applied: bool
    liquidity_cap_applied: bool

    # Liquidity assessment
    liquidity_category: Optional[LiquidityCategory] = None
    position_pct_of_adv20: Optional[float] = None

    # Warnings
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


# ════════════════════════════════════════════════════════════════════════════════
# CORE CALCULATOR
# ════════════════════════════════════════════════════════════════════════════════

class TradePlanCalculator:
    """Trade plan risk and sizing calculations."""

    # ════════════════════════════════════════════════════════════════════════════
    # VALIDATION
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def validate_inputs(input_params: CalculatorInput) -> Tuple[bool, List[str]]:
        """
        Validate input parameters for logical consistency.

        Args:
            input_params: Calculator inputs

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Basic positive checks
        if input_params.entry_price <= 0:
            errors.append("Entry price must be positive")
        if input_params.stop_price <= 0:
            errors.append("Stop price must be positive")
        if input_params.portfolio_value <= 0:
            errors.append("Portfolio value must be positive")
        if input_params.risk_percent <= 0:
            errors.append("Risk percent must be positive")

        # Long trade: Stop < Entry < Target
        if input_params.stop_price >= input_params.entry_price:
            errors.append("For long trade: Stop must be below Entry")

        for i, target in enumerate(input_params.target_prices):
            if target <= input_params.entry_price:
                errors.append(f"Target {i+1} ({target}) must be above Entry ({input_params.entry_price})")

        # Targets should be in ascending order
        for i in range(len(input_params.target_prices) - 1):
            if input_params.target_prices[i] >= input_params.target_prices[i + 1]:
                errors.append(f"Targets must be in ascending order")
                break

        # Risk percent reasonable
        if input_params.risk_percent > 10:
            errors.append("Risk percent > 10% is unusually high")

        return len(errors) == 0, errors

    # ════════════════════════════════════════════════════════════════════════════
    # POSITION SIZING
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def calculate_risk_per_share(entry: float, stop: float) -> float:
        """
        Calculate risk per share.

        Formula:
            Risk/Share = Entry - Stop

        Args:
            entry: Entry price
            stop: Stop-loss price

        Returns:
            Risk per share (rounded to 2 decimals)
        """
        risk = entry - stop
        return round(risk, 2)

    @staticmethod
    def calculate_max_loss(portfolio_value: float, risk_percent: float) -> float:
        """
        Calculate maximum portfolio loss in PKR.

        Formula:
            Max Loss = Portfolio Value × (Risk% / 100)

        Args:
            portfolio_value: Total portfolio (PKR)
            risk_percent: Risk percentage (e.g., 1.0 for 1%)

        Returns:
            Max loss in PKR (rounded to 2 decimals)
        """
        max_loss = portfolio_value * (risk_percent / 100)
        return round(max_loss, 2)

    @staticmethod
    def calculate_position_size(max_loss: float, risk_per_share: float) -> int:
        """
        Calculate number of shares to buy.

        Formula:
            Position Size = Max Loss / Risk/Share

        Args:
            max_loss: Maximum allowable loss (PKR)
            risk_per_share: Risk per share (PKR)

        Returns:
            Number of shares (rounded down to integer)
        """
        if risk_per_share == 0:
            return 0
        position_size = max_loss / risk_per_share
        return int(position_size)

    @staticmethod
    def calculate_capital_required(position_size: int, entry_price: float) -> float:
        """
        Calculate total capital required for position.

        Formula:
            Capital Required = Position Size × Entry Price

        Args:
            position_size: Number of shares
            entry_price: Entry price per share

        Returns:
            Capital required (PKR, rounded to 2 decimals)
        """
        capital = position_size * entry_price
        return round(capital, 2)

    @staticmethod
    def calculate_allocation_pct(capital_required: float, portfolio_value: float) -> float:
        """
        Calculate portfolio allocation percentage.

        Formula:
            Allocation% = (Capital Required / Portfolio Value) × 100

        Args:
            capital_required: Capital to deploy
            portfolio_value: Total portfolio

        Returns:
            Allocation percentage (rounded to 2 decimals)
        """
        if portfolio_value == 0:
            return 0.0
        allocation = (capital_required / portfolio_value) * 100
        return round(allocation, 2)

    # ════════════════════════════════════════════════════════════════════════════
    # RISK/REWARD
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def calculate_risk_reward_ratio(
        entry: float,
        stop: float,
        target: float
    ) -> RiskRewardRatio:
        """
        Calculate Risk/Reward ratio for single target.

        Formula:
            Risk = Entry - Stop
            Reward = Target - Entry
            R/R = Reward / Risk

        Args:
            entry: Entry price
            stop: Stop-loss
            target: Target price

        Returns:
            RiskRewardRatio object with ratio (e.g., 3.0 = 1:3)
        """
        risk = entry - stop
        if risk == 0:
            ratio = 0.0
        else:
            reward = target - entry
            ratio = round(reward / risk, 2)

        return RiskRewardRatio(
            target_price=target,
            reward_per_share=round(target - entry, 2),
            ratio=ratio
        )

    @staticmethod
    def calculate_all_risk_reward_ratios(
        entry: float,
        stop: float,
        targets: List[float]
    ) -> List[RiskRewardRatio]:
        """
        Calculate R/R for all targets.

        Args:
            entry: Entry price
            stop: Stop-loss
            targets: List of target prices

        Returns:
            List of RiskRewardRatio objects
        """
        return [
            TradePlanCalculator.calculate_risk_reward_ratio(entry, stop, t)
            for t in targets
        ]

    # ════════════════════════════════════════════════════════════════════════════
    # LIQUIDITY ASSESSMENT
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def assess_liquidity(
        position_value: float,
        adv20_value: float,
        threshold_pct: float = 5.0
    ) -> Tuple[LiquidityCategory, float]:
        """
        Assess liquidity impact of position.

        Position / ADV20 categories:
            < 2%: LOW
            2-5%: MODERATE
            5-15%: HIGH
            > 15%: VERY_HIGH

        Args:
            position_value: Position size in PKR
            adv20_value: Average daily value (PKR)
            threshold_pct: Warning threshold (default 5%)

        Returns:
            (LiquidityCategory, position_pct_of_adv20)
        """
        if adv20_value == 0:
            return LiquidityCategory.MODERATE, 0.0

        pct = (position_value / adv20_value) * 100
        pct = round(pct, 2)

        if pct < 2:
            category = LiquidityCategory.LOW
        elif pct < 5:
            category = LiquidityCategory.MODERATE
        elif pct < 15:
            category = LiquidityCategory.HIGH
        else:
            category = LiquidityCategory.VERY_HIGH

        return category, pct

    # ════════════════════════════════════════════════════════════════════════════
    # CONSTRAINTS & CAPS
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def apply_concentration_cap(
        position_size: int,
        entry_price: float,
        portfolio_value: float,
        max_position_pct: float = 20.0
    ) -> Tuple[int, bool]:
        """
        Apply concentration limit to position size.

        If calculated position exceeds max_position_pct of portfolio,
        reduce position size to match cap.

        Args:
            position_size: Risk-based position size
            entry_price: Entry price
            portfolio_value: Total portfolio
            max_position_pct: Max % of portfolio

        Returns:
            (adjusted_position_size, was_cap_applied)
        """
        risk_based_capital = position_size * entry_price
        risk_based_pct = (risk_based_capital / portfolio_value) * 100

        if risk_based_pct > max_position_pct:
            max_capital = portfolio_value * (max_position_pct / 100)
            capped_position_size = int(max_capital / entry_price)
            return capped_position_size, True

        return position_size, False

    @staticmethod
    def apply_liquidity_cap(
        position_size: int,
        entry_price: float,
        adv20_value: float,
        max_liquidity_pct: float = 5.0
    ) -> Tuple[int, bool]:
        """
        Apply liquidity constraint to position size.

        If position would exceed max_liquidity_pct of ADV20,
        reduce position to stay within limit.

        Args:
            position_size: Current position size
            entry_price: Entry price
            adv20_value: Average daily value (PKR)
            max_liquidity_pct: Max % of ADV20

        Returns:
            (adjusted_position_size, was_cap_applied)
        """
        if adv20_value == 0:
            return position_size, False

        position_value = position_size * entry_price
        position_pct_of_adv20 = (position_value / adv20_value) * 100

        if position_pct_of_adv20 > max_liquidity_pct:
            max_value = adv20_value * (max_liquidity_pct / 100)
            capped_position_size = int(max_value / entry_price)
            return capped_position_size, True

        return position_size, False

    # ════════════════════════════════════════════════════════════════════════════
    # WARNING ENGINE
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def generate_warnings(
        entry: float,
        stop: float,
        targets: List[float],
        allocation_pct: float,
        position_pct_of_adv20: Optional[float],
        risk_reward_ratios: List[RiskRewardRatio]
    ) -> List[str]:
        """
        Generate non-blocking warnings for risk assessment.

        Args:
            entry: Entry price
            stop: Stop-loss
            targets: Target prices
            allocation_pct: Portfolio allocation %
            position_pct_of_adv20: Position as % of ADV20
            risk_reward_ratios: R/R for all targets

        Returns:
            List of warning strings
        """
        warnings = []

        # Concentration warning
        if allocation_pct > 25:
            warnings.append(
                f"⚠ Position exceeds 25% of portfolio ({allocation_pct:.1f}%)"
            )

        # Liquidity warning
        if position_pct_of_adv20 and position_pct_of_adv20 > 15:
            warnings.append(
                f"⚠ Position equals {position_pct_of_adv20:.1f}% of average daily value"
            )

        # Entry vs nearest support (crude check: stop is likely support)
        distance_to_stop_pct = ((entry - stop) / stop) * 100
        if distance_to_stop_pct > 10:
            warnings.append(
                f"⚠ Entry is {distance_to_stop_pct:.1f}% above stop-loss "
                "(wide risk zone)"
            )

        # R/R warnings
        for i, rr in enumerate(risk_reward_ratios):
            if rr.ratio < 1.0:
                warnings.append(
                    f"⚠ Target {i+1} gives risk/reward below 1:1 ({rr.ratio:.2f})"
                )

        return warnings

    # ════════════════════════════════════════════════════════════════════════════
    # MAIN CALCULATOR
    # ════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def calculate(input_params: CalculatorInput) -> CalculatorOutput:
        """
        Complete trade plan calculation.

        Answers all 10 critical questions:
        1. WHERE WOULD I ENTER? → entry_zone
        2. WHERE AM I WRONG? → stop_price
        3. WHERE WOULD I TAKE PROFIT? → target_prices
        4. HOW MUCH MONEY AM I RISKING? → max_loss
        5. HOW MANY SHARES SHOULD I BUY? → position_size
        6. IS THE RISK/REWARD ACCEPTABLE? → risk_reward_ratios
        7. IS THE POSITION TOO LARGE FOR MY PORTFOLIO? → allocation_pct
        8. IS THE STOCK LIQUID ENOUGH? → liquidity_assessment
        9. WHAT EVENTS COULD INVALIDATE THE TRADE? → (context module)
        10. WHAT IS MY EXIT PLAN BEFORE I ENTER? → targets + stop

        Args:
            input_params: CalculatorInput with all parameters

        Returns:
            CalculatorOutput with complete risk calculations
        """
        # Validate
        is_valid, errors = TradePlanCalculator.validate_inputs(input_params)
        if not is_valid:
            raise ValueError(f"Invalid inputs: {', '.join(errors)}")

        # ────────────────────────────────────────────────────────────────────────
        # RISK CALCULATIONS
        # ────────────────────────────────────────────────────────────────────────

        risk_per_share = TradePlanCalculator.calculate_risk_per_share(
            input_params.entry_price,
            input_params.stop_price
        )

        max_loss = TradePlanCalculator.calculate_max_loss(
            input_params.portfolio_value,
            input_params.risk_percent
        )

        position_size_risk_based = TradePlanCalculator.calculate_position_size(
            max_loss,
            risk_per_share
        )

        # ────────────────────────────────────────────────────────────────────────
        # CONSTRAINTS
        # ────────────────────────────────────────────────────────────────────────

        position_size = position_size_risk_based
        concentration_cap_applied = False
        liquidity_cap_applied = False

        # Apply concentration cap
        position_size, conc_cap = TradePlanCalculator.apply_concentration_cap(
            position_size,
            input_params.entry_price,
            input_params.portfolio_value,
            input_params.max_position_percent
        )
        concentration_cap_applied = conc_cap

        # Apply liquidity cap
        if input_params.adv20_value:
            position_size, liq_cap = TradePlanCalculator.apply_liquidity_cap(
                position_size,
                input_params.entry_price,
                input_params.adv20_value,
                input_params.max_position_liquidity_pct
            )
            liquidity_cap_applied = liq_cap

        # ────────────────────────────────────────────────────────────────────────
        # CAPITAL & ALLOCATION
        # ────────────────────────────────────────────────────────────────────────

        capital_required = TradePlanCalculator.calculate_capital_required(
            position_size,
            input_params.entry_price
        )

        allocation_pct = TradePlanCalculator.calculate_allocation_pct(
            capital_required,
            input_params.portfolio_value
        )

        # ────────────────────────────────────────────────────────────────────────
        # RISK/REWARD
        # ────────────────────────────────────────────────────────────────────────

        risk_reward_ratios = TradePlanCalculator.calculate_all_risk_reward_ratios(
            input_params.entry_price,
            input_params.stop_price,
            input_params.target_prices
        )

        # ────────────────────────────────────────────────────────────────────────
        # LIQUIDITY ASSESSMENT
        # ────────────────────────────────────────────────────────────────────────

        liquidity_category = None
        position_pct_of_adv20 = None

        if input_params.adv20_value:
            liquidity_category, position_pct_of_adv20 = \
                TradePlanCalculator.assess_liquidity(
                    capital_required,
                    input_params.adv20_value,
                    input_params.max_position_liquidity_pct
                )

        # ────────────────────────────────────────────────────────────────────────
        # WARNINGS
        # ────────────────────────────────────────────────────────────────────────

        warnings = TradePlanCalculator.generate_warnings(
            input_params.entry_price,
            input_params.stop_price,
            input_params.target_prices,
            allocation_pct,
            position_pct_of_adv20,
            risk_reward_ratios
        )

        # ────────────────────────────────────────────────────────────────────────
        # BUILD OUTPUT
        # ────────────────────────────────────────────────────────────────────────

        entry_zone = EntryZone(
            low=input_params.entry_price * 0.99,  # ±1% zone
            high=input_params.entry_price * 1.01,
            planned_entry=input_params.entry_price
        )

        risk_metrics = RiskMetrics(
            risk_per_share=risk_per_share,
            max_loss=max_loss,
            position_size=position_size,
            capital_required=capital_required,
            allocation_pct=allocation_pct
        )

        output = CalculatorOutput(
            entry_zone=entry_zone,
            stop_price=input_params.stop_price,
            target_prices=input_params.target_prices,
            risk_metrics=risk_metrics,
            risk_reward_ratios=risk_reward_ratios,
            position_size_before_caps=position_size_risk_based,
            concentration_cap_applied=concentration_cap_applied,
            liquidity_cap_applied=liquidity_cap_applied,
            liquidity_category=liquidity_category,
            position_pct_of_adv20=position_pct_of_adv20,
            warnings=warnings
        )

        return output


# ════════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def format_trade_plan_summary(output: CalculatorOutput) -> str:
    """
    Format calculator output as human-readable summary.

    Args:
        output: CalculatorOutput object

    Returns:
        Formatted string summary
    """
    lines = [
        "═" * 60,
        "TRADE PLAN SUMMARY",
        "═" * 60,
        "",
        "ENTRY",
        f"  Zone:          {output.entry_zone.low:.2f} - {output.entry_zone.high:.2f}",
        f"  Planned Entry: {output.entry_zone.planned_entry:.2f}",
        "",
        "STOP",
        f"  {output.stop_price:.2f}",
        "",
        "TARGETS",
    ]

    for i, target in enumerate(output.target_prices, 1):
        lines.append(f"  T{i}: {target:.2f}")

    lines.extend([
        "",
        "─" * 60,
        "RISK METRICS",
        "─" * 60,
        f"  Risk/Share:         {output.risk_metrics.risk_per_share:.2f} PKR",
        f"  Max Loss:           {output.risk_metrics.max_loss:,.2f} PKR",
        f"  Position Size:      {output.risk_metrics.position_size:,} shares",
        f"  Capital Required:   {output.risk_metrics.capital_required:,.2f} PKR",
        f"  Portfolio Weight:   {output.risk_metrics.allocation_pct:.2f}%",
        "",
        "─" * 60,
        "RISK / REWARD",
        "─" * 60,
    ])

    for i, rr in enumerate(output.risk_reward_ratios, 1):
        lines.append(f"  T{i}: 1 : {rr.ratio:.2f}")

    if output.liquidity_category:
        lines.extend([
            "",
            "─" * 60,
            "LIQUIDITY",
            "─" * 60,
            f"  Category:     {output.liquidity_category.value}",
            f"  Of ADV20:     {output.position_pct_of_adv20:.2f}%",
        ])

    if output.warnings:
        lines.extend([
            "",
            "─" * 60,
            "WARNINGS",
            "─" * 60,
        ])
        for warning in output.warnings:
            lines.append(f"  {warning}")

    lines.extend([
        "",
        "═" * 60,
    ])

    return "\n".join(lines)
