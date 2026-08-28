"""
Strategy V2.7 Missed Signal Auditor & Offline Opportunity Analyzer.
Evaluates offline time intervals when the MT5 bot was offline and determines whether
the complete Frozen V2.7 state machine would have generated and accepted a valid signal.

CRITICAL SEPARATION RULE:
- FORWARD_EXECUTED: Bot online + valid signal + MT5 demo order filled.
- MISSED_SIGNAL: Bot offline + complete Frozen V2.7 rules accepted.
- REJECTED_SIGNAL: Signal rejected by heat cap, position cap, or volume floor.
- NO_SIGNAL: Normal market noise without entry setup.

MISSED_SIGNALS ARE STRICTLY ISOLATED FROM FORWARD TRADING STATISTICS.
"""

import os
import sys
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict

from rsi_trend_pullback.data.loader import DataLoader, Candle
from rsi_trend_pullback.data.multi_asset_builder import build_all_multi_asset_datasets
from rsi_trend_pullback.research.broker_sizing_engine import XM_AUTHORITATIVE_METADATA, BrokerSizingEngineGate4
from rsi_trend_pullback.research.portfolio_heat_engine import PortfolioHeatEngineGate2, CandidateSignal, ActivePosition
from rsi_trend_pullback.research.multi_asset_calendar_engine import ASSET_SPECS, IndependentAssetStream
from rsi_trend_pullback.research.v27_integrity_pipeline import PositionLifecycleState, TradeRecord

MISSED_SIGNALS_CSV = "d:/Kaeha/missed_signals.csv"
MISSED_SUMMARY_JSON = "d:/Kaeha/missed_signal_summary.json"
MISSED_REPORT_MD = "d:/Kaeha/missed_signal_report.md"


@dataclass
class MissedSignalRecord:
    missed_signal_id: str
    timestamp: str
    symbol: str
    direction: str
    rsi_14: float
    er_14: float
    atr_14: float
    volatility_ratio: float
    theoretical_entry: float
    theoretical_stop: float
    theoretical_exit: Optional[float]
    exit_time: Optional[str]
    exit_reason: Optional[str]
    hypothetical_gross_pnl_thb: float
    hypothetical_net_pnl_thb: float
    reason_valid_signal: str
    portfolio_heat_projected: float
    position_count_at_signal: int
    classification: str = "MISSED_SIGNAL"
    bot_status: str = "OFFLINE"


