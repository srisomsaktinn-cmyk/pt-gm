"""
Strategy V2.7 Forward Validation Reporting & Divergence Analysis Engine.
Generates:
1. Daily Health Report (v27_daily_health_report.md)
2. 10-Trade Batch Performance Report (v27_batch_report.md)
3. Execution Divergence & Slippage Report (v27_execution_divergence_report.md)
4. Backtest vs. Live Forward Statistical Comparison (v27_backtest_vs_forward_report.md)
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict

from rsi_trend_pullback.monitoring.v27_forward_telemetry import (
    V27TelemetryDatabase,
    ForwardTradeRecord,
    FORWARD_TRADES_CSV,
    RISK_ALERTS_LOG,
    BROKER_ERRORS_LOG
)


class V27ReportingEngine:
    """
    Generates automated markdown diagnostic reports for Strategy V2.7 Forward Testing.
    """

    def __init__(self, db: V27TelemetryDatabase):
        self.db = db

    def generate_daily_health_report(self) -> str:
        report_path = "d:/Kaeha/v27_daily_health_report.md"
        open_trades = list(self.db.trades.values())
        closed_trades = self.db.closed_trades
        
        # Read recent alerts
        recent_alerts = []
        if os.path.exists(RISK_ALERTS_LOG):
            with open(RISK_ALERTS_LOG, "r", encoding="utf-8") as f:
                recent_alerts = f.readlines()[-10:]

        content = []
        content.append("# 🩺 STRATEGY V2.7: DAILY HEALTH & SYSTEM DIAGNOSTIC REPORT\n")
        content.append(f"> **Report Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC+7)")
        content.append(f"> **System Status:** {'🟢 HEALTHY' if len(recent_alerts) == 0 else '⚠️ ANOMALIES DETECTED'}\n")

        content.append("## 1. REAL-TIME PORTFOLIO METRICS\n")
        content.append(f"- **Active Open Positions:** {len(open_trades)} / 2 Max Positions")
        curr_heat = sum(t.portfolio_heat_at_entry for t in open_trades)
        content.append(f"- **Aggregate Open Heat:** {curr_heat * 100:.2f}% / 6.0% Hard Ceiling")
        content.append(f"- **Total Forward Closed Trades:** {len(closed_trades)} trades\n")

        content.append("## 2. ACTIVE POSITIONS IN MARKET\n")
        if open_trades:
            content.append("| Trade ID | Symbol | Type | Volume | Entry Price | Current SL | Heat at Entry | Latency (ms) |")
            content.append("|---|---|---|---|---|---|---|---|")
            for t in open_trades:
                content.append(f"| {t.trade_id} | {t.symbol} | {t.direction} | {t.volume} | {t.actual_entry:.5f} | {t.current_sl:.5f} | {t.portfolio_heat_at_entry*100:.2f}% | {t.execution_latency_ms:.1f} ms |")
        else:
            content.append("*No open positions currently in market (Awaiting closed H1 signals).*\n")

        content.append("\n## 3. RECENT RISK ALERTS & BROKER ANOMALIES\n")
        if recent_alerts:
            content.append("```text")
            for a in recent_alerts:
                content.append(a.strip())
            content.append("```\n")
        else:
            content.append("🟢 *Zero risk violations or broker errors logged.*\n")

        report_str = "\n".join(content)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_str)
        return report_path

    def generate_batch_report(self, batch_size: int = 10) -> str:
        report_path = "d:/Kaeha/v27_batch_report.md"
        closed = self.db.closed_trades

        content = []
        content.append("# 📦 STRATEGY V2.7: 10-TRADE BATCH ROLLING EVALUATION\n")
        content.append(f"> **Evaluated Batches:** {len(closed) // batch_size} Complete Batches ({len(closed)} Total Closed Trades)\n")

        if len(closed) < batch_size:
            content.append(f"*Insufficient trades for full batch evaluation ({len(closed)}/{batch_size} trades completed).*")
            content.append("Monitoring will generate complete batch metrics once 10 trades have closed.")
        else:
            # Group into batches of 10
            for b_idx in range(0, len(closed), batch_size):
                batch = closed[b_idx:b_idx + batch_size]
                b_num = (b_idx // batch_size) + 1
                wins = [t for t in batch if (t.actual_pnl_thb or 0.0) > 0]
                losses = [t for t in batch if (t.actual_pnl_thb or 0.0) < 0]
                gross_w = sum((t.actual_pnl_thb or 0.0) for t in wins)
                gross_l = abs(sum((t.actual_pnl_thb or 0.0) for t in losses))
                pf = (gross_w / gross_l) if gross_l > 0 else 999.0
                net_pnl = sum((t.actual_pnl_thb or 0.0) for t in batch)
                avg_slip = sum(t.slippage_pips for t in batch) / len(batch)
                tot_drag = sum((t.friction_drag_thb or 0.0) for t in batch)

                content.append(f"### Batch #{b_num} (Trades {b_idx+1} to {b_idx+len(batch)})\n")
                content.append(f"- **Win Rate:** {len(wins)/len(batch)*100:.1f}% ({len(wins)}W / {len(losses)}L)")
                content.append(f"- **Profit Factor (PF):** {pf:.2f}")
                content.append(f"- **Batch Realized P&L:** {net_pnl:+,.2f} THB")
                content.append(f"- **Average Entry Slippage:** {avg_slip:.2f} pips")
                content.append(f"- **Total Friction Drag:** {tot_drag:,.2f} THB\n")

        report_str = "\n".join(content)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_str)
        return report_path

    def generate_execution_divergence_report(self) -> str:
        report_path = "d:/Kaeha/v27_execution_divergence_report.md"
        all_trades = list(self.db.closed_trades) + list(self.db.trades.values())

        content = []
        content.append("# ⚡ STRATEGY V2.7: EXECUTION DIVERGENCE & SLIPPAGE AUDIT\n")
        content.append(f"> **Audited Live Trades:** {len(all_trades)} Total Executions\n")

        if not all_trades:
            content.append("*No live trades executed yet.*")
        else:
            avg_latency = sum(t.execution_latency_ms for t in all_trades) / len(all_trades)
            avg_entry_slip = sum(t.slippage_pips for t in all_trades) / len(all_trades)
            max_entry_slip = max(t.slippage_pips for t in all_trades)
            
            content.append("## 1. EXECUTION FIDELITY SUMMARY\n")
            content.append(f"- **Average Broker Execution Latency:** {avg_latency:.1f} ms")
            content.append(f"- **Average Entry Slippage:** {avg_entry_slip:.2f} pips")
            content.append(f"- **Peak Observed Slippage:** {max_entry_slip:.2f} pips")
            content.append(f"- **Slippage Anomaly Threshold:** 3.0 pips\n")

            content.append("## 2. TRADE-BY-TRADE SLIPPAGE & FRICTION BREAKDOWN\n")
            content.append("| Trade ID | Symbol | Latency (ms) | Spread | Theo Entry | Actual Entry | Slippage (pips) | Friction Drag |")
            content.append("|---|---|---|---|---|---|---|---|")
            for t in all_trades:
                drag_str = f"{t.friction_drag_thb:+,.2f} THB" if t.friction_drag_thb is not None else "OPEN"
                content.append(f"| {t.trade_id} | {t.symbol} | {t.execution_latency_ms:.1f} | {t.spread_price:.5f} | {t.theoretical_entry:.5f} | {t.actual_entry:.5f} | {t.slippage_pips:+.2f} | {drag_str} |")

        report_str = "\n".join(content)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_str)
        return report_path

    def generate_backtest_vs_forward_report(self) -> str:
        report_path = "d:/Kaeha/v27_backtest_vs_forward_report.md"
        closed = self.db.closed_trades

        # Baseline Frozen Targets
        bt_pf = 1.24
        bt_wr = 41.2
        bt_exp = 704.67
        bt_dd = 10.40

        content = []
        content.append("# ⚖️ STRATEGY V2.7: HISTORICAL BASELINE VS. LIVE FORWARD DEMO\n")
        content.append(f"> **Baseline Dataset:** 2020–2025 In-Sample Frozen Baseline (289 Trades)\n")
        content.append(f"> **Live Forward Sample:** XM MT5 Demo Live Executions ({len(closed)} Closed Trades)\n")

        if len(closed) == 0:
            content.append("## 1. BENCHMARK COMPARISON TABLE\n")
            content.append("| Metric | Frozen Historical Baseline (2020–2025) | Live Forward Demo Execution | Status |")
            content.append("|---|---|---|---|")
            content.append(f"| **Profit Factor (PF)** | **`1.24`** | *Awaiting Live Fills* | PENDING ⏳ |")
            content.append(f"| **Win Rate (%)** | **`41.2%`** | *Awaiting Live Fills* | PENDING ⏳ |")
            content.append(f"| **Expectancy per Trade** | **`+704.67 THB`** | *Awaiting Live Fills* | PENDING ⏳ |")
            content.append(f"| **Peak Drawdown (%)** | **`-10.40%`** | *0.00%* | PENDING ⏳ |")
        else:
            wins = [t for t in closed if (t.actual_pnl_thb or 0.0) > 0]
            losses = [t for t in closed if (t.actual_pnl_thb or 0.0) < 0]
            gw = sum((t.actual_pnl_thb or 0.0) for t in wins)
            gl = abs(sum((t.actual_pnl_thb or 0.0) for t in losses))
            fwd_pf = (gw / gl) if gl > 0 else 999.0
            fwd_wr = (len(wins) / len(closed) * 100.0)
            fwd_net = sum((t.actual_pnl_thb or 0.0) for t in closed)
            fwd_exp = fwd_net / len(closed)

            content.append("## 1. BENCHMARK COMPARISON TABLE\n")
            content.append("| Metric | Frozen Historical Baseline (2020–2025) | Live Forward Demo Execution | Status |")
            content.append("|---|---|---|---|")
            content.append(f"| **Profit Factor (PF)** | **`1.24`** | **`{fwd_pf:.2f}`** | {'🟢 ON TRACK' if fwd_pf >= 1.15 else '⚠️ DIVERGENCE'} |")
            content.append(f"| **Win Rate (%)** | **`41.2%`** | **`{fwd_wr:.1f}%`** | {'🟢 NORMAL' if abs(fwd_wr-41.2) < 10 else '⚠️ DIVERGENCE'} |")
            content.append(f"| **Expectancy per Trade** | **`+704.67 THB`** | **`{fwd_exp:+,.2f} THB`** | {'🟢 POSITIVE' if fwd_exp > 0 else '❌ NEGATIVE'} |")

        report_str = "\n".join(content)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_str)
        return report_path
