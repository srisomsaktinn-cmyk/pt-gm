"""
Strategy V2.7 Forward Validation Telemetry & Trade Database Engine.
Tracks high-resolution execution metrics for every live MT5 forward trade:
- Signal timestamp vs Actual execution timestamp (Latency in ms)
- Theoretical entry (Bar Close / Open) vs Actual broker fill price (Slippage)
- Real-time spread, ATR14, ER14, RSI14
- Stop distance, Portfolio heat at execution, Active position count
- Pyramiding scale-in tracking (+1.5R)
- Theoretical P&L vs Actual P&L (Friction Drag & Commission/Swap)
- Anomaly detection (Spread spikes, excessive slippage, risk violations)
"""

import os
import sys
import csv
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

# ── PATH CONFIGURATION ──
FORWARD_TRADES_CSV = "d:/Kaeha/v27_forward_trades.csv"
RISK_ALERTS_LOG = "d:/Kaeha/v27_risk_alerts.log"
BROKER_ERRORS_LOG = "d:/Kaeha/v27_broker_errors.log"
TELEMETRY_STATE_JSON = "d:/Kaeha/v27_forward_telemetry_state.json"

logger = logging.getLogger("V27_TELEMETRY")


@dataclass
class ForwardTradeRecord:
    trade_id: str
    symbol: str
    is_pyramid: bool
    parent_id: Optional[str]
    direction: str
    signal_timestamp: str
    actual_entry_time: str
    execution_latency_ms: float
    theoretical_entry: float
    actual_entry: float
    slippage_price: float
    slippage_pips: float
    spread_price: float
    atr_14: float
    er_14: float
    rsi_14: float
    stop_distance_price: float
    initial_sl: float
    current_sl: float
    volume: float
    portfolio_heat_at_entry: float
    position_count_at_entry: int
    exit_signal_time: Optional[str] = None
    actual_exit_time: Optional[str] = None
    theoretical_exit: Optional[float] = None
    actual_exit: Optional[float] = None
    exit_slippage_price: Optional[float] = None
    exit_reason: Optional[str] = None
    theoretical_pnl_thb: Optional[float] = None
    actual_pnl_thb: Optional[float] = None
    friction_drag_thb: Optional[float] = None
    status: str = "OPEN"  # "OPEN", "CLOSED", "ANOMALY"


