"""
Strategy V2.6 with 3-Layer Architecture:
Layer 1: Volatility Sufficiency (ATR / Friction >= Threshold or Relative ATR)
Layer 2: Kaufman ER Directional Regime (ER > 0.40)
Layer 3: RSI Timing Trigger (60/50/40) + 2.5x ATR Stop Loss + Thesis Exit
"""

from typing import List, Optional
from datetime import datetime
from ..data.loader import Candle
from ..indicator.rsi import WilderRSI
from ..indicator.kaufman_er import KaufmanER
from ..indicator.atr import WilderATR
from ..state_machine.states import StrategyState, SignalType, TradingSignal, PositionSide
from ..state_machine.engine_v2 import RSIStateMachineV2
from ..execution.simulator import ExecutionEngine, ExecutionConfig
from ..portfolio.position import TradeRecord
from ..portfolio.portfolio import Portfolio, EquityPoint


class RSIStrategyV26Engine:
    """
    Strategy V2.6 Engine with 3-Layer Architecture.
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
        min_atr_cost_ratio: float = 5.0, # Minimum ATR / Roundturn Cost (e.g. 5.0x friction)
        execution_config: Optional[ExecutionConfig] = None,
        initial_capital: float = 100000.0,
        units_per_trade: float = 50.0
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

        self.indicator_rsi = WilderRSI(period=rsi_period)
        self.indicator_er = KaufmanER(period=er_period)
        self.indicator_atr = WilderATR(period=atr_period)
        
        self.state_machine = RSIStateMachineV2(
            upper_level=upper_level,
            pullback_level=pullback_level,
            lower_level=lower_level,
            er_threshold=er_threshold
        )
        self.execution = ExecutionEngine(config=execution_config or ExecutionConfig.create_realistic())
        self.portfolio = Portfolio(initial_capital=initial_capital, fixed_position_size_units=units_per_trade)
        
        self._price_history: List[float] = []
        self._active_stop_price: Optional[float] = None
        self._latest_atr: Optional[float] = None

    def reset(self) -> None:
        self.indicator_rsi.reset()
        self.indicator_er.reset()
        self.indicator_atr.reset()
        self.state_machine.reset()
        self.execution.reset()
        self.portfolio.reset()
        self._price_history.clear()
        self._active_stop_price = None
        self._latest_atr = None

    @property
    def closed_trades(self) -> List[TradeRecord]:
        return self.execution.closed_trades

    @property
    def equity_curve(self) -> List[EquityPoint]:
        return self.portfolio.equity_curve

    def run_backtest(self, candles: List[Candle]) -> "RSIStrategyV26Engine":
        self.reset()

        # Calculate estimated roundturn friction per unit ($0.25 spread + $0.15 slip + ~$0.06 comm = ~$0.46)
        roundturn_friction = self.execution.config.spread + (self.execution.config.slippage * 2) + 0.06
        if self.execution.config.is_raw:
            roundturn_friction = 0.01

        for bar_idx, candle in enumerate(candles):
            # 1. BAR OPEN execution
            action_trade = self.execution.process_bar_open(bar_idx, candle)
            if action_trade is not None:
                self.state_machine.notify_order_executed(bar_idx, candle.timestamp)
                if self.execution.active_trade is not None:
                    atr_val = self._latest_atr or 5.0
                    if self.execution.active_trade.direction == PositionSide.LONG:
                        self._active_stop_price = round(action_trade.entry_price - (self.atr_multiplier * atr_val), 2)
                    elif self.execution.active_trade.direction == PositionSide.SHORT:
                        self._active_stop_price = round(action_trade.entry_price + (self.atr_multiplier * atr_val), 2)
                else:
                    self._active_stop_price = None

            # 2. INTRABAR: Hard Stop Loss Check
            active_trade = self.execution.active_trade
            if active_trade is not None and self._active_stop_price is not None:
                if active_trade.direction == PositionSide.LONG and candle.low <= self._active_stop_price:
                    fill_price = min(candle.open, self._active_stop_price)
                    half_spread = 0.0 if self.execution.config.is_raw else (self.execution.config.spread / 2.0)
                    slip = 0.0 if self.execution.config.is_raw else self.execution.config.slippage
                    effective_exit = fill_price - half_spread - slip
                    exit_fee = 0.0 if self.execution.config.is_raw else (effective_exit * self.execution.config.commission_rate)

                    active_trade.close(
                        exit_signal_bar_index=bar_idx,
                        exit_signal_timestamp=candle.timestamp,
                        exit_bar_index=bar_idx,
                        exit_timestamp=candle.timestamp,
                        exit_price=effective_exit,
                        fees=exit_fee,
                        slippage=slip + half_spread,
                        state_at_exit=self.state_machine.current_state,
                        exit_reason=f"Hard 2.5x ATR Stop Loss hit (${self._active_stop_price:.2f})"
                    )
                    self.execution._closed_trades.append(active_trade)
                    self.execution._active_trade = None
                    self._active_stop_price = None

                elif active_trade.direction == PositionSide.SHORT and candle.high >= self._active_stop_price:
                    fill_price = max(candle.open, self._active_stop_price)
                    half_spread = 0.0 if self.execution.config.is_raw else (self.execution.config.spread / 2.0)
                    slip = 0.0 if self.execution.config.is_raw else self.execution.config.slippage
                    effective_exit = fill_price + half_spread + slip
                    exit_fee = 0.0 if self.execution.config.is_raw else (effective_exit * self.execution.config.commission_rate)

                    active_trade.close(
                        exit_signal_bar_index=bar_idx,
                        exit_signal_timestamp=candle.timestamp,
                        exit_bar_index=bar_idx,
                        exit_timestamp=candle.timestamp,
                        exit_price=effective_exit,
                        fees=exit_fee,
                        slippage=slip + half_spread,
                        state_at_exit=self.state_machine.current_state,
                        exit_reason=f"Hard 2.5x ATR Stop Loss hit (${self._active_stop_price:.2f})"
                    )
                    self.execution._closed_trades.append(active_trade)
                    self.execution._active_trade = None
                    self._active_stop_price = None

            # 3. BAR CLOSE: Indicator calculations
            close_p = candle.close
            self._price_history.append(close_p)

            rsi_val = self.indicator_rsi.update(close_p)
            er_val = self.indicator_er.update(close_p)
            atr_val = self.indicator_atr.update(candle)
            if atr_val is not None:
                self._latest_atr = atr_val

            close_change_14: Optional[float] = None
            if len(self._price_history) > self.er_period:
                close_change_14 = close_p - self._price_history[-1 - self.er_period]

            # ── LAYER 1: Volatility Sufficiency Check ──
            # Is ATR large enough relative to friction?
            is_volatility_sufficient = True
            if atr_val is not None and roundturn_friction > 0:
                is_volatility_sufficient = (atr_val / roundturn_friction) >= self.min_atr_cost_ratio

            # If volatility is insufficient, suppress new trend cycle qualifications
            effective_er = er_val if is_volatility_sufficient else 0.0

            signal = self.state_machine.evaluate_bar(
                bar_index=bar_idx,
                timestamp=candle.timestamp,
                current_rsi=rsi_val,
                current_er=effective_er,
                close_change_14=close_change_14
            )

            if signal is not None:
                if signal.signal_type in (SignalType.LONG_EXIT_SIGNAL, SignalType.SHORT_EXIT_SIGNAL):
                    if self.execution.active_trade is not None:
                        self.execution.submit_signal(signal, candle)
                else:
                    self.execution.submit_signal(signal, candle)

            # 4. Mark-to-market accounting
            self.portfolio.update_bar(
                bar_index=bar_idx,
                candle=candle,
                active_trade=self.execution.active_trade,
                closed_trades=self.execution.closed_trades
            )

        return self
