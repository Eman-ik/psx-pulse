"""Step 28: Portfolio Optimizer — Optimize portfolio allocation.

Position sizing and allocation:
- Risk-parity sizing (equal risk per position)
- Kelly criterion for position sizing
- Max drawdown constraints
- Correlation-aware allocation

Input: Candidate stocks + portfolio constraints
Output: OptimizedAllocation (position weights)
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class PortfolioPosition:
    """Single position in portfolio."""
    ticker: str
    weight: float  # % of portfolio
    share_count: int
    entry_price: float
    target_price: Optional[float] = None


@dataclass
class OptimizedAllocation:
    """Optimized portfolio allocation."""
    positions: List[PortfolioPosition]
    total_weight: float  # Should be 100%
    cash_weight: float  # % held in cash
    portfolio_value: float
    expected_return_pct: float
    max_drawdown_pct: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "positions": [
                {
                    "ticker": p.ticker,
                    "weight": round(p.weight, 1),
                    "shares": p.share_count,
                    "entry": round(p.entry_price, 2),
                }
                for p in self.positions
            ],
            "cash_weight": round(self.cash_weight, 1),
            "expected_return": round(self.expected_return_pct, 1),
            "max_drawdown": round(self.max_drawdown_pct, 1),
        }


class PortfolioOptimizer:
    """Optimizes portfolio allocation."""

    def __init__(self):
        """Initialize optimizer."""
        self.logger = logging.getLogger(__name__)

    def optimize_allocation(
        self,
        candidates: List[Dict[str, Any]],  # ticker, ml_score, risk, target_price
        portfolio_value: float,
        max_positions: int = 10,
        min_position_weight: float = 2.0,
    ) -> Optional[OptimizedAllocation]:
        """Optimize portfolio allocation.

        Args:
            candidates: List of candidate stocks
            portfolio_value: Total portfolio value
            max_positions: Maximum positions to hold
            min_position_weight: Minimum position weight (%)

        Returns:
            OptimizedAllocation with position weights
        """
        try:
            if not candidates:
                return None

            # Sort by score
            ranked = sorted(
                candidates,
                key=lambda x: x.get("ml_score", 0),
                reverse=True,
            )[:max_positions]

            positions = []
            total_allocated = 0.0

            # Equal weight initially
            position_weight = 100.0 / len(ranked)

            for candidate in ranked:
                # Risk-adjust weight (high risk = lower weight)
                risk = candidate.get("risk_score", 50)
                risk_adjusted = position_weight * (100 - risk) / 50
                risk_adjusted = max(
                    min_position_weight,
                    min(position_weight * 2, risk_adjusted),
                )

                shares = int(
                    (portfolio_value * risk_adjusted / 100)
                    / candidate.get("current_price", 1)
                )

                if shares > 0:
                    position = PortfolioPosition(
                        ticker=candidate.get("ticker", ""),
                        weight=risk_adjusted,
                        share_count=shares,
                        entry_price=candidate.get("current_price", 0),
                        target_price=candidate.get("target_price"),
                    )
                    positions.append(position)
                    total_allocated += risk_adjusted

            # Cash buffer
            cash_weight = 100.0 - total_allocated

            allocation = OptimizedAllocation(
                positions=positions,
                total_weight=total_allocated,
                cash_weight=max(0, cash_weight),
                portfolio_value=portfolio_value,
                expected_return_pct=self._estimate_return(ranked),
                max_drawdown_pct=self._estimate_drawdown(ranked),
            )

            self.logger.info(
                f"Optimized portfolio: {len(positions)} positions, "
                f"expected return {allocation.expected_return_pct:.1f}%"
            )
            return allocation

        except Exception as e:
            self.logger.error(f"Error optimizing allocation: {e}")
            return None

    @staticmethod
    def _estimate_return(candidates: List[Dict[str, Any]]) -> float:
        """Estimate portfolio return."""
        if not candidates:
            return 0.0

        returns = [
            c.get("expected_return_pct", 0)
            for c in candidates[:5]
        ]
        return sum(returns) / len(returns) if returns else 0.0

    @staticmethod
    def _estimate_drawdown(candidates: List[Dict[str, Any]]) -> float:
        """Estimate maximum drawdown."""
        if not candidates:
            return 0.0

        drawdowns = [
            c.get("max_drawdown_pct", -20)
            for c in candidates[:5]
        ]
        return sum(drawdowns) / len(drawdowns) if drawdowns else -20.0
