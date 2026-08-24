"""
Portfolio and Equity tracker for backtesting.
Records mark-to-market equity curves, cash balances, and drawdown history.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from .position import TradeRecord
from ..state_machine.states import PositionSide
from ..data.loader import Candle


@dataclass(frozen=True)
class EquityPoint:
    bar_index: int
    timestamp: datetime
    cash: float
    equity: float
    unrealized_pnl: float
    realized_pnl: float
    drawdown_amount: float
    drawdown_pct: float
    position_side: PositionSide


class Portfolio:
    """
    Manages portfolio state, cash, trade accounting, and equity tracking.
    """

    def __init__(self, initial_capital: float = 10000.0, fixed_position_size_units: float = 100.0):
        self.initial_capital: float = initial_capital
        self.fixed_position_size_units: float = fixed_position_size_units
        self.cash: float = initial_capital
        self.peak_equity: float = initial_capital
        self.equity_curve: List[EquityPoint] = []

    def reset(self) -> None:
        self.cash = self.initial_capital
        self.peak_equity = self.initial_capital
        self.equity_curve.clear()

    def update_bar(
        self,
        bar_index: int,
        candle: Candle,
        active_trade: Optional[TradeRecord],
        closed_trades: List[TradeRecord]
    ) -> EquityPoint:
        """
        Updates mark-to-market equity at candle CLOSE.
        """
        # Sum realized PnL from closed trades
        total_realized_pnl = sum(t.net_pnl for t in closed_trades)
        
        # Calculate unrealized PnL on active trade
        unrealized_pnl = 0.0
        pos_side = PositionSide.NONE

        if active_trade is not None:
            pos_side = active_trade.direction
            current_price = candle.close
            if active_trade.direction == PositionSide.LONG:
                unrealized_pnl = (current_price - active_trade.entry_price) * active_trade.units
            elif active_trade.direction == PositionSide.SHORT:
                unrealized_pnl = (active_trade.entry_price - current_price) * active_trade.units

        current_equity = self.initial_capital + total_realized_pnl + unrealized_pnl
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        dd_amount = self.peak_equity - current_equity
        dd_pct = (dd_amount / self.peak_equity * 100.0) if self.peak_equity > 0 else 0.0

        point = EquityPoint(
            bar_index=bar_index,
            timestamp=candle.timestamp,
            cash=self.initial_capital + total_realized_pnl,
            equity=round(current_equity, 4),
            unrealized_pnl=round(unrealized_pnl, 4),
            realized_pnl=round(total_realized_pnl, 4),
            drawdown_amount=round(dd_amount, 4),
            drawdown_pct=round(dd_pct, 4),
            position_side=pos_side
        )
        self.equity_curve.append(point)
        return point
