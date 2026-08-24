"""
Streaming Paper Trading & Real-Time Shadow Backtest Engine for Strategy V2.6.
Strictly implements the frozen specification:
- Layer 1: Volatility Sufficiency (Entry Filter only; never closes existing position)
- Layer 2: Kaufman ER Directional Regime
- Layer 3: RSI Timing
- Hard SL: Intrabar touch audit
- Thesis Exit: Bar Close -> Next Open audit
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import random
import math

from ..data.loader import Candle
from ..indicator.rsi import WilderRSI
from ..indicator.kaufman_er import KaufmanER
from ..indicator.atr import WilderATR
from ..state_machine.states import StrategyState, SignalType, TradingSignal, PositionSide
from ..state_machine.engine_v2 import RSIStateMachineV2
from .audit_logger import ShadowAuditRecord, ShadowAuditLogger, DivergenceCategory, ExitTriggerType


class ShadowPaperTradingEngine:
    """
    Paper Trading Execution Engine for Strategy V2.6 (Frozen Spec).
    """

    def __init__(
        self,
        rsi_period: int = 14,
        er_period: int = 14,
        atr_period: int = 14,
        upper_level: float = 60.0,
        pullback_level: float = 50.0,
        lower_level: float = 40.0,
        er_threshold: float = 0.40,
        atr_multiplier: float = 2.5,
        min_atr_cost_ratio: float = 5.0,
        base_spread: float = 0.25,
        base_slippage: float = 0.15,
        commission_rate: float = 0.00003,
        initial_capital: float = 100000.0,
        units_per_trade: float = 50.0,
        seed: int = 42
    ):
        self.rsi_period = rsi_period
        self.er_period = er_period
        self.atr_period = atr_period
        self.upper_level = upper_level
        self.pullback_level = pullback_level
        self.lower_level = lower_level
        self.er_threshold = er_threshold
        self.atr_multiplier = atr_multiplier
        self.min_atr_cost_ratio = min_atr_cost_ratio

        self.base_spread = base_spread
        self.base_slippage = base_slippage
        self.commission_rate = commission_rate
        self.initial_capital = initial_capital
        self.units_per_trade = units_per_trade

        self.indicator_rsi = WilderRSI(period=rsi_period)
        self.indicator_er = KaufmanER(period=er_period)
        self.indicator_atr = WilderATR(period=atr_period)
        self.state_machine = RSIStateMachineV2(
            upper_level=upper_level,
            pullback_level=pullback_level,
            lower_level=lower_level,
            er_threshold=er_threshold
        )

        self._price_history: List[float] = []
        self._pending_signal: Optional[TradingSignal] = None
        self._active_record: Optional[ShadowAuditRecord] = None
        self._active_direction: Optional[str] = None
        self._trade_counter: int = 0
        self._completed_audit_records: List[ShadowAuditRecord] = []
        
        self.rng = random.Random(seed)
        self._latest_atr: Optional[float] = None
        self._latest_er: Optional[float] = None
        self._latest_rsi: Optional[float] = None

    def reset(self) -> None:
        self.indicator_rsi.reset()
        self.indicator_er.reset()
        self.indicator_atr.reset()
        self.state_machine.reset()
        self._price_history.clear()
        self._pending_signal = None
        self._active_record = None
        self._active_direction = None
        self._trade_counter = 0
        self._completed_audit_records.clear()

    @property
    def audit_records(self) -> List[ShadowAuditRecord]:
        return list(self._completed_audit_records)

    def on_hourly_candle(self, bar_index: int, candle: Candle) -> Tuple[Optional[ShadowAuditRecord], Optional[TradingSignal]]:
        closed_record: Optional[ShadowAuditRecord] = None
        executed_signal: Optional[TradingSignal] = None

        # ── 1. BAR OPEN: Execute Pending Order ──
        if self._pending_signal is not None:
            sig = self._pending_signal
            self._pending_signal = None
            executed_signal = sig

            theo_open = candle.open
            live_spread = self.base_spread + max(0.0, self.rng.gauss(0, 0.05))
            live_slip = self.base_slippage + self.rng.gauss(0, 0.04)
            exec_delay = max(45.0, self.rng.gauss(120.0, 30.0))

            # If it's a Thesis Exit signal for active position
            if sig.signal_type in (SignalType.LONG_EXIT_SIGNAL, SignalType.SHORT_EXIT_SIGNAL):
                if self._active_record is not None:
                    if self._active_direction == "LONG":
                        actual_exit = theo_open - (live_spread / 2.0) - max(0.0, live_slip)
                        exit_slip = theo_open - actual_exit
                    else:
                        actual_exit = theo_open + (live_spread / 2.0) + max(0.0, live_slip)
                        exit_slip = actual_exit - theo_open

                    self._active_record.finalize_trade(
                        exit_trigger_type=ExitTriggerType.THESIS_EXIT,
                        exit_trigger_time=sig.timestamp,
                        exit_trigger_price=theo_open,
                        exit_execution_time=candle.timestamp + timedelta(milliseconds=exec_delay),
                        exit_signal_time=sig.timestamp,
                        theoretical_exit=theo_open,
                        actual_exit=actual_exit,
                        exit_slippage=exit_slip,
                        exit_reason=sig.reason,
                        units=self.units_per_trade,
                        commission_rate=self.commission_rate
                    )
                    self._completed_audit_records.append(self._active_record)
                    closed_record = self._active_record
                    self._active_record = None
                    self._active_direction = None

            # If it's an Entry Signal
            elif sig.signal_type in (SignalType.LONG_ENTRY_SIGNAL, SignalType.SHORT_ENTRY_SIGNAL):
                if self._active_record is None:
                    self._trade_counter += 1
                    if sig.signal_type == SignalType.LONG_ENTRY_SIGNAL:
                        actual_fill = theo_open + (live_spread / 2.0) + max(0.0, live_slip)
                        direction = "LONG"
                        entry_slip = actual_fill - theo_open
                        hard_sl = round(actual_fill - (self.atr_multiplier * (self._latest_atr or 5.0)), 2)
                    else: # SHORT
                        actual_fill = theo_open - (live_spread / 2.0) - max(0.0, live_slip)
                        direction = "SHORT"
                        entry_slip = theo_open - actual_fill
                        hard_sl = round(actual_fill + (self.atr_multiplier * (self._latest_atr or 5.0)), 2)

                    state_before = self.state_machine.current_state.value
                    self.state_machine.notify_order_executed(bar_index, candle.timestamp)
                    state_after = self.state_machine.current_state.value

                    vol_ratio = ((self._latest_atr or 0.0) / 0.46) if self._latest_atr else 0.0

                    record = ShadowAuditRecord(
                        trade_id=self._trade_counter,
                        timestamp=candle.timestamp,
                        direction=direction,
                        theoretical_entry=theo_open,
                        actual_entry=round(actual_fill, 2),
                        entry_slippage=round(entry_slip, 2),
                        spread_at_entry=round(live_spread, 2),
                        execution_delay_ms=round(exec_delay, 1),
                        atr_14=round(self._latest_atr or 0.0, 2),
                        er_14=round(self._latest_er or 0.0, 4),
                        volatility_ratio=round(vol_ratio, 2),
                        rsi_14=round(self._latest_rsi or 0.0, 2),
                        hard_stop_price=hard_sl,
                        state_before=state_before,
                        state_after=state_after
                    )
                    self._active_record = record
                    self._active_direction = direction

        # ── 2. INTRABAR: Check Hard Stop Loss ──
        if self._active_record is not None and self._active_direction is not None:
            stop_hit = False
            intrabar_hit_time = candle.timestamp + timedelta(minutes=25) # approximate intrabar touch
            exec_delay = max(45.0, self.rng.gauss(120.0, 30.0))

            if self._active_direction == "LONG" and candle.low <= self._active_record.hard_stop_price:
                stop_hit = True
                theo_exit = self._active_record.hard_stop_price
                actual_exit = min(candle.open, self._active_record.hard_stop_price) - 0.12 - (self.base_spread / 2.0)
                exit_slip = theo_exit - actual_exit
            elif self._active_direction == "SHORT" and candle.high >= self._active_record.hard_stop_price:
                stop_hit = True
                theo_exit = self._active_record.hard_stop_price
                actual_exit = max(candle.open, self._active_record.hard_stop_price) + 0.12 + (self.base_spread / 2.0)
                exit_slip = actual_exit - theo_exit

            if stop_hit:
                self._active_record.finalize_trade(
                    exit_trigger_type=ExitTriggerType.HARD_STOP,
                    exit_trigger_time=intrabar_hit_time,
                    exit_trigger_price=theo_exit,
                    exit_execution_time=intrabar_hit_time + timedelta(milliseconds=exec_delay),
                    exit_signal_time=intrabar_hit_time,
                    theoretical_exit=theo_exit,
                    actual_exit=actual_exit,
                    exit_slippage=exit_slip,
                    exit_reason=f"HARD_STOP: Touch ${self._active_record.hard_stop_price:.2f}",
                    units=self.units_per_trade,
                    commission_rate=self.commission_rate
                )
                self._completed_audit_records.append(self._active_record)
                closed_record = self._active_record
                self._active_record = None
                self._active_direction = None

        # ── 3. BAR CLOSE: Calculate Indicators & Evaluate Logic ──
        close_p = candle.close
        self._price_history.append(close_p)

        rsi_val = self.indicator_rsi.update(close_p)
        er_val = self.indicator_er.update(close_p)
        atr_val = self.indicator_atr.update(candle)

        self._latest_rsi = rsi_val
        self._latest_er = er_val
        self._latest_atr = atr_val

        close_change_14: Optional[float] = None
        if len(self._price_history) > self.er_period:
            close_change_14 = close_p - self._price_history[-1 - self.er_period]

        # ── LAYER 1: Volatility Sufficiency (ENTRY FILTER ONLY) ──
        # If ATR / Cost < 5.0, ONLY suppress new Trend Cycle initiation.
        # NEVER close or modify an active trade!
        roundturn_cost = self.base_spread + (self.base_slippage * 2) + 0.06
        is_vol_sufficient = (atr_val / roundturn_cost) >= self.min_atr_cost_ratio if (atr_val and roundturn_cost > 0) else False

        effective_er = er_val if is_vol_sufficient else 0.0

        signal = self.state_machine.evaluate_bar(
            bar_index=bar_index,
            timestamp=candle.timestamp,
            current_rsi=rsi_val,
            current_er=effective_er,
            close_change_14=close_change_14
        )

        if signal is not None:
            if signal.signal_type in (SignalType.LONG_EXIT_SIGNAL, SignalType.SHORT_EXIT_SIGNAL):
                # Thesis Exit will close at NEXT bar OPEN
                if self._active_record is not None:
                    self._pending_signal = signal
            else:
                # Entry signal will open at NEXT bar OPEN
                if self._active_record is None:
                    self._pending_signal = signal

        return closed_record, signal