class V27TelemetryDatabase:
    """
    Production-grade telemetry database and anomaly auditor for Strategy V2.7 Demo Forward Testing.
    """

    def __init__(self):
        self.trades: Dict[str, ForwardTradeRecord] = {}
        self.closed_trades: List[ForwardTradeRecord] = []
        self._ensure_csv_headers()
        self.load_state()

    def _ensure_csv_headers(self):
        if not os.path.exists(FORWARD_TRADES_CSV):
            with open(FORWARD_TRADES_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "trade_id", "symbol", "is_pyramid", "parent_id", "direction",
                    "signal_timestamp", "actual_entry_time", "execution_latency_ms",
                    "theoretical_entry", "actual_entry", "slippage_price", "slippage_pips",
                    "spread_price", "atr_14", "er_14", "rsi_14", "stop_distance_price",
                    "initial_sl", "current_sl", "volume", "portfolio_heat_at_entry",
                    "position_count_at_entry", "exit_signal_time", "actual_exit_time",
                    "theoretical_exit", "actual_exit", "exit_slippage_price", "exit_reason",
                    "theoretical_pnl_thb", "actual_pnl_thb", "friction_drag_thb", "status"
                ])

    def record_entry_telemetry(
        self,
        trade_id: str,
        symbol: str,
        is_pyramid: bool,
        parent_id: Optional[str],
        direction: str,
        signal_timestamp: datetime,
        actual_entry_time: datetime,
        theoretical_entry: float,
        actual_entry: float,
        spread_price: float,
        atr_14: float,
        er_14: float,
        rsi_14: float,
        initial_sl: float,
        volume: float,
        portfolio_heat: float,
        position_count: int,
        tick_size: float = 0.01
    ) -> ForwardTradeRecord:
        """
        Records full entry telemetry and checks for execution anomalies.
        """
        # Duplicate Trade Check
        if trade_id in self.trades:
            self.log_risk_alert("DUPLICATE_TRADE_DETECTED", f"Trade ID {trade_id} already exists in active telemetry database!")
            return self.trades[trade_id]

        latency_ms = (actual_entry_time - signal_timestamp).total_seconds() * 1000.0
        slippage_price = actual_entry - theoretical_entry if direction == "LONG" else theoretical_entry - actual_entry
        # Convert slippage to pips
        pip_unit = 0.0001 if "USD" in symbol and symbol != "USDJPY" else (0.01 if symbol in ("USDJPY", "XAUUSD", "US500") else 1.0)
        slippage_pips = round(slippage_price / pip_unit, 2)
        stop_dist = abs(actual_entry - initial_sl)

        rec = ForwardTradeRecord(
            trade_id=trade_id,
            symbol=symbol,
            is_pyramid=is_pyramid,
            parent_id=parent_id,
            direction=direction,
            signal_timestamp=signal_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            actual_entry_time=actual_entry_time.strftime("%Y-%m-%d %H:%M:%S"),
            execution_latency_ms=round(latency_ms, 2),
            theoretical_entry=round(theoretical_entry, 5),
            actual_entry=round(actual_entry, 5),
            slippage_price=round(slippage_price, 5),
            slippage_pips=slippage_pips,
            spread_price=round(spread_price, 5),
            atr_14=round(atr_14, 5),
            er_14=round(er_14, 4),
            rsi_14=round(rsi_14, 2),
            stop_distance_price=round(stop_dist, 5),
            initial_sl=round(initial_sl, 5),
            current_sl=round(initial_sl, 5),
            volume=round(volume, 4),
            portfolio_heat_at_entry=round(portfolio_heat, 4),
            position_count_at_entry=position_count,
            status="OPEN"
        )

        # ── RISK & EXECUTION ANOMALY AUDIT ──
        if portfolio_heat > 0.0601:
            self.log_risk_alert("HEAT_CAP_VIOLATION", f"Trade {trade_id} entered with Portfolio Heat = {portfolio_heat*100:.2f}% (Limit: 6.0%)")
            rec.status = "ANOMALY"

        if position_count > 2:
            self.log_risk_alert("POSITION_CAP_VIOLATION", f"Trade {trade_id} entered with Position Count = {position_count} (Limit: 2)")
            rec.status = "ANOMALY"

        if slippage_pips > 3.0:
            self.log_risk_alert("EXCESSIVE_SLIPPAGE", f"Trade {trade_id} ({symbol}) experienced {slippage_pips} pips entry slippage!")

        # Spread spike check (Spread > 0.35 * ATR)
        if atr_14 > 0 and (spread_price / atr_14) > 0.35:
            self.log_risk_alert("SPREAD_SPIKE_DETECTED", f"Trade {trade_id} ({symbol}) entered during spread spike (Spread: {spread_price}, ATR: {atr_14})")

        self.trades[trade_id] = rec
        self.save_state()
        self._append_trade_to_csv(rec)
        return rec

    def record_exit_telemetry(
        self,
        trade_id: str,
        exit_signal_time: datetime,
        actual_exit_time: datetime,
        theoretical_exit: float,
        actual_exit: float,
        exit_reason: str,
        tick_size: float,
        tick_value: float,
        actual_broker_pnl_thb: float
    ) -> Optional[ForwardTradeRecord]:
        """
        Records exit telemetry and calculates friction drag.
        """
        if trade_id not in self.trades:
            self.log_broker_error("MISSING_TRADE_ON_EXIT", f"Attempted to close untracked trade ID {trade_id}!")
            return None

        rec = self.trades[trade_id]
        rec.exit_signal_time = exit_signal_time.strftime("%Y-%m-%d %H:%M:%S")
        rec.actual_exit_time = actual_exit_time.strftime("%Y-%m-%d %H:%M:%S")
        rec.theoretical_exit = round(theoretical_exit, 5)
        rec.actual_exit = round(actual_exit, 5)
        rec.exit_reason = exit_reason

        exit_slip = (theoretical_exit - actual_exit) if rec.direction == "LONG" else (actual_exit - theoretical_exit)
        rec.exit_slippage_price = round(exit_slip, 5)

        # Theoretical P&L (Gross from theoretical entry to theoretical exit)
        theo_diff = (theoretical_exit - rec.theoretical_entry) if rec.direction == "LONG" else (rec.theoretical_entry - theoretical_exit)
        theo_pnl = (theo_diff / tick_size) * tick_value * rec.volume
        rec.theoretical_pnl_thb = round(theo_pnl, 2)

        # Actual Realized P&L
        rec.actual_pnl_thb = round(actual_broker_pnl_thb, 2)
        rec.friction_drag_thb = round(theo_pnl - actual_broker_pnl_thb, 2)
        rec.status = "CLOSED"

        self.closed_trades.append(rec)
        del self.trades[trade_id]

        self.save_state()
        self._sync_entire_csv()
        return rec

    def _append_trade_to_csv(self, rec: ForwardTradeRecord):
        with open(FORWARD_TRADES_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(list(asdict(rec).values()))

    def _sync_entire_csv(self):
        all_recs = list(self.closed_trades) + list(self.trades.values())
        with open(FORWARD_TRADES_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(list(asdict(ForwardTradeRecord(""," ",False,None,"","","",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)).keys()))
            for r in all_recs:
                writer.writerow(list(asdict(r).values()))

    def log_risk_alert(self, alert_type: str, message: str):
        log_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚨 [RISK_ALERT] [{alert_type}] {message}"
        print(log_msg)
        with open(RISK_ALERTS_LOG, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")

    def log_broker_error(self, error_type: str, message: str):
        log_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ [BROKER_ERROR] [{error_type}] {message}"
        print(log_msg)
        with open(BROKER_ERRORS_LOG, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")

    def save_state(self):
        state = {
            "last_saved": datetime.now().isoformat(),
            "open_trades": {k: asdict(v) for k, v in self.trades.items()},
            "closed_trades": [asdict(v) for v in self.closed_trades]
        }
        with open(TELEMETRY_STATE_JSON, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)

    def load_state(self):
        if os.path.exists(TELEMETRY_STATE_JSON):
            try:
                with open(TELEMETRY_STATE_JSON, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    for k, v in state.get("open_trades", {}).items():
                        self.trades[k] = ForwardTradeRecord(**v)
                    for v in state.get("closed_trades", []):
                        self.closed_trades.append(ForwardTradeRecord(**v))
            except Exception as e:
                self.log_broker_error("STATE_LOAD_FAILED", f"Could not load state JSON: {e}")
