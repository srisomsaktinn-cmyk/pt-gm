"""
Deterministic State Machine Engine for Strategy V2:
RSI(14) Trend Pullback Re-entry + Kaufman Efficiency Ratio (ER > 0.40) Regime Filter.
"""

from typing import Optional, List
from datetime import datetime
from .states import StrategyState, SignalType, TradingSignal, StateTransitionRecord


class RSIStateMachineV2:
    """
    Strategy V2 State Machine with Kaufman ER Regime Filter.
    
    Regime Rules:
      Bullish Regime: ER(14) > 0.40 AND Close > Close[14]
      Bearish Regime: ER(14) > 0.40 AND Close < Close[14]
      No Trade (Chop): ER(14) <= 0.40
    """

    def __init__(
        self,
        upper_level: float = 60.0,
        pullback_level: float = 50.0,
        lower_level: float = 40.0,
        er_threshold: float = 0.40
    ):
        self.upper_level = upper_level
        self.pullback_level = pullback_level
        self.lower_level = lower_level
        self.er_threshold = er_threshold

        self._state: StrategyState = StrategyState.IDLE
        self._prev_rsi: Optional[float] = None
        self._transition_history: List[StateTransitionRecord] = []

    @property
    def current_state(self) -> StrategyState:
        return self._state

    @property
    def transition_history(self) -> List[StateTransitionRecord]:
        return list(self._transition_history)

    def reset(self) -> None:
        self._state = StrategyState.IDLE
        self._prev_rsi = None
        self._transition_history.clear()

    @staticmethod
    def cross_above(prev: Optional[float], curr: float, level: float) -> bool:
        if prev is None: return False
        return (prev <= level) and (curr > level)

    @staticmethod
    def cross_below(prev: Optional[float], curr: float, level: float) -> bool:
        if prev is None: return False
        return (prev >= level) and (curr < level)

    def notify_order_executed(self, bar_index: int, timestamp: datetime) -> None:
        if self._state == StrategyState.LONG_ENTRY:
            old_state = self._state
            self._state = StrategyState.BULLISH_TRADED
            self._record_transition(bar_index, timestamp, old_state, self._state, self._prev_rsi, "Long executed -> BULLISH_TRADED")
        elif self._state == StrategyState.SHORT_ENTRY:
            old_state = self._state
            self._state = StrategyState.BEARISH_TRADED
            self._record_transition(bar_index, timestamp, old_state, self._state, self._prev_rsi, "Short executed -> BEARISH_TRADED")

    def _record_transition(
        self,
        bar_index: int,
        timestamp: datetime,
        prev_state: StrategyState,
        new_state: StrategyState,
        rsi: Optional[float],
        reason: str
    ) -> None:
        if prev_state != new_state:
            self._transition_history.append(StateTransitionRecord(
                bar_index=bar_index,
                timestamp=timestamp,
                previous_state=prev_state,
                current_state=new_state,
                rsi=rsi,
                transition_reason=reason
            ))

    def evaluate_bar(
        self,
        bar_index: int,
        timestamp: datetime,
        current_rsi: Optional[float],
        current_er: Optional[float],
        close_change_14: Optional[float]
    ) -> Optional[TradingSignal]:
        if current_rsi is None or current_er is None or close_change_14 is None:
            return None

        # Auto-resolve transient states
        if self._state == StrategyState.LONG_ENTRY:
            self._state = StrategyState.BULLISH_TRADED
        elif self._state == StrategyState.SHORT_ENTRY:
            self._state = StrategyState.BEARISH_TRADED

        signal: Optional[TradingSignal] = None
        old_state = self._state
        prev_rsi_val = self._prev_rsi

        # Regime evaluation
        is_bullish_regime = (current_er > self.er_threshold) and (close_change_14 > 0)
        is_bearish_regime = (current_er > self.er_threshold) and (close_change_14 < 0)

        # ── State-specific transition evaluation ──

        if self._state == StrategyState.IDLE:
            if is_bullish_regime and current_rsi > self.upper_level:
                self._state = StrategyState.BULLISH_TREND
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bullish Trend started (RSI={current_rsi:.1f}, ER={current_er:.2f} > {self.er_threshold})")
            elif is_bearish_regime and current_rsi < self.lower_level:
                self._state = StrategyState.BEARISH_TREND
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bearish Trend started (RSI={current_rsi:.1f}, ER={current_er:.2f} > {self.er_threshold})")

        elif self._state == StrategyState.BULLISH_TREND:
            # Priority 1: Trend reversal (RSI < 40)
            if current_rsi < self.lower_level:
                # If bearish regime confirmed, flip to BEARISH_TREND, else IDLE
                self._state = StrategyState.BEARISH_TREND if is_bearish_regime else StrategyState.IDLE
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bullish cycle ended: RSI < {self.lower_level} -> {'BEARISH_TREND' if is_bearish_regime else 'IDLE'}")
            # Priority 2: Pullback detection (cross below 50 while > 40)
            elif self.cross_below(prev_rsi_val, current_rsi, self.pullback_level) and current_rsi > self.lower_level:
                self._state = StrategyState.BULLISH_PULLBACK
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bullish pullback detected: RSI crossed below {self.pullback_level}")

        elif self._state == StrategyState.BULLISH_PULLBACK:
            # Priority 1: Invalidation (RSI < 40)
            if current_rsi < self.lower_level:
                self._state = StrategyState.BEARISH_TREND if is_bearish_regime else StrategyState.IDLE
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bullish setup invalidated: RSI < {self.lower_level} -> {'BEARISH_TREND' if is_bearish_regime else 'IDLE'}")
            # Priority 2: Trigger (cross back above 50)
            elif self.cross_above(prev_rsi_val, current_rsi, self.pullback_level):
                self._state = StrategyState.LONG_ENTRY
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Long trigger fired: RSI crossed back above {self.pullback_level}")
                signal = TradingSignal(
                    signal_type=SignalType.LONG_ENTRY_SIGNAL,
                    bar_index=bar_index,
                    timestamp=timestamp,
                    rsi_value=current_rsi,
                    state_at_signal=StrategyState.LONG_ENTRY,
                    reason=f"V2 Long trigger (RSI crossed > {self.pullback_level}, ER={current_er:.2f})"
                )

        elif self._state == StrategyState.BULLISH_TRADED:
            # Long Exit strictly when RSI < 40
            if current_rsi < self.lower_level:
                self._state = StrategyState.BEARISH_TREND if is_bearish_regime else StrategyState.IDLE
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Long Exit: RSI < {self.lower_level} -> {'BEARISH_TREND' if is_bearish_regime else 'IDLE'}")
                signal = TradingSignal(
                    signal_type=SignalType.LONG_EXIT_SIGNAL,
                    bar_index=bar_index,
                    timestamp=timestamp,
                    rsi_value=current_rsi,
                    state_at_signal=StrategyState.BULLISH_TRADED,
                    reason=f"Long strategy exit: RSI ({current_rsi:.2f}) < {self.lower_level}"
                )

        elif self._state == StrategyState.BEARISH_TREND:
            # Priority 1: Trend reversal (RSI > 60)
            if current_rsi > self.upper_level:
                self._state = StrategyState.BULLISH_TREND if is_bullish_regime else StrategyState.IDLE
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bearish cycle ended: RSI > {self.upper_level} -> {'BULLISH_TREND' if is_bullish_regime else 'IDLE'}")
            # Priority 2: Pullback detection (cross above 50 while < 60)
            elif self.cross_above(prev_rsi_val, current_rsi, self.pullback_level) and current_rsi < self.upper_level:
                self._state = StrategyState.BEARISH_PULLBACK
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bearish pullback detected: RSI crossed above {self.pullback_level}")

        elif self._state == StrategyState.BEARISH_PULLBACK:
            # Priority 1: Invalidation (RSI > 60)
            if current_rsi > self.upper_level:
                self._state = StrategyState.BULLISH_TREND if is_bullish_regime else StrategyState.IDLE
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bearish setup invalidated: RSI > {self.upper_level} -> {'BULLISH_TREND' if is_bullish_regime else 'IDLE'}")
            # Priority 2: Trigger (cross back below 50)
            elif self.cross_below(prev_rsi_val, current_rsi, self.pullback_level):
                self._state = StrategyState.SHORT_ENTRY
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Short trigger fired: RSI crossed back below {self.pullback_level}")
                signal = TradingSignal(
                    signal_type=SignalType.SHORT_ENTRY_SIGNAL,
                    bar_index=bar_index,
                    timestamp=timestamp,
                    rsi_value=current_rsi,
                    state_at_signal=StrategyState.SHORT_ENTRY,
                    reason=f"V2 Short trigger (RSI crossed < {self.pullback_level}, ER={current_er:.2f})"
                )

        elif self._state == StrategyState.BEARISH_TRADED:
            # Short Exit strictly when RSI > 60
            if current_rsi > self.upper_level:
                self._state = StrategyState.BULLISH_TREND if is_bullish_regime else StrategyState.IDLE
                self._record_transition(bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Short Exit: RSI > {self.upper_level} -> {'BULLISH_TREND' if is_bullish_regime else 'IDLE'}")
                signal = TradingSignal(
                    signal_type=SignalType.SHORT_EXIT_SIGNAL,
                    bar_index=bar_index,
                    timestamp=timestamp,
                    rsi_value=current_rsi,
                    state_at_signal=StrategyState.BEARISH_TRADED,
                    reason=f"Short strategy exit: RSI ({current_rsi:.2f}) > {self.upper_level}"
                )

        self._prev_rsi = current_rsi
        return signal