class V27MissedSignalAuditor:
    """
    Evaluates complete frozen V2.7 strategy over user-defined offline windows.
    """

    def __init__(
        self,
        initial_equity_thb: float = 10000.0,
        broker_metadata: Dict[str, Any] = XM_AUTHORITATIVE_METADATA,
        asset_specs: Dict[str, Any] = ASSET_SPECS
    ):
        self.initial_equity_thb = initial_equity_thb
        self.broker_metadata = broker_metadata
        self.asset_specs = asset_specs
        self.offline_intervals: List[Tuple[datetime, datetime]] = []
        self.missed_signals: List[MissedSignalRecord] = []

    def add_offline_interval(self, start_dt: datetime, end_dt: datetime):
        """Adds an offline window (e.g. 09:00 -> 17:00 or specific days)."""
        self.offline_intervals.append((start_dt, end_dt))

    def is_bot_offline(self, ts: datetime) -> bool:
        for s, e in self.offline_intervals:
            if s <= ts <= e:
                return True
        return False

    def audit_offline_period(
        self,
        start_year: int = 2020,
        end_year: int = 2025
    ) -> Dict[str, Any]:
        """
        Runs causal simulation and flags valid signals that occurred during offline intervals.
        """
        paths = build_all_multi_asset_datasets()
        paths["XAUUSD"] = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"

        raw_data = {sym: DataLoader.load_csv(p) for sym, p in paths.items()}
        timeline_set = set()
        candles_by_time_sym = defaultdict(dict)
        for sym, candles in raw_data.items():
            for c in candles:
                if start_year <= c.timestamp.year <= end_year:
                    timeline_set.add(c.timestamp)
                    candles_by_time_sym[c.timestamp][sym] = c

        sorted_timestamps = sorted(list(timeline_set))

        # Setup independent asset streams
        streams = {sym: IndependentAssetStream(self.asset_specs[sym]) for sym in raw_data.keys()}
        active_sim_trades: Dict[str, TradeRecord] = {}
        trade_counter = 0
        missed_counter = 0

        current_equity = self.initial_equity_thb

        for ts in sorted_timestamps:
            candles_at_ts = candles_by_time_sym[ts]
            bot_offline = self.is_bot_offline(ts)

            # 1. Manage Active Simulation Trades (SL / Thesis Exit)
            for tid, tr in list(active_sim_trades.items()):
                sym = tr.symbol
                if sym not in candles_at_ts:
                    continue
                c = candles_at_ts[sym]
                meta = self.broker_metadata[sym]

                # Stop loss
                is_stopped = False
                sl_exit = tr.current_sl
                if tr.direction == "LONG":
                    if c.low <= tr.current_sl:
                        is_stopped = True
                        sl_exit = min(tr.current_sl, c.open) if c.open < tr.current_sl else tr.current_sl
                else:
                    if c.high >= tr.current_sl:
                        is_stopped = True
                        sl_exit = max(tr.current_sl, c.open) if c.open > tr.current_sl else tr.current_sl

                if is_stopped:
                    # Close trade
                    diff = (sl_exit - tr.entry_price) if tr.direction == "LONG" else (tr.entry_price - sl_exit)
                    gross = (diff / meta.trade_tick_size) * meta.trade_tick_value * (tr.volume / 1.0)
                    net = gross - (25.0 * (tr.volume / 0.01) * 0.5)
                    tr.exit_time = ts
                    tr.exit_price = sl_exit
                    tr.exit_reason = "STOP_LOSS_TOUCH"
                    tr.realized_pnl_thb = net
                    current_equity += net
                    del active_sim_trades[tid]

            # 2. Ingest Candles and Detect Signals
            raw_candidates: List[CandidateSignal] = []
            for sym, c in candles_at_ts.items():
                stream = streams[sym]
                meta = self.broker_metadata[sym]
                sig = stream.process_candle(c)

                if sig and sig.signal_type in ("LONG_EXIT_SIGNAL", "SHORT_EXIT_SIGNAL"):
                    for tid, tr in list(active_sim_trades.items()):
                        if tr.symbol == sym:
                            if (tr.direction == "LONG" and sig.signal_type == "LONG_EXIT_SIGNAL") or \
                               (tr.direction == "SHORT" and sig.signal_type == "SHORT_EXIT_SIGNAL"):
                                diff = (c.close - tr.entry_price) if tr.direction == "LONG" else (tr.entry_price - c.close)
                                gross = (diff / meta.trade_tick_size) * meta.trade_tick_value * (tr.volume / 1.0)
                                net = gross - (25.0 * (tr.volume / 0.01) * 0.5)
                                tr.exit_time = ts
                                tr.exit_price = c.close
                                tr.exit_reason = "THESIS_EXIT"
                                tr.realized_pnl_thb = net
                                current_equity += net
                                del active_sim_trades[tid]

                if sig and sig.signal_type in ("LONG_ENTRY_SIGNAL", "SHORT_ENTRY_SIGNAL"):
                    has_active = any(t.symbol == sym for t in active_sim_trades.values())
                    if not has_active:
                        direction = "LONG" if sig.signal_type == "LONG_ENTRY_SIGNAL" else "SHORT"
                        atr_val = stream.latest_atr or (c.close * 0.01)
                        sl_dist = 2.5 * atr_val
                        stop_p = c.close - sl_dist if direction == "LONG" else c.close + sl_dist

                        size_res = BrokerSizingEngineGate4.calculate_base_sizing(meta, current_equity, current_equity, sl_dist)
                        if size_res.is_accepted:
                            raw_candidates.append(CandidateSignal(
                                sym, False, direction, c.close, stop_p,
                                size_res.quantized_volume, meta.trade_tick_size, meta.trade_tick_value,
                                25.0, stream.latest_er or 0.0, meta.trade_tick_size * 25 / atr_val
                            ))

            # 3. Collision Resolution & Missed Signal Flagging
            if raw_candidates:
                # Convert active to ActivePosition for heat check
                active_pos_list = []
                for t in active_sim_trades.values():
                    m = self.broker_metadata[t.symbol]
                    st = streams[t.symbol]
                    cp = st.price_history[-1] if st.price_history else t.entry_price
                    active_pos_list.append(ActivePosition(
                        t.symbol, t.is_pyramid_leg, t.direction, t.entry_price, cp, t.current_sl,
                        t.volume, m.trade_tick_size, m.trade_tick_value, 25.0
                    ))

                resolved = PortfolioHeatEngineGate2.resolve_signal_collisions(active_pos_list, raw_candidates, current_equity)
                for cand, can_accept, reason in resolved:
                    if can_accept:
                        trade_counter += 1
                        t_id = f"{cand.symbol}_BASE_{trade_counter}"
                        t_rec = TradeRecord(
                            t_id, cand.symbol, False, None, cand.direction,
                            ts, cand.entry_price, cand.stop_price, cand.stop_price,
                            cand.volume, PositionLifecycleState.BASE_ACTIVE
                        )
                        active_sim_trades[t_id] = t_rec

                        # IF BOT WAS OFFLINE -> Record as MISSED_SIGNAL!
                        if bot_offline:
                            missed_counter += 1
                            m_rec = MissedSignalRecord(
                                missed_signal_id=f"MISSED_{cand.symbol}_{missed_counter:04d}",
                                timestamp=ts.strftime("%Y-%m-%d %H:%M:%S"),
                                symbol=cand.symbol,
                                direction=cand.direction,
                                rsi_14=round(streams[cand.symbol].rsi_history[-1] if streams[cand.symbol].rsi_history else 50.0, 2),
                                er_14=round(cand.er_14, 4),
                                atr_14=round(streams[cand.symbol].latest_atr or 0.0, 5),
                                volatility_ratio=round((streams[cand.symbol].latest_atr or 1.0) / (self.broker_metadata[cand.symbol].trade_tick_size * 25.0), 2),
                                theoretical_entry=cand.entry_price,
                                theoretical_stop=cand.stop_price,
                                theoretical_exit=None,
                                exit_time=None,
                                exit_reason=None,
                                hypothetical_gross_pnl_thb=0.0,
                                hypothetical_net_pnl_thb=0.0,
                                reason_valid_signal="Passed complete V2.7 Frozen rules & portfolio constraints",
                                portfolio_heat_projected=round(cand.spread_atr_ratio * 100, 2),
                                position_count_at_signal=len(active_sim_trades),
                                classification="MISSED_SIGNAL",
                                bot_status="OFFLINE"
                            )
                            self.missed_signals.append(m_rec)

        return self._generate_reports()

    def _generate_reports(self) -> Dict[str, Any]:
        # 1. Export missed_signals.csv
        with open(MISSED_SIGNALS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(MissedSignalRecord("","","","",0,0,0,0,0,0,0,"","",0,0,"",0,0)).keys()))
            writer.writeheader()
            for m in self.missed_signals:
                writer.writerow(asdict(m))

        # 2. Statistics Breakdown
        total_missed = len(self.missed_signals)
        signals_by_asset = defaultdict(int)
        signals_by_direction = defaultdict(int)
        for m in self.missed_signals:
            signals_by_asset[m.symbol] += 1
            signals_by_direction[m.direction] += 1

        summary_data = {
            "auditor": "Strategy V2.7 Missed Signal Auditor",
            "audit_timestamp": datetime.now().isoformat(),
            "total_offline_intervals": len(self.offline_intervals),
            "total_missed_signals": total_missed,
            "signals_by_asset": dict(signals_by_asset),
            "signals_by_direction": dict(signals_by_direction),
            "isolation_status": "STRICTLY_ISOLATED (0% impact on Forward metrics)"
        }

        # 3. Export missed_signal_summary.json
        with open(MISSED_SUMMARY_JSON, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=4)

        # 4. Export missed_signal_report.md
        with open(MISSED_REPORT_MD, "w", encoding="utf-8") as f:
            f.write("# 📡 STRATEGY V2.7: MISSED SIGNAL AUDIT REPORT\n\n")
            f.write("> **Purpose:** Identify signals that occurred while the bot was OFFLINE\n")
            f.write("> **Strict Isolation:** MISSED_SIGNALS are NEVER counted as Forward Trades, P&L, Win Rate, or Drawdown.\n\n")

            f.write("## 1. SUMMARY OF OFFLINE MISSED OPPORTUNITIES\n\n")
            f.write(f"- **Total Offline Windows Evaluated:** {len(self.offline_intervals)}\n")
            f.write(f"- **Total Missed Valid Signals:** {total_missed} signals\n")
            f.write(f"- **Breakdown by Asset:** {dict(signals_by_asset)}\n")
            f.write(f"- **Breakdown by Direction:** {dict(signals_by_direction)}\n\n")

            f.write("## 2. DETAILED LOG OF MISSED SIGNALS\n\n")
            if self.missed_signals:
                f.write("| Missed ID | Timestamp | Symbol | Dir | Entry Price | Stop Loss | ER14 | RSI14 | Reason Valid |\n")
                f.write("|---|---|---|---|---|---|---|---|---|\n")
                for m in self.missed_signals:
                    f.write(f"| {m.missed_signal_id} | {m.timestamp} | {m.symbol} | {m.direction} | {m.theoretical_entry:.5f} | {m.theoretical_stop:.5f} | {m.er_14:.4f} | {m.rsi_14:.1f} | {m.reason_valid_signal} |\n")
            else:
                f.write("*Zero missed signals occurred during the evaluated offline windows.*\n")

        return summary_data
