"""
Missed Signal Scanner for Frozen Strategy V2.6 (XAUUSD H1).
Analyzes historical / live candles to detect all valid V2.6 entry signals,
and classifies them into PAPER_EXECUTED vs MISSED_SIGNAL based on the user's
specific availability schedule (Asia/Bangkok UTC+7).

Schedule:
- ONLINE Windows  : 09:00–16:00, 17:00–22:00 (Asia/Bangkok)
- OFFLINE Windows : 16:00–17:00, 22:00–09:00 (Asia/Bangkok)

CRITICAL: Strategy V2.6 logic is 100% FROZEN. Never modifies strategy logic.
Never backfills orders when coming back online.
"""

import os
import sys
import csv
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rsi_trend_pullback.data.loader import Candle, DataLoader
from rsi_trend_pullback.indicator.rsi import WilderRSI
from rsi_trend_pullback.indicator.kaufman_er import KaufmanER
from rsi_trend_pullback.indicator.atr import WilderATR
from rsi_trend_pullback.state_machine.states import StrategyState, SignalType, TradingSignal
from rsi_trend_pullback.state_machine.engine_v2 import RSIStateMachineV2


# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION & CONSTANTS (FROZEN STRATEGY V2.6)
# ═════════════════════════════════════════════════════════════════════════════
RSI_PERIOD = 14
ER_PERIOD = 14
ATR_PERIOD = 14
UPPER_LEVEL = 60.0
PULLBACK_LEVEL = 50.0
LOWER_LEVEL = 40.0
ER_THRESHOLD = 0.40
ATR_MULTIPLIER = 2.5
MIN_ATR_COST_RATIO = 5.0
ESTIMATED_ROUNDTURN_FRICTION = 0.46 # $0.46/oz


