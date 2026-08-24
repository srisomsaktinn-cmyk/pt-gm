"""
Execution Simulator handling next-bar open fills, transaction costs,
spread, slippage, and strict execution timing.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from ..data.loader import Candle
from ..state_machine.states import PositionSide, SignalType, TradingSignal, StrategyState
from ..portfolio.position import TradeRecord


@dataclass(frozen=True)
class ExecutionConfig:
    """
    Cost and execution configuration.
    Distinguishes Raw vs Realistic execution.
    """
    commission_rate: float = 0.0002   # 2 bps (0.02%) per trade leg
    spread: float = 0.0001            # 1 pip / 0.0001 absolute price units
    slippage: float = 0.00005         # 0.5 pip / 0.00005 adverse price shift
    is_raw: bool = False              # If True, costs are 0.0

    @classmethod
    def create_raw(cls) -> "ExecutionConfig":
        return cls(commission_rate=0.0, spread=0.0, slippage=0.0, is_raw=True)

    @classmethod
    def create_realistic(
        cls,
        commission_rate: float = 0.0002,
        spread: float = 0.0001,
        slippage: float = 0.00005
    ) -> "ExecutionConfig":
        return cls(
            commission_rate=commission_rate,
            spread=spread,
            slippage=slippage,
            is_raw=False
        )


@dataclass
class PendingOrder:
    """
    Order generated at candle T Close, awaiting execution at candle T+1 Open.
    """
    signal: TradingSignal
    signal_candle: Candle


class ExecutionEngine:
    """
    Processes trading signals and executes fills strictly at NEXT bar OPEN.
    """

    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config: ExecutionConfig = config or ExecutionConfig.create_realistic()
        self._pending_order: Optional[PendingOrder] = None
        self._active_trade: Optional[TradeRecord] = None
        self._closed_trades: List[TradeRecord] = []
        self._trade_counter: int = 0

    @property
    def active_trade(self) -> Optional[TradeRecord]:
        return self._active_trade

    @property
    def closed_trades(self) -> List[TradeRecord]:
        return list(self._closed_trades)

    @property
    def current_position_side(self) -> PositionSide:
        if self._active_trade is not None:
            return self._active_trade.direction
        return PositionSide.NONE

    def reset(self) -> None:
        self._pending_order = None
        self._active_trade = None
        self._closed_trades.clear()
        self._trade_counter = 0

    def submit_signal(self, signal: TradingSignal, signal_candle: Candle) -> None:
        """
        Stores pending signal at bar T close. Order will execute at bar T+1 open.
        """
        self._pending_order = PendingOrder(signal=signal, signal_candle=signal_candle)

    def process_bar_open(self, bar_index: int, current_candle: Candle) -> Optional[TradeRecord]:
        """
        Executes pending orders at the OPEN of the new candle.
        Returns the modified/closed TradeRecord if an action took place.
        """
        if self._pending_order is None:
            return None

        order = self._pending_order
        self._pending_order = None  # Consume order

        sig = order.signal
        open_price = current_candle.open
        action_trade: Optional[TradeRecord] = None

        # ── 1. Long Entry ──
        if sig.signal_type == SignalType.LONG_ENTRY_SIGNAL:
            # If already long, do not duplicate
            if self._active_trade is None:
                self._trade_counter += 1
                half_spread = 0.0 if self.config.is_raw else (self.config.spread / 2.0)
                slip = 0.0 if self.config.is_raw else self.config.slippage
                effective_entry_price = open_price + half_spread + slip
                entry_fee = 0.0 if self.config.is_raw else (effective_entry_price * self.config.commission_rate)

                trade = TradeRecord(
                    trade_id=self._trade_counter,
                    direction=PositionSide.LONG,
                    signal_bar_index=sig.bar_index,
                    signal_timestamp=sig.timestamp,
                    entry_bar_index=bar_index,
                    entry_timestamp=current_candle.timestamp,
                    entry_price=effective_entry_price,
                    units=1.0,
                    fees=entry_fee,
                    slippage=slip + half_spread,
                    state_at_entry=sig.state_at_signal,
                    exit_reason=""
                )
                self._active_trade = trade
                action_trade = trade

        # ── 2. Short Entry ──
        elif sig.signal_type == SignalType.SHORT_ENTRY_SIGNAL:
            if self._active_trade is None:
                self._trade_counter += 1
                half_spread = 0.0 if self.config.is_raw else (self.config.spread / 2.0)
                slip = 0.0 if self.config.is_raw else self.config.slippage
                effective_entry_price = open_price - half_spread - slip
                entry_fee = 0.0 if self.config.is_raw else (effective_entry_price * self.config.commission_rate)

                trade = TradeRecord(
                    trade_id=self._trade_counter,
                    direction=PositionSide.SHORT,
                    signal_bar_index=sig.bar_index,
                    signal_timestamp=sig.timestamp,
                    entry_bar_index=bar_index,
                    entry_timestamp=current_candle.timestamp,
                    entry_price=effective_entry_price,
                    units=1.0,
                    fees=entry_fee,
                    slippage=slip + half_spread,
                    state_at_entry=sig.state_at_signal,
                    exit_reason=""
                )
                self._active_trade = trade
                action_trade = trade

        # ── 3. Long Exit ──
        elif sig.signal_type == SignalType.LONG_EXIT_SIGNAL:
            if self._active_trade is not None and self._active_trade.direction == PositionSide.LONG:
                half_spread = 0.0 if self.config.is_raw else (self.config.spread / 2.0)
                slip = 0.0 if self.config.is_raw else self.config.slippage
                effective_exit_price = open_price - half_spread - slip
                exit_fee = 0.0 if self.config.is_raw else (effective_exit_price * self.config.commission_rate)

                self._active_trade.close(
                    exit_signal_bar_index=sig.bar_index,
                    exit_signal_timestamp=sig.timestamp,
                    exit_bar_index=bar_index,
                    exit_timestamp=current_candle.timestamp,
                    exit_price=effective_exit_price,
                    fees=exit_fee,
                    slippage=slip + half_spread,
                    state_at_exit=sig.state_at_signal,
                    exit_reason=sig.reason
                )
                self._closed_trades.append(self._active_trade)
                action_trade = self._active_trade
                self._active_trade = None

        # ── 4. Short Exit ──
        elif sig.signal_type == SignalType.SHORT_EXIT_SIGNAL:
            if self._active_trade is not None and self._active_trade.direction == PositionSide.SHORT:
                half_spread = 0.0 if self.config.is_raw else (self.config.spread / 2.0)
                slip = 0.0 if self.config.is_raw else self.config.slippage
                effective_exit_price = open_price + half_spread + slip
                exit_fee = 0.0 if self.config.is_raw else (effective_exit_price * self.config.commission_rate)

                self._active_trade.close(
                    exit_signal_bar_index=sig.bar_index,
                    exit_signal_timestamp=sig.timestamp,
                    exit_bar_index=bar_index,
                    exit_timestamp=current_candle.timestamp,
                    exit_price=effective_exit_price,
                    fees=exit_fee,
                    slippage=slip + half_spread,
                    state_at_exit=sig.state_at_signal,
                    exit_reason=sig.reason
                )
                self._closed_trades.append(self._active_trade)
                action_trade = self._active_trade
                self._active_trade = None

        return action_trade
