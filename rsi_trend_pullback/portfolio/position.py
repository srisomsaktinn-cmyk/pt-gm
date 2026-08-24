"""
Position and Trade data structures for precise trade logging and audit trail.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from ..state_machine.states import PositionSide, StrategyState


@dataclass
class TradeRecord:
    """
    Complete audit record for every closed or open trade.
    Matches the required specification format.
    """
    trade_id: int
    direction: PositionSide
    signal_bar_index: int
    signal_timestamp: datetime
    entry_bar_index: int
    entry_timestamp: datetime
    entry_price: float
    units: float = 1.0
    exit_signal_bar_index: Optional[int] = None
    exit_signal_timestamp: Optional[datetime] = None
    exit_bar_index: Optional[int] = None
    exit_timestamp: Optional[datetime] = None
    exit_price: Optional[float] = None
    holding_bars: int = 0
    gross_pnl: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    net_pnl: float = 0.0
    return_pct: float = 0.0
    state_at_entry: StrategyState = StrategyState.LONG_ENTRY
    state_at_exit: Optional[StrategyState] = None
    exit_reason: str = ""

    def close(
        self,
        exit_signal_bar_index: int,
        exit_signal_timestamp: datetime,
        exit_bar_index: int,
        exit_timestamp: datetime,
        exit_price: float,
        fees: float,
        slippage: float,
        state_at_exit: StrategyState,
        exit_reason: str
    ) -> None:
        """
        Finalizes trade PnL calculations upon exit execution.
        """
        self.exit_signal_bar_index = exit_signal_bar_index
        self.exit_signal_timestamp = exit_signal_timestamp
        self.exit_bar_index = exit_bar_index
        self.exit_timestamp = exit_timestamp
        self.exit_price = exit_price
        self.holding_bars = exit_bar_index - self.entry_bar_index
        self.fees += fees
        self.slippage += slippage
        self.state_at_exit = state_at_exit
        self.exit_reason = exit_reason

        if self.direction == PositionSide.LONG:
            self.gross_pnl = (self.exit_price - self.entry_price) * self.units
            self.return_pct = ((self.exit_price / self.entry_price) - 1.0) * 100.0
        elif self.direction == PositionSide.SHORT:
            self.gross_pnl = (self.entry_price - self.exit_price) * self.units
            self.return_pct = (1.0 - (self.exit_price / self.entry_price)) * 100.0

        self.net_pnl = self.gross_pnl - self.fees - self.slippage

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "direction": self.direction.value,
            "signal_timestamp": self.signal_timestamp.isoformat() if self.signal_timestamp else "",
            "entry_timestamp": self.entry_timestamp.isoformat() if self.entry_timestamp else "",
            "entry_price": round(self.entry_price, 5),
            "exit_signal_timestamp": self.exit_signal_timestamp.isoformat() if self.exit_signal_timestamp else "",
            "exit_timestamp": self.exit_timestamp.isoformat() if self.exit_timestamp else "",
            "exit_price": round(self.exit_price, 5) if self.exit_price is not None else None,
            "holding_bars": self.holding_bars,
            "gross_pnl": round(self.gross_pnl, 4),
            "fees": round(self.fees, 4),
            "slippage": round(self.slippage, 4),
            "net_pnl": round(self.net_pnl, 4),
            "return_pct": round(self.return_pct, 4),
            "state_at_entry": self.state_at_entry.value if self.state_at_entry else "",
            "state_at_exit": self.state_at_exit.value if self.state_at_exit else "",
            "exit_reason": self.exit_reason
        }