class MissedSignalScanner:
    """
    Scans XAUUSD H1 candles using Frozen Strategy V2.6 and checks against Bangkok online schedule.
    """

    def __init__(self, data_timezone_offset_hours: int = 0):
        """
        :param data_timezone_offset_hours: Offset of the input dataset from UTC (e.g. 0 if UTC, 2 if broker GMT+2).
        """
        self.data_tz_offset = data_timezone_offset_hours

        self.indicator_rsi = WilderRSI(period=RSI_PERIOD)
        self.indicator_er = KaufmanER(period=ER_PERIOD)
        self.indicator_atr = WilderATR(period=ATR_PERIOD)
        self.state_machine = RSIStateMachineV2(
            upper_level=UPPER_LEVEL,
            pullback_level=PULLBACK_LEVEL,
            lower_level=LOWER_LEVEL,
            er_threshold=ER_THRESHOLD
        )
        self._price_history: List[float] = []

    def is_bot_online_in_bangkok(self, dt: datetime) -> bool:
        """
        Determines if the bot is ONLINE in Asia/Bangkok Timezone (UTC+7).
        Online Windows:
        - 09:00 - 16:00 (Hours 9, 10, 11, 12, 13, 14, 15)
        - 17:00 - 22:00 (Hours 17, 18, 19, 20, 21)
        Offline Windows:
        - 16:00 - 17:00 (Hour 16)
        - 22:00 - 09:00 (Hours 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8)
        """
        # Convert timestamp to Bangkok Time (UTC+7)
        # If input data is UTC (offset 0), add 7 hours
        bangkok_dt = dt + timedelta(hours=(7 - self.data_tz_offset))
        hour = bangkok_dt.hour

        # Check Online Windows
        if 9 <= hour < 16:
            return True
        if 17 <= hour < 22:
            return True
        return False

    def scan_dataset(self, candles: List[Candle]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes full historical/live scan on candles and generates signal logs and daily summaries.
        """
        signal_records: List[Dict[str, Any]] = []
        daily_map: Dict[str, Dict[str, int]] = defaultdict(lambda: {"paper": 0, "missed": 0, "total": 0})
        hourly_distribution: Dict[int, int] = defaultdict(int)
        weekday_distribution: Dict[str, int] = defaultdict(int)

        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for idx, candle in enumerate(candles):
            self._price_history.append(candle.close)
            rsi_val = self.indicator_rsi.update(candle.close)
            er_val = self.indicator_er.update(candle.close)
            atr_val = self.indicator_atr.update(candle)

            close_change_14 = None
            if len(self._price_history) > ER_PERIOD:
                close_change_14 = candle.close - self._price_history[-1 - ER_PERIOD]

            # Layer 1 Economic Filter (Entry only)
            is_vol_sufficient = (atr_val / ESTIMATED_ROUNDTURN_FRICTION) >= MIN_ATR_COST_RATIO if (atr_val and ESTIMATED_ROUNDTURN_FRICTION > 0) else False
            effective_er = er_val if is_vol_sufficient else 0.0

            state_before = self.state_machine.current_state.value
            signal = self.state_machine.evaluate_bar(
                bar_index=idx,
                timestamp=candle.timestamp,
                current_rsi=rsi_val,
                current_er=effective_er,
                close_change_14=close_change_14
            )
            state_after = self.state_machine.current_state.value

            # If an Entry Signal was generated at Close(T)
            if signal and signal.signal_type in (SignalType.LONG_ENTRY_SIGNAL, SignalType.SHORT_ENTRY_SIGNAL):
                direction = "LONG" if signal.signal_type == SignalType.LONG_ENTRY_SIGNAL else "SHORT"
                
                # Theoretical execution happens at Open(T+1)
                next_bar_time = candle.timestamp + timedelta(hours=1)
                theo_entry_price = candles[idx + 1].open if (idx + 1 < len(candles)) else candle.close

                # Check Online status at execution time Open(T+1)
                is_online = self.is_bot_online_in_bangkok(next_bar_time)
                status = "PAPER_EXECUTED" if is_online else "MISSED_SIGNAL"

                # Calculate Hard Stop
                hard_sl = round(theo_entry_price - (ATR_MULTIPLIER * atr_val) if direction == "LONG" else theo_entry_price + (ATR_MULTIPLIER * atr_val), 2)
                vol_ratio = (atr_val / ESTIMATED_ROUNDTURN_FRICTION) if atr_val else 0.0

                # Bangkok time representation
                bangkok_time = next_bar_time + timedelta(hours=(7 - self.data_tz_offset))
                date_str = bangkok_time.strftime("%Y-%m-%d")
                hour_val = bangkok_time.hour
                day_name = weekday_names[bangkok_time.weekday()]

                hourly_distribution[hour_val] += 1
                weekday_distribution[day_name] += 1

                daily_map[date_str]["total"] += 1
                if status == "PAPER_EXECUTED":
                    daily_map[date_str]["paper"] += 1
                    # In real execution, state machine is notified of order fill
                    self.state_machine.notify_order_executed(idx + 1, next_bar_time)
                else:
                    daily_map[date_str]["missed"] += 1
                    # CRITICAL: Missed signals NEVER backfill orders, but state machine remains intact

                record = {
                    "missed_signal_time": bangkok_time.strftime("%Y-%m-%d %H:%M:%S (Bangkok UTC+7)"),
                    "direction": direction,
                    "status": status,
                    "theoretical_entry": f"{theo_entry_price:.2f}",
                    "ATR14": f"{atr_val:.2f}" if atr_val else "0.00",
                    "ER14": f"{er_val:.4f}" if er_val else "0.0000",
                    "RSI14": f"{rsi_val:.2f}" if rsi_val else "0.00",
                    "volatility_ratio": f"{vol_ratio:.2f}",
                    "hard_stop_price": f"{hard_sl:.2f}",
                    "state": state_after,
                    "reason": signal.reason
                }
                signal_records.append(record)

        # Build Daily Summaries
        daily_summaries: List[Dict[str, Any]] = []
        for d_str in sorted(daily_map.keys()):
            counts = daily_map[d_str]
            daily_summaries.append({
                "date": d_str,
                "paper_signals": counts["paper"],
                "missed_signals": counts["missed"],
                "offline_hours": 12, # 11 hrs night (22-09) + 1 hr afternoon (16-17) = 12 hrs
                "total_signals": counts["total"]
            })

        total_sigs = len(signal_records)
        paper_sigs = sum(1 for r in signal_records if r["status"] == "PAPER_EXECUTED")
        missed_sigs = sum(1 for r in signal_records if r["status"] == "MISSED_SIGNAL")
        pct_missed = (missed_sigs / total_sigs * 100.0) if total_sigs > 0 else 0.0

        stats = {
            "total_signals": total_sigs,
            "paper_executed_signals": paper_sigs,
            "missed_signals": missed_sigs,
            "pct_missed": pct_missed,
            "hourly_distribution": dict(sorted(hourly_distribution.items())),
            "weekday_distribution": {k: weekday_distribution[k] for k in weekday_names if k in weekday_distribution}
        }

        return signal_records, daily_summaries, stats

    @staticmethod
    def export_csv_reports(
        signal_records: List[Dict[str, Any]],
        daily_summaries: List[Dict[str, Any]],
        output_signals_csv: str,
        output_daily_csv: str
    ) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(output_signals_csv)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(output_daily_csv)), exist_ok=True)

        # 1. Export Signal Records CSV
        with open(output_signals_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "missed_signal_time", "direction", "status", "theoretical_entry",
                "ATR14", "ER14", "RSI14", "volatility_ratio", "hard_stop_price",
                "state", "reason"
            ])
            for r in signal_records:
                writer.writerow([
                    r["missed_signal_time"], r["direction"], r["status"], r["theoretical_entry"],
                    r["ATR14"], r["ER14"], r["RSI14"], r["volatility_ratio"], r["hard_stop_price"],
                    r["state"], r["reason"]
                ])

        # 2. Export Daily Summary CSV
        with open(output_daily_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "paper_signals", "missed_signals", "offline_hours", "total_signals"])
            for d in daily_summaries:
                writer.writerow([
                    d["date"], d["paper_signals"], d["missed_signals"], d["offline_hours"], d["total_signals"]
                ])
