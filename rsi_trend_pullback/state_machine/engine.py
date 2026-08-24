"""
Deterministic State Machine Engine for RSI(14) Trend Pullback Re-entry.
Strictly implements the locked specification with prioritized state transitions
and complete transition audit logging.
"""

from typing import Optional, List, Tuple
from datetime import datetime
from .states import StrategyState, SignalType, TradingSignal, StateTransitionRecord


class RSIStateMachine:
    """
    Locked State Machine implementation.
    
    Levels:
      upper_level    = 60.0
      pullback_level = 50.0
      lower_level    = 40.0
    """

    def __init__(
        self,
        upper_level: float = 60.0,
        pullback_level: float = 50.0,
        lower_level: float = 40.0
    ):
        self.upper_level: float = upper_level
        self.pullback_level: float = pullback_level
        self.lower_level: float = lower_level

        self._state: StrategyState = StrategyState.IDLE
        self._prev_rsi: Optional[float] = None
        self._transition_history: List[StateTransitionRecord] = []

    @property
    def current_state(self) -> StrategyState:
        return self._state

    @property
    def prev_rsi(self) -> Optional[float]:
        return self._prev_rsi

    @property
    def transition_history(self) -> List[StateTransitionRecord]:
        return list(self._transition_history)

    def reset(self) -> None:
        """
        Resets state machine to initial IDLE state.
        """
        self._state = StrategyState.IDLE
        self._prev_rsi = None
        self._transition_history.clear()

    @staticmethod
    def cross_above(prev: Optional[float], curr: float, level: float) -> bool:
        """
        Cross Above: prev <= level AND curr > level
        """
        if prev is None:
            return False
        return (prev <= level) and (curr > level)

    @staticmethod
    def cross_below(prev: Optional[float], curr: float, level: float) -> bool:
        """
        Cross Below: prev >= level AND curr < level
        """
        if prev is None:
            return False
        return (prev >= level) and (curr < level)

    def notify_order_executed(self, bar_index: int, timestamp: datetime) -> None:
        """
        Called when a pending order executes at bar open.
        Converts transient LONG_ENTRY / SHORT_ENTRY into TRADED states.
        """
        if self._state == StrategyState.LONG_ENTRY:
            old_state = self._state
            self._state = StrategyState.BULLISH_TRADED
            self._record_transition(
                bar_index=bar_index,
                timestamp=timestamp,
                prev_state=old_state,
                new_state=self._state,
                rsi=self._prev_rsi,
                reason="Long order executed at next bar open -> BULLISH_TRADED"
            )
        elif self._state == StrategyState.SHORT_ENTRY:
            old_state = self._state
            self._state = StrategyState.BEARISH_TRADED
            self._record_transition(
                bar_index=bar_index,
                timestamp=timestamp,
                prev_state=old_state,
                new_state=self._state,
                rsi=self._prev_rsi,
                reason="Short order executed at next bar open -> BEARISH_TRADED"
            )

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
            record = StateTransitionRecord(
                bar_index=bar_index,
                timestamp=timestamp,
                previous_state=prev_state,
                current_state=new_state,
                rsi=rsi,
                transition_reason=reason
            )
            self._transition_history.append(record)

    def evaluate_bar(
        self,
        bar_index: int,
        timestamp: datetime,
        current_rsi: Optional[float]
    ) -> Optional[TradingSignal]:
        """
        Evaluates transitions at candle CLOSE.
        Returns a TradingSignal if an entry or exit trigger occurred at this candle close, else None.
        """
        # If RSI not available (warm-up), stay in current state (IDLE)
        if current_rsi is None:
            return None

        # Auto-resolve any leftover transient states if notify_order_executed was not called
        if self._state == StrategyState.LONG_ENTRY:
            self._record_transition(
                bar_index=bar_index,
                timestamp=timestamp,
                prev_state=self._state,
                new_state=StrategyState.BULLISH_TRADED,
                rsi=self._prev_rsi,
                reason="Auto transition LONG_ENTRY -> BULLISH_TRADED on bar evaluate"
            )
            self._state = StrategyState.BULLISH_TRADED
        elif self._state == StrategyState.SHORT_ENTRY:
            self._record_transition(
                bar_index=bar_index,
                timestamp=timestamp,
                prev_state=self._state,
                new_state=StrategyState.BEARISH_TRADED,
                rsi=self._prev_rsi,
                reason="Auto transition SHORT_ENTRY -> BEARISH_TRADED on bar evaluate"
            )
            self._state = StrategyState.BEARISH_TRADED

        signal: Optional[TradingSignal] = None
        old_state = self._state
        prev_rsi_val = self._prev_rsi

        # ── State-specific transition evaluation (Priority Ordered) ──

        if self._state == StrategyState.IDLE:
            if current_rsi > self.upper_level:
                self._state = StrategyState.BULLISH_TREND
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"RSI ({current_rsi:.2f}) > {self.upper_level} -> Bullish Trend started"
                )
            elif current_rsi < self.lower_level:
                self._state = StrategyState.BEARISH_TREND
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"RSI ({current_rsi:.2f}) < {self.lower_level} -> Bearish Trend started"
                )

        elif self._state == StrategyState.BULLISH_TREND:
            # Priority 1: Trend reversal (RSI < 40)
            if current_rsi < self.lower_level:
                self._state = StrategyState.BEARISH_TREND
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bullish cycle ended: RSI ({current_rsi:.2f}) < {self.lower_level} -> Flip to Bearish Trend"
                )
            # Priority 2: Pullback detection (cross below 50 while remaining > 40)
            elif self.cross_below(prev_rsi_val, current_rsi, self.pullback_level) and current_rsi > self.lower_level:
                self._state = StrategyState.BULLISH_PULLBACK
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bullish pullback detected: RSI crossed below {self.pullback_level} (current={current_rsi:.2f})"
                )

        elif self._state == StrategyState.BULLISH_PULLBACK:
            # Priority 1: Invalidation (RSI < 40)
            if current_rsi < self.lower_level:
                self._state = StrategyState.BEARISH_TREND
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bullish setup invalidated: RSI ({current_rsi:.2f}) < {self.lower_level} -> Flip to Bearish Trend"
                )
            # Priority 2: Long trigger (cross back above 50)
            elif self.cross_above(prev_rsi_val, current_rsi, self.pullback_level):
                self._state = StrategyState.LONG_ENTRY
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Long trigger fired: RSI crossed back above {self.pullback_level} (prev={prev_rsi_val}, curr={current_rsi:.2f})"
                )
                signal = TradingSignal(
                    signal_type=SignalType.LONG_ENTRY_SIGNAL,
                    bar_index=bar_index,
                    timestamp=timestamp,
                    rsi_value=current_rsi,
                    state_at_signal=StrategyState.LONG_ENTRY,
                    reason=f"Bullish Pullback re-entry trigger: RSI crossed above {self.pullback_level}"
                )

        elif self._state == StrategyState.BULLISH_TRADED:
            # Priority 1: Cycle end & Long Exit (RSI < 40)
            if current_rsi < self.lower_level:
                self._state = StrategyState.BEARISH_TREND
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bullish cycle ended: RSI ({current_rsi:.2f}) < {self.lower_level} -> Long Exit Signal + Flip to Bearish Trend"
                )
                signal = TradingSignal(
                    signal_type=SignalType.LONG_EXIT_SIGNAL,
                    bar_index=bar_index,
                    timestamp=timestamp,
                    rsi_value=current_rsi,
                    state_at_signal=StrategyState.BULLISH_TRADED,
                    reason=f"Long strategy exit: RSI ({current_rsi:.2f}) < {self.lower_level}"
                )
            # Pullbacks in BULLISH_TRADED are completely ignored (1 trade per cycle)

        elif self._state == StrategyState.BEARISH_TREND:
            # Priority 1: Trend reversal (RSI > 60)
            if current_rsi > self.upper_level:
                self._state = StrategyState.BULLISH_TREND
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bearish cycle ended: RSI ({current_rsi:.2f}) > {self.upper_level} -> Flip to Bullish Trend"
                )
            # Priority 2: Pullback detection (cross above 50 while remaining < 60)
            elif self.cross_above(prev_rsi_val, current_rsi, self.pullback_level) and current_rsi < self.upper_level:
                self._state = StrategyState.BEARISH_PULLBACK
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bearish pullback detected: RSI crossed above {self.pullback_level} (current={current_rsi:.2f})"
                )

        elif self._state == StrategyState.BEARISH_PULLBACK:
            # Priority 1: Invalidation (RSI > 60)
            if current_rsi > self.upper_level:
                self._state = StrategyState.BULLISH_TREND
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bearish setup invalidated: RSI ({current_rsi:.2f}) > {self.upper_level} -> Flip to Bullish Trend"
                )
            # Priority 2: Short trigger (cross back below 50)
            elif self.cross_below(prev_rsi_val, current_rsi, self.pullback_level):
                self._state = StrategyState.SHORT_ENTRY
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Short trigger fired: RSI crossed back below {self.pullback_level} (prev={prev_rsi_val}, curr={current_rsi:.2f})"
                )
                signal = TradingSignal(
                    signal_type=SignalType.SHORT_ENTRY_SIGNAL,
                    bar_index=bar_index,
                    timestamp=timestamp,
                    rsi_value=current_rsi,
                    state_at_signal=StrategyState.SHORT_ENTRY,
                    reason=f"Bearish Pullback re-entry trigger: RSI crossed below {self.pullback_level}"
                )

        elif self._state == StrategyState.BEARISH_TRADED:
            # Priority 1: Cycle end & Short Exit (RSI > 60)
            if current_rsi > self.upper_level:
                self._state = StrategyState.BULLISH_TREND
                self._record_transition(
                    bar_index, timestamp, old_state, self._state, current_rsi,
                    f"Bearish cycle ended: RSI ({current_rsi:.2f}) > {self.upper_level} -> Short Exit Signal + Flip to Bullish Trend"
                )
                signal = TradingSignal(
                    signal_type=SignalType.SHORT_EXIT_SIGNAL,
                    bar_index=bar_index,
                    timestamp=timestamp,
                    rsi_value=current_rsi,
                    state_at_signal=StrategyState.BEARISH_TRADED,
                    reason=f"Short strategy exit: RSI ({current_rsi:.2f}) > {self.upper_level}"
                )
            # Pullbacks in BEARISH_TRADED are completely ignored (1 trade per cycle)

        # Update previous RSI for the next bar
        self._prev_rsi = current_rsi
        return signal
