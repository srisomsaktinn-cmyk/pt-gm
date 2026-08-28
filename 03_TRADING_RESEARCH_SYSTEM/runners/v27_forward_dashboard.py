"""
Strategy V2.7 Live Forward Telemetry & System Health Dashboard.
Displays real-time terminal metrics:
- MT5 Connection & Account Balance
- Active positions & current open portfolio heat
- Real-time slippage & execution latency
- Alert stream & anomaly detection
- Automatically refreshes diagnostic reports
"""

import os
import sys
import time
from datetime import datetime

sys.path.insert(0, "d:/Kaeha")

from rsi_trend_pullback.monitoring.v27_forward_telemetry import (
    V27TelemetryDatabase,
    RISK_ALERTS_LOG,
    BROKER_ERRORS_LOG
)
from rsi_trend_pullback.monitoring.v27_reporting_engine import V27ReportingEngine

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


def render_dashboard():
    db = V27TelemetryDatabase()
    reporter = V27ReportingEngine(db)

    # Generate all reports
    reporter.generate_daily_health_report()
    reporter.generate_batch_report()
    reporter.generate_execution_divergence_report()
    reporter.generate_backtest_vs_forward_report()

    os.system("cls" if os.name == "nt" else "clear")

    print("=" * 95)
    print("  STRATEGY V2.7: LIVE FORWARD TELEMETRY & SYSTEM HEALTH DASHBOARD")
    print(f"  Current Local Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC+7) | Status: 🟢 MONITORING ACTIVE")
    print("=" * 95)

    # 1. MT5 Account Telemetry
    if MT5_AVAILABLE and mt5.initialize():
        acct = mt5.account_info()
        if acct:
            print("\n--- 1. MT5 ACCOUNT TELEMETRY ---")
            print(f"  • Broker:          {acct.company} ({acct.server})")
            print(f"  • Login ID:        {acct.login} (Mode: {'🟢 DEMO' if acct.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO else '🚨 REAL'})")
            print(f"  • Balance:         {acct.balance:,.2f} {acct.currency}")
            print(f"  • Equity:          {acct.equity:,.2f} {acct.currency}")
            print(f"  • Free Margin:     {acct.margin_free:,.2f} {acct.currency}")
            print(f"  • Margin Level:    {acct.margin_level:.1f}%")

    # 2. Real-Time Risk & Portfolio Constraints
    open_trades = list(db.trades.values())
    curr_heat = sum(t.portfolio_heat_at_entry for t in open_trades)
    print("\n--- 2. REAL-TIME RISK & PORTFOLIO CONSTRAINTS ---")
    print(f"  • Active Open Positions:    {len(open_trades)} / 2 Max Positions ({'🟢 NORMAL' if len(open_trades) <= 2 else '🚨 BREACH'})")
    print(f"  • Aggregate Portfolio Heat: {curr_heat*100:.2f}% / 6.00% Hard Ceiling ({'🟢 NORMAL' if curr_heat <= 0.060 else '🚨 BREACH'})")
    print(f"  • Total Completed Trades:   {len(db.closed_trades)} forward executions")

    # 3. Active Positions Table
    print("\n--- 3. ACTIVE POSITIONS IN MARKET ---")
    if open_trades:
        print(f"  {'Trade ID':<18} | {'Symbol':<8} | {'Type':<5} | {'Vol':<5} | {'Entry Price':<12} | {'Current SL':<12} | {'Heat':<7} | {'Latency':<8}")
        print("  " + "-" * 90)
        for t in open_trades:
            print(f"  {t.trade_id:<18} | {t.symbol:<8} | {t.direction:<5} | {t.volume:<5.2f} | {t.actual_entry:<12.5f} | {t.current_sl:<12.5f} | {t.portfolio_heat_at_entry*100:<6.2f}% | {t.execution_latency_ms:<6.1f} ms")
    else:
        print("  🟢 No open positions. Awaiting closed H1 candle signals.")

    # 4. Recent Risk Alerts & Anomaly Stream
    print("\n--- 4. RECENT SYSTEM ALERTS & ANOMALIES ---")
    if os.path.exists(RISK_ALERTS_LOG):
        with open(RISK_ALERTS_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                for line in lines[-5:]:
                    print(f"  {line.strip()}")
            else:
                print("  🟢 Zero risk violations logged.")
    else:
        print("  🟢 Zero risk violations logged.")

    print("\n" + "=" * 95)
    print("  Report Artifacts Updated: v27_daily_health_report.md | v27_batch_report.md | v27_execution_divergence_report.md")
    print("=" * 95)


if __name__ == "__main__":
    render_dashboard()
