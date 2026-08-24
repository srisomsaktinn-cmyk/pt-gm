"""
Strategy V2 Backtest Engine:
RSI(14) Trend Pullback Re-entry + Kaufman Efficiency Ratio (ER > 0.40).
"""

from typing import List, Optional
from datetime import datetime
from ..data.loader import Candle
from ..indicator.rsi import WilderRSI
from ..indicator.kaufman_er import KaufmanER
from ..state_machine.states import StrategyState, SignalType, TradingSignal
from ..state_machine.engine_v2 import RSIStateMachineV2
from ..execution.simulator import ExecutionEngine, ExecutionConfig
from ..portfolio.position import TradeRecord
from ..portfolio.portfolio import Portfolio, EquityPoint


class RSIStrategyV2Engine:
    """
    Orchestrates the Strategy V2 Backtest with Kaufman ER Regime Filter.
    """

    def __init__(
        self,
        rsi_period: int = 14,
        er_period: int = 14,
        upper_level: float = 60.0,
        pullback_level: float = 50.0,
        lower_level: float = 40.0,
        er_threshold: float = 0.40,
        execution_config: Optional[ExecutionConfig] = None,
        initial_capital: float = 100000.0,
        units_per_trade: float = 50.0
    ):
        self.rsi_period = rsi_period
        self.er_period = er_period
        self.upper_level = upper_level
        self.pullback_level = pullback_level
        self.lower_level = lower_level
        self.er_threshold = er_threshold

        self.indicator_rsi = WilderRSI(period=rsi_period)
        self.indicator_er = KaufmanER(period=er_period)
        self.state_machine = RSIStateMachineV2(
            upper_level=upper_level,
            pullback_level=pullback_level,
            lower_level=lower_level,
            er_threshold=er_threshold
        )
        self.execution = ExecutionEngine(config=execution_config or ExecutionConfig.create_realistic())
        self.portfolio = Portfolio(initial_capital=initial_capital, fixed_position_size_units=units_per_trade)
        
        self._price_history: List[float] = []
        self._rsi_history: List[Optional[float]] = []
        self._er_history: List[Optional[float]] = []
        self._signals_history: List[TradingSignal] = []

    def reset(self) -> None:
        self.indicator_rsi.reset()
        self.indicator_er.reset()
        self.state_machine.reset()
        self.execution.reset()
        self.portfolio.reset()
        self._price_history.clear()
        self._rsi_history.clear()
        self._er_history.clear()
        self._signals_history.clear()

    @property
    def closed_trades(self) -> List[TradeRecord]:
        return self.execution.closed_trades

    @property
    def transition_history(self):
        return self.state_machine.transition_history

    @property
    def equity_curve(self) -> List[EquityPoint]:
        return self.portfolio.equity_curve

    def run_backtest(self, candles: List[Candle]) -> "RSIStrategyV2Engine":
        self.reset()

        for bar_idx, candle in enumerate(candles):
            # 1. Bar Open execution
            action_trade = self.execution.process_bar_open(bar_idx, candle)
            if action_trade is not None:
                self.state_machine.notify_order_executed(bar_idx, candle.timestamp)

            # 2. Bar Close calculations
            close_p = candle.close
            self._price_history.append(close_p)

            rsi_val = self.indicator_rsi.update(close_p)
            er_val = self.indicator_er.update(close_p)
            self._rsi_history.append(rsi_val)
            self._er_history.append(er_val)

            close_change_14: Optional[float] = None
            if len(self._price_history) > self.er_period:
                close_change_14 = close_p - self._price_history[-1 - self.er_period]

            # Evaluate state transitions & signal generation
            signal = self.state_machine.evaluate_bar(
                bar_index=bar_idx,
                timestamp=candle.timestamp,
                current_rsi=rsi_val,
                current_er=er_val,
                close_change_14=close_change_14
            )

            if signal is not None:
                self._signals_history.append(signal)
                self.execution.submit_signal(signal, candle)

            # 3. Mark-to-market equity update
            self.portfolio.update_bar(
                bar_index=bar_idx,
                candle=candle,
                active_trade=self.execution.active_trade,
                closed_trades=self.execution.closed_trades
            )

        return self
