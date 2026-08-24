"""
Main Strategy Runner for RSI(14) Trend Pullback Re-entry — Strategy V1.
Wires together the indicator, state machine, execution simulator, and portfolio tracker
in a strict, non-lookahead bar-by-bar chronological engine.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ..data.loader import Candle
from ..indicator.rsi import WilderRSI
from ..state_machine.states import StrategyState, SignalType, TradingSignal, PositionSide
from ..state_machine.engine import RSIStateMachine
from ..execution.simulator import ExecutionEngine, ExecutionConfig
from ..portfolio.position import TradeRecord
from ..portfolio.portfolio import Portfolio, EquityPoint


class RSIStrategyEngine:
    """
    Orchestrates the RSI(14) Trend Pullback Re-entry Backtest.
    """

    def __init__(
        self,
        rsi_period: int = 14,
        upper_level: float = 60.0,
        pullback_level: float = 50.0,
        lower_level: float = 40.0,
        execution_config: Optional[ExecutionConfig] = None,
        initial_capital: float = 10000.0,
        units_per_trade: float = 100.0
    ):
        self.rsi_period = rsi_period
        self.upper_level = upper_level
        self.pullback_level = pullback_level
        self.lower_level = lower_level

        self.indicator = WilderRSI(period=rsi_period)
        self.state_machine = RSIStateMachine(
            upper_level=upper_level,
            pullback_level=pullback_level,
            lower_level=lower_level
        )
        self.execution = ExecutionEngine(config=execution_config or ExecutionConfig.create_realistic())
        self.portfolio = Portfolio(initial_capital=initial_capital, fixed_position_size_units=units_per_trade)
        self.units_per_trade = units_per_trade

        self._rsi_history: List[Optional[float]] = []
        self._signals_history: List[TradingSignal] = []

    def reset(self) -> None:
        self.indicator.reset()
        self.state_machine.reset()
        self.execution.reset()
        self.portfolio.reset()
        self._rsi_history.clear()
        self._signals_history.clear()

    @property
    def closed_trades(self) -> List[TradeRecord]:
        return self.execution.closed_trades

    @property
    def active_trade(self) -> Optional[TradeRecord]:
        return self.execution.active_trade

    @property
    def transition_history(self):
        return self.state_machine.transition_history

    @property
    def equity_curve(self) -> List[EquityPoint]:
        return self.portfolio.equity_curve

    @property
    def rsi_series(self) -> List[Optional[float]]:
        return list(self._rsi_history)

    def run_backtest(self, candles: List[Candle]) -> "RSIStrategyEngine":
        """
        Executes a full bar-by-bar backtest over the provided chronological candles.
        Guarantees:
        1. Execution at bar T+1 OPEN for signals generated at bar T CLOSE.
        2. Zero look-ahead bias.
        3. Deterministic state tracking.
        """
        self.reset()

        for bar_idx, candle in enumerate(candles):
            # ── 1. BAR OPEN: Execute pending orders from prior candle close ──
            action_trade = self.execution.process_bar_open(bar_idx, candle)
            if action_trade is not None:
                # If an entry executed, inform state machine to transition to TRADED state
                self.state_machine.notify_order_executed(bar_idx, candle.timestamp)

            # ── 2. BAR CLOSE: Calculate RSI & evaluate state machine ──
            rsi_val = self.indicator.update(candle.close)
            self._rsi_history.append(rsi_val)

            # Evaluate state transitions & signal generation
            signal = self.state_machine.evaluate_bar(
                bar_index=bar_idx,
                timestamp=candle.timestamp,
                current_rsi=rsi_val
            )

            # If signal fired, submit order to be executed at NEXT bar OPEN
            if signal is not None:
                self._signals_history.append(signal)
                self.execution.submit_signal(signal, candle)

            # ── 3. PORTFOLIO UPDATE: Record mark-to-market equity at bar close ──
            self.portfolio.update_bar(
                bar_index=bar_idx,
                candle=candle,
                active_trade=self.execution.active_trade,
                closed_trades=self.execution.closed_trades
            )

        return self
