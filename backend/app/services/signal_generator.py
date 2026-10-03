"""Step 27: Signal Generator — Generate actionable trade signals.

Multi-signal framework:
- Buy/sell signals from technical + fundamental
- Signal strength (0-100%)
- Signal type: Entry, Exit, Stop-loss trigger
- Confirmation: signals must agree

Input: Technical + fundamental analysis
Output: TradeSignal (actionable entry/exit)
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """Signal action types."""
    ENTRY = "Entry"
    EXIT = "Exit"
    STOP_LOSS = "Stop Loss Trigger"


@dataclass
class TradeSignal:
    """Single trade signal."""
    ticker: str
    signal_type: SignalType
    strength: float  # 0-100%
    reason: str
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    suggested_stop: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "type": self.signal_type.value,
            "strength": round(self.strength, 1),
            "reason": self.reason,
        }


class SignalGenerator:
    """Generates trade signals."""

    def __init__(self):
        """Initialize signal generator."""
        self.logger = logging.getLogger(__name__)

    def generate_signals(
        self,
        ticker: str,
        technical_score: float,
        fundamental_score: float,
        momentum_pct: float,
        current_price: float,
        support_level: Optional[float] = None,
    ) -> List[TradeSignal]:
        """Generate trade signals.

        Args:
            ticker: Company ticker
            technical_score: Technical analysis score (0-100)
            fundamental_score: Fundamental score (0-100)
            momentum_pct: Price momentum percentage
            current_price: Current stock price
            support_level: Technical support level

        Returns:
            List of trade signals
        """
        signals = []

        try:
            # Entry signal: strong fundamental + positive momentum
            if fundamental_score > 70 and momentum_pct > 5:
                strength = (fundamental_score + momentum_pct) / 2
                signals.append(
                    TradeSignal(
                        ticker=ticker,
                        signal_type=SignalType.ENTRY,
                        strength=min(100, strength),
                        reason="Strong fundamentals with positive momentum",
                        entry_price=current_price,
                    )
                )

            # Exit signal: weakness in either technical or fundamental
            if fundamental_score < 40 or technical_score < 30:
                weakness_score = 100 - max(fundamental_score, technical_score)
                signals.append(
                    TradeSignal(
                        ticker=ticker,
                        signal_type=SignalType.EXIT,
                        strength=weakness_score,
                        reason="Deteriorating fundamentals or technicals",
                        exit_price=current_price,
                    )
                )

            # Stop loss: support level break
            if support_level and current_price < support_level:
                signals.append(
                    TradeSignal(
                        ticker=ticker,
                        signal_type=SignalType.STOP_LOSS,
                        strength=80.0,
                        reason="Support level broken",
                        suggested_stop=support_level * 0.95,
                    )
                )

            self.logger.info(
                f"Generated {len(signals)} signals for {ticker}"
            )
            return signals

        except Exception as e:
            self.logger.error(f"Error generating signals: {e}")
            return []
