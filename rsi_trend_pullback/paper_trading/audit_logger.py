"""
Audit Logger and Divergence Classifier for Real-Time Shadow Paper Trading.
Logs all theoretical vs live execution parameters with explicit Exit Event Tracking
and detailed 4-component Friction Cost Decomposition:
- spread_cost
- commission_cost
- entry_slippage_cost
- exit_slippage_cost
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import csv
import os


class ExitTriggerType(str, Enum):
    HARD_STOP = "HARD_STOP"
    THESIS_EXIT = "THESIS_EXIT"


class DivergenceCategory(str, Enum):
    NONE = "NONE"
    DATA = "DATA"
    TIME = "TIME"
    CALCULATION = "CALCULATION"
    STATE = "STATE"
    EXECUTION = "EXECUTION"
    SLIPPAGE = "SLIPPAGE"
    SPREAD = "SPREAD"
    OTHER = "OTHER"


@dataclass
class ShadowAuditRecord:
    """
    Comprehensive 33-Column Execution Audit Record with Decomposed Friction Costs.
    """
    trade_id: int
    timestamp: datetime
    direction: str
    theoretical_entry: float
    actual_entry: float
    entry_slippage: float
    spread_at_entry: float
    execution_delay_ms: float

    atr_14: float
    er_14: float
    volatility_ratio: float
    rsi_14: float

    hard_stop_price: float

    # ── Explicit Exit Event Tracking ──
    exit_trigger_type: Optional[ExitTriggerType] = None
    exit_trigger_time: Optional[datetime] = None
    exit_trigger_price: Optional[float] = None
    exit_execution_time: Optional[datetime] = None

    exit_signal_time: Optional[datetime] = None
    theoretical_exit: Optional[float] = None
    actual_exit: Optional[float] = None
    exit_slippage: float = 0.0
    exit_reason: str = ""

    # ── PnL Accounting ──
    theoretical_net_pnl: float = 0.0
    actual_net_pnl: float = 0.0
    friction_drag: float = 0.0

    # ── Decomposed Friction Costs ──
    spread_cost: float = 0.0
    commission_cost: float = 0.0
    entry_slippage_cost: float = 0.0
    exit_slippage_cost: float = 0.0

    # ── State Machine & Diagnostics ──
    state_before: str = ""
    state_after: str = ""
    divergence_category: DivergenceCategory = DivergenceCategory.NONE
    divergence_notes: str = ""

    def finalize_trade(
        self,
        exit_trigger_type: ExitTriggerType,
        exit_trigger_time: datetime,
        exit_trigger_price: float,
        exit_execution_time: datetime,
        exit_signal_time: datetime,
        theoretical_exit: float,
        actual_exit: float,
        exit_slippage: float,
        exit_reason: str,
        units: float = 50.0,
        commission_rate: float = 0.00003
    ) -> None:
        self.exit_trigger_type = exit_trigger_type
        self.exit_trigger_time = exit_trigger_time
        self.exit_trigger_price = round(exit_trigger_price, 2)
        self.exit_execution_time = exit_execution_time

        self.exit_signal_time = exit_signal_time
        self.theoretical_exit = round(theoretical_exit, 2)
        self.actual_exit = round(actual_exit, 2)
        self.exit_slippage = round(exit_slippage, 2)
        self.exit_reason = exit_reason

        # 1. Theoretical PnL (Zero Spread / Zero Slippage Baseline)
        if self.direction == "LONG":
            theo_gross = (self.theoretical_exit - self.theoretical_entry) * units
            actual_gross = (self.actual_exit - self.actual_entry) * units
        else: # SHORT
            theo_gross = (self.theoretical_entry - self.theoretical_exit) * units
            actual_gross = (self.actual_entry - self.actual_exit) * units

        theo_comm = (self.theoretical_entry + self.theoretical_exit) * commission_rate * units
        actual_comm = (self.actual_entry + self.actual_exit) * commission_rate * units

        self.theoretical_net_pnl = round(theo_gross - theo_comm, 2)
        self.actual_net_pnl = round(actual_gross - actual_comm, 2)
        self.friction_drag = round(self.theoretical_net_pnl - self.actual_net_pnl, 2)

        # 2. Decomposed Friction Drag Components ($)
        self.spread_cost = round(self.spread_at_entry * units, 2)
        self.commission_cost = round(actual_comm, 2)
        self.entry_slippage_cost = round(abs(self.entry_slippage) * units, 2)
        self.exit_slippage_cost = round(abs(self.exit_slippage) * units, 2)

        # 3. Classify Divergence Category
        if abs(self.entry_slippage) > 0.30 or abs(self.exit_slippage) > 0.30:
            self.divergence_category = DivergenceCategory.SLIPPAGE
            self.divergence_notes = f"Elevated slippage: Entry={self.entry_slippage:.2f}, Exit={self.exit_slippage:.2f}"
        elif self.spread_at_entry > 0.50:
            self.divergence_category = DivergenceCategory.SPREAD
            self.divergence_notes = f"Wide spread at entry: ${self.spread_at_entry:.2f}"
        elif self.execution_delay_ms > 1000.0:
            self.divergence_category = DivergenceCategory.EXECUTION
            self.divergence_notes = f"Execution latency spike: {self.execution_delay_ms:.1f} ms"
        else:
            self.divergence_category = DivergenceCategory.NONE
            self.divergence_notes = "Normal ECN execution within bounds"


class ShadowAuditLogger:
    """
    Manages 33-column audit record exports to CSV.
    """

    @staticmethod
    def export_audit_csv(records: List[ShadowAuditRecord], output_path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "trade_id",
                "timestamp",
                "direction",
                "theoretical_entry",
                "actual_entry",
                "entry_slippage",
                "spread_at_entry",
                "execution_delay_ms",
                "ATR14",
                "ER14",
                "volatility_ratio",
                "RSI14",
                "hard_stop_price",
                "exit_trigger_type",
                "exit_trigger_time",
                "exit_trigger_price",
                "exit_execution_time",
                "exit_signal_time",
                "theoretical_exit",
                "actual_exit",
                "exit_slippage",
                "exit_reason",
                "theoretical_net_pnl",
                "actual_net_pnl",
                "friction_drag",
                "spread_cost",
                "commission_cost",
                "entry_slippage_cost",
                "exit_slippage_cost",
                "state_before",
                "state_after",
                "divergence_category",
                "divergence_notes"
            ])
            for r in records:
                writer.writerow([
                    r.trade_id,
                    r.timestamp.isoformat(),
                    r.direction,
                    f"{r.theoretical_entry:.2f}",
                    f"{r.actual_entry:.2f}",
                    f"{r.entry_slippage:.2f}",
                    f"{r.spread_at_entry:.2f}",
                    f"{r.execution_delay_ms:.1f}",
                    f"{r.atr_14:.2f}",
                    f"{r.er_14:.4f}",
                    f"{r.volatility_ratio:.2f}",
                    f"{r.rsi_14:.2f}",
                    f"{r.hard_stop_price:.2f}",
                    r.exit_trigger_type.value if r.exit_trigger_type else "",
                    r.exit_trigger_time.isoformat() if r.exit_trigger_time else "",
                    f"{r.exit_trigger_price:.2f}" if r.exit_trigger_price is not None else "",
                    r.exit_execution_time.isoformat() if r.exit_execution_time else "",
                    r.exit_signal_time.isoformat() if r.exit_signal_time else "",
                    f"{r.theoretical_exit:.2f}" if r.theoretical_exit is not None else "",
                    f"{r.actual_exit:.2f}" if r.actual_exit is not None else "",
                    f"{r.exit_slippage:.2f}",
                    r.exit_reason,
                    f"{r.theoretical_net_pnl:.2f}",
                    f"{r.actual_net_pnl:.2f}",
                    f"{r.friction_drag:.2f}",
                    f"{r.spread_cost:.2f}",
                    f"{r.commission_cost:.2f}",
                    f"{r.entry_slippage_cost:.2f}",
                    f"{r.exit_slippage_cost:.2f}",
                    r.state_before,
                    r.state_after,
                    r.divergence_category.value,
                    r.divergence_notes
                ])
