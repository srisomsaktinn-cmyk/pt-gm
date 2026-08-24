"""
Simulator and Runner for Strategy V2.6 Real-Time Shadow Paper Trading.
Executes bar-by-bar streaming, generates trade-by-trade shadow audits,
and produces 10-trade batch inspection reports.
"""

import os
from datetime import datetime
from typing import List

from rsi_trend_pullback.data.loader import DataLoader, Candle
from rsi_trend_pullback.paper_trading.shadow_engine import ShadowPaperTradingEngine
from rsi_trend_pullback.paper_trading.audit_logger import ShadowAuditLogger
from rsi_trend_pullback.paper_trading.reporter import PeriodicBatchReporter


def run_paper_trading_simulation(max_trades: int = 100):
    output_dir = "d:/Kaeha/rsi_trend_pullback/output_paper_trading"
    os.makedirs(output_dir, exist_ok=True)

    # Load authentic historical candles (2020-2025 stream)
    csv_data_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"
    candles = DataLoader.load_from_csv(csv_data_path)

    print("=" * 80)
    print("STRATEGY V2.6: REAL-TIME SHADOW PAPER TRADING SIMULATOR")
    print(f"Target: Continuous Data Collection (Monitoring first {max_trades} trades)")
    print("=" * 80)

    engine = ShadowPaperTradingEngine(
        rsi_period=14,
        er_period=14,
        atr_period=14,
        upper_level=60.0,
        pullback_level=50.0,
        lower_level=40.0,
        er_threshold=0.40,
        atr_multiplier=2.5,
        min_atr_cost_ratio=5.0,
        base_spread=0.25,
        base_slippage=0.15,
        commission_rate=0.00003,
        initial_capital=100000.0,
        units_per_trade=50.0
    )

    batch_reports = []
    last_reported_trade_count = 0

    for bar_idx, candle in enumerate(candles):
        closed_record, signal = engine.on_hourly_candle(bar_idx, candle)

        # Trigger batch report every 10 trades
        completed_trades = len(engine.audit_records)
        if completed_trades > 0 and completed_trades % 10 == 0 and completed_trades != last_reported_trade_count:
            last_reported_trade_count = completed_trades
            batch_num = completed_trades // 10
            rep = PeriodicBatchReporter.generate_10_trade_summary(engine.audit_records, batch_num)
            batch_reports.append(rep)
            print(f"\n{rep}")

        if completed_trades >= max_trades:
            break

    # Export complete Audit CSV
    audit_csv_path = os.path.join(output_dir, "xauusd_v26_shadow_audit_log.csv")
    ShadowAuditLogger.export_audit_csv(engine.audit_records, audit_csv_path)
    print(f"\n[COMPLETE] Exported {len(engine.audit_records)} shadow audit trade records to: {audit_csv_path}")

    return {
        "records": engine.audit_records,
        "batch_reports": batch_reports
    }


if __name__ == "__main__":
    run_paper_trading_simulation(max_trades=50)
