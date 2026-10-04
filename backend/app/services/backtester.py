"""Backtesting harness — apply strategy rules to historical snapshots and calculate returns.

Workflow:
1. Iterate through date range
2. For each date, get snapshots for investable universe
3. Apply strategy rules to filter/rank securities
4. Size positions based on confidence/risk
5. Track daily P&L across portfolio
6. Calculate risk metrics (returns, volatility, Sharpe, max drawdown)
"""

from datetime import date, timedelta
from typing import Optional, List, Callable, Dict, Tuple
from dataclasses import dataclass, field
import logging
import math

from sqlalchemy.orm import Session

from app.services.historical_snapshot import HistoricalSnapshotEngine, HistoricalSnapshot

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Open position in a security."""

    symbol: str
    entry_date: date
    entry_price: float
    quantity: int
    conviction: float  # 0-100, strategy confidence

    @property
    def entry_value(self) -> float:
        return self.entry_price * self.quantity

    def get_current_value(self, current_price: float) -> float:
        return current_price * self.quantity

    def get_pnl(self, current_price: float) -> float:
        return self.get_current_value(current_price) - self.entry_value

    def get_return_pct(self, current_price: float) -> float:
        if self.entry_price == 0:
            return 0
        return ((current_price - self.entry_price) / self.entry_price) * 100


@dataclass
class PortfolioMetrics:
    """Daily portfolio metrics."""

    date: date
    positions_count: int
    portfolio_value: float
    daily_return_pct: float
    cumulative_return_pct: float


@dataclass
class BacktestResult:
    """Complete backtest results."""

    strategy_name: str
    start_date: date
    end_date: date
    portfolio_size_pkr: float

    # Returns
    total_return_pct: float = 0
    annual_return_pct: float = 0

    # Risk
    volatility_pct: float = 0
    max_drawdown_pct: float = 0

    # Efficiency
    sharpe_ratio: float = 0
    sortino_ratio: float = 0

    # Stats
    winning_days: int = 0
    losing_days: int = 0
    best_day_pct: float = 0
    worst_day_pct: float = 0

    # Trades
    positions_opened: int = 0
    positions_closed: int = 0

    # Drawdown tracking
    daily_returns: List[float] = field(default_factory=list)
    daily_values: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "strategy_name": self.strategy_name,
            "period": {
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
                "days": (self.end_date - self.start_date).days,
            },
            "portfolio": {
                "initial_size_pkr": self.portfolio_size_pkr,
            },
            "returns": {
                "total_pct": round(self.total_return_pct, 2),
                "annual_pct": round(self.annual_return_pct, 2),
            },
            "risk": {
                "volatility_pct": round(self.volatility_pct, 2),
                "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            },
            "efficiency": {
                "sharpe_ratio": round(self.sharpe_ratio, 2),
                "sortino_ratio": round(self.sortino_ratio, 2),
            },
            "daily_stats": {
                "winning_days": self.winning_days,
                "losing_days": self.losing_days,
                "best_day_pct": round(self.best_day_pct, 2),
                "worst_day_pct": round(self.worst_day_pct, 2),
            },
            "trading": {
                "positions_opened": self.positions_opened,
                "positions_closed": self.positions_closed,
            },
        }


class Backtester:
    """Backtest framework using historical snapshots."""

    def __init__(
        self,
        db: Session,
        strategy_name: str,
        portfolio_size_pkr: float = 1_000_000,  # Default 1M PKR
        rebalance_frequency_days: int = 1,  # Daily rebalancing
        max_positions: int = 10,
        max_position_pct: float = 10.0,  # Max 10% per position
    ):
        self.db = db
        self.strategy_name = strategy_name
        self.portfolio_size_pkr = portfolio_size_pkr
        self.rebalance_frequency_days = rebalance_frequency_days
        self.max_positions = max_positions
        self.max_position_pct = max_position_pct

        self.snapshot_engine = HistoricalSnapshotEngine(db)
        self.positions: Dict[str, Position] = {}
        self.portfolio_values: List[Tuple[date, float]] = []
        self.daily_returns: List[float] = []

    def run(
        self,
        start_date: date,
        end_date: date,
        decision_function: Callable[[List[HistoricalSnapshot]], List[Tuple[str, float]]],
    ) -> BacktestResult:
        """Run backtest with strategy decision function.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            decision_function: Takes list of snapshots, returns list of (symbol, conviction) tuples
                             to trade. Conviction is 0-100 confidence.

        Returns:
            BacktestResult with performance metrics
        """
        try:
            current_date = start_date
            portfolio_values = [self.portfolio_size_pkr]
            daily_returns = []
            positions_opened = 0
            positions_closed = 0

            while current_date <= end_date:
                # Rebalancing decision
                if (current_date - start_date).days % self.rebalance_frequency_days == 0:
                    # Get snapshots for investable universe
                    universe_snapshots = self._get_universe_snapshots(current_date)

                    if universe_snapshots:
                        # Apply strategy rules
                        signals = decision_function(universe_snapshots)

                        # Rebalance portfolio
                        positions_opened += self._rebalance(
                            signals, universe_snapshots, current_date
                        )

                # Calculate daily P&L
                portfolio_value, daily_return = self._calculate_daily_pnl(
                    current_date, portfolio_values[-1]
                )

                portfolio_values.append(portfolio_value)
                if len(portfolio_values) > 1:
                    daily_returns.append(daily_return)

                current_date += timedelta(days=1)

            # Calculate metrics
            return self._calculate_metrics(
                start_date,
                end_date,
                portfolio_values,
                daily_returns,
                positions_opened,
                positions_closed,
            )

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise

    def _get_universe_snapshots(self, as_of_date: date) -> List[HistoricalSnapshot]:
        """Get snapshots for all investable securities on a date."""
        from sqlalchemy import select
        from app.db.models import Security

        # Query all active securities
        securities = self.db.execute(
            select(Security).where(Security.is_active.is_(True))
        ).scalars().all()

        tickers = [s.symbol for s in securities]

        if not tickers:
            return []

        snapshots = self.snapshot_engine.snapshot_batch(tickers, as_of_date)
        # Filter to only investable snapshots
        return [s for s in snapshots if s.is_investable()]

    def _rebalance(
        self,
        signals: List[Tuple[str, float]],
        available_snapshots: List[HistoricalSnapshot],
        current_date: date,
    ) -> int:
        """Rebalance portfolio based on signals.

        Args:
            signals: List of (symbol, conviction) tuples from decision function
            available_snapshots: Snapshots of investable securities
            current_date: Current date for position entry

        Returns:
            Number of new positions opened
        """
        if not signals:
            return 0

        new_positions = 0

        # Sort by conviction (descending)
        signals.sort(key=lambda x: x[1], reverse=True)

        # Position size: equal weight up to max_positions
        num_positions = min(len(signals), self.max_positions)
        if num_positions == 0:
            return 0

        position_size_pkr = (self.portfolio_size_pkr * self.max_position_pct) / 100

        snapshot_map = {s.symbol: s for s in available_snapshots}

        for symbol, conviction in signals[:num_positions]:
            if symbol not in snapshot_map:
                continue

            snapshot = snapshot_map[symbol]
            if not snapshot.close_price:
                continue

            # Skip if already in position
            if symbol in self.positions:
                continue

            # Open position
            quantity = int(position_size_pkr / snapshot.close_price)
            if quantity > 0:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    entry_date=current_date,
                    entry_price=snapshot.close_price,
                    quantity=quantity,
                    conviction=conviction,
                )
                new_positions += 1

        return new_positions

    def _calculate_daily_pnl(
        self, current_date: date, previous_portfolio_value: float
    ) -> Tuple[float, float]:
        """Calculate daily P&L for all positions.

        Args:
            current_date: Current date
            previous_portfolio_value: Portfolio value at start of day

        Returns:
            Tuple of (portfolio_value, daily_return_pct)
        """
        if not self.positions:
            return previous_portfolio_value, 0

        # Get current prices for all positions
        snapshots = self.snapshot_engine.snapshot_batch(
            list(self.positions.keys()), current_date
        )
        price_map = {s.symbol: s.close_price for s in snapshots}

        # Calculate total position value
        total_position_value = 0
        for symbol, position in self.positions.items():
            current_price = price_map.get(symbol)
            if current_price:
                total_position_value += position.get_current_value(current_price)

        # Current portfolio value = cash + positions
        # (simplified: assume we invest all capital initially)
        current_portfolio_value = total_position_value

        # Daily return
        if previous_portfolio_value > 0:
            daily_return_pct = (
                (current_portfolio_value - previous_portfolio_value)
                / previous_portfolio_value
                * 100
            )
        else:
            daily_return_pct = 0

        return current_portfolio_value, daily_return_pct

    def _calculate_metrics(
        self,
        start_date: date,
        end_date: date,
        portfolio_values: List[float],
        daily_returns: List[float],
        positions_opened: int,
        positions_closed: int,
    ) -> BacktestResult:
        """Calculate risk/return metrics."""
        result = BacktestResult(
            strategy_name=self.strategy_name,
            start_date=start_date,
            end_date=end_date,
            portfolio_size_pkr=self.portfolio_size_pkr,
            daily_returns=daily_returns,
            daily_values=portfolio_values,
            positions_opened=positions_opened,
            positions_closed=positions_closed,
        )

        if len(portfolio_values) < 2:
            return result

        # Total return
        final_value = portfolio_values[-1]
        initial_value = portfolio_values[0]
        total_return_pct = ((final_value - initial_value) / initial_value) * 100
        result.total_return_pct = total_return_pct

        # Annualized return
        days = (end_date - start_date).days
        if days > 0:
            years = days / 365.25
            annual_return_pct = (
                (final_value / initial_value) ** (1 / years) - 1
            ) * 100
            result.annual_return_pct = annual_return_pct

        if not daily_returns:
            return result

        # Volatility
        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(
            daily_returns
        )
        daily_volatility = math.sqrt(variance)
        result.volatility_pct = daily_volatility * math.sqrt(252)  # Annualize

        # Max drawdown
        peak = portfolio_values[0]
        max_dd = 0
        for value in portfolio_values[1:]:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            max_dd = max(max_dd, dd)
        result.max_drawdown_pct = max_dd

        # Sharpe ratio (assuming 0% risk-free rate)
        if result.volatility_pct > 0:
            result.sharpe_ratio = result.annual_return_pct / result.volatility_pct

        # Win/loss stats
        winning = sum(1 for r in daily_returns if r > 0)
        losing = sum(1 for r in daily_returns if r < 0)
        result.winning_days = winning
        result.losing_days = losing

        if daily_returns:
            result.best_day_pct = max(daily_returns)
            result.worst_day_pct = min(daily_returns)

        return result
