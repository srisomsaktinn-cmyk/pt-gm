"""
State Machine enumeration and data transfer objects for RSI Strategy V1.
Locked states and signal types.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class StrategyState(str, Enum):
    """
    Locked 9 states of the RSI Trend Pullback Re-entry state machine.
    """
    IDLE = "IDLE"
    BULLISH_TREND = "BULLISH_TREND"
    BULLISH_PULLBACK = "BULLISH_PULLBACK"
    LONG_ENTRY = "LONG_ENTRY"
    BULLISH_TRADED = "BULLISH_TRADED"
    BEARISH_TREND = "BEARISH_TREND"
    BEARISH_PULLBACK = "BEARISH_PULLBACK"
    SHORT_ENTRY = "SHORT_ENTRY"
    BEARISH_TRADED = "BEARISH_TRADED"


class PositionSide(str, Enum):
    """
    Trading position direction.
    """
    NONE = "NONE"
    LONG = "LONG"
    SHORT = "SHORT"


class SignalType(str, Enum):
    """
    Trading signals emitted at bar close for execution at next bar open.
    """
    NO_SIGNAL = "NO_SIGNAL"
    LONG_ENTRY_SIGNAL = "LONG_ENTRY_SIGNAL"
    SHORT_ENTRY_SIGNAL = "SHORT_ENTRY_SIGNAL"
    LONG_EXIT_SIGNAL = "LONG_EXIT_SIGNAL"
    SHORT_EXIT_SIGNAL = "SHORT_EXIT_SIGNAL"


@dataclass(frozen=True)
class TradingSignal:
    """
    Signal generated strictly at candle close T.
    """
    signal_type: SignalType
    bar_index: int
    timestamp: datetime
    rsi_value: float
    state_at_signal: StrategyState
    reason: str


@dataclass(frozen=True)
class StateTransitionRecord:
    """
    Audit record for every state machine transition.
    """
    bar_index: int
    timestamp: datetime
    previous_state: StrategyState
    current_state: StrategyState
    rsi: Optional[float]
    transition_reason: str
