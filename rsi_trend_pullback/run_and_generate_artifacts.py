"""
Full pipeline execution and artifact generator for Phase 9 XAUUSD H1 validation.
Generates CSVs, computes all statistics across all splits, and formats the final report.
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any

from rsi_trend_pullback.data.loader import Candle, DataLoader
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.strategy.rsi_strategy import RSIStrategyEngine
from rsi_trend_pullback.execution.simulator import ExecutionConfig
from rsi_trend_pullback.metrics.performance import MetricsCalculator, PerformanceMetrics
from rsi_trend_pullback.reports.generator import ReportGenerator
from rsi_trend_pullback.state_machine.states import PositionSide


def generate_all_xauusd_results():
    output_dir = "d:/Kaeha/rsi_trend_pullback/output_xauusd"
    os.makedirs(output_dir, exist_ok=True)
    csv_data_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"

    # Generate & load data
    candles = generate_xauusd_h1_historical_dataset()
    save_xauusd_csv(candles, csv_data_path)

    # Chronological splits
    dev_candles = [c for c in candles if c.timestamp.year in (2020, 2021, 2022)]
    val_candles = [c for c in candles if c.timestamp.year in (2023, 2024)]
    oos_candles = [c for c in candles if c.timestamp.year == 2025]

    # Costs
    raw_config = ExecutionConfig.create_raw()
    real_config = ExecutionConfig.create_realistic(
        commission_rate=0.00003, # 0.003% notional (~$0.06/oz at $2000 gold)
        spread=0.25,             # $0.25 / oz (2.5 pips)
        slippage=0.15            # $0.15 / oz (1.5 pips)
    )

    # 1. Full Period
    engine_full_raw = RSIStrategyEngine(execution_config=raw_config, initial_capital=100000.0, units_per_trade=50.0)
    engine_full_raw.run_backtest(candles)
    m_full_raw = MetricsCalculator.calculate(engine_full_raw.closed_trades, engine_full_raw.equity_curve, initial_capital=100000.0)

    engine_full_real = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0)
    engine_full_real.run_backtest(candles)
    m_full_real = MetricsCalculator.calculate(engine_full_real.closed_trades, engine_full_real.equity_curve, initial_capital=100000.0)

    # 2. Splits
    engine_dev_real = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0)
    engine_dev_real.run_backtest(dev_candles)
    m_dev_real = MetricsCalculator.calculate(engine_dev_real.closed_trades, engine_dev_real.equity_curve, initial_capital=100000.0)

    engine_val_real = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0)
    engine_val_real.run_backtest(val_candles)
    m_val_real = MetricsCalculator.calculate(engine_val_real.closed_trades, engine_val_real.equity_curve, initial_capital=100000.0)

    engine_oos_real = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0)
    engine_oos_real.run_backtest(oos_candles)
    m_oos_real = MetricsCalculator.calculate(engine_oos_real.closed_trades, engine_oos_real.equity_curve, initial_capital=100000.0)

    # Export CSVs
    ReportGenerator.export_trade_log_csv(engine_full_real.closed_trades, f"{output_dir}/xauusd_h1_full_trades_realistic.csv")
    ReportGenerator.export_state_log_csv(engine_full_real.transition_history, f"{output_dir}/xauusd_h1_state_transitions.csv")
    ReportGenerator.export_trade_log_csv(engine_dev_real.closed_trades, f"{output_dir}/xauusd_h1_dev_trades.csv")
    ReportGenerator.export_trade_log_csv(engine_val_real.closed_trades, f"{output_dir}/xauusd_h1_val_trades.csv")
    ReportGenerator.export_trade_log_csv(engine_oos_real.closed_trades, f"{output_dir}/xauusd_h1_oos_trades.csv")

    # Export Equity curves
    with open(f"{output_dir}/xauusd_equity_curve.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bar_index", "timestamp", "equity", "drawdown_amount", "drawdown_pct", "position_side"])
        for pt in engine_full_real.equity_curve:
            writer.writerow([pt.bar_index, pt.timestamp.isoformat(), f"{pt.equity:.2f}", f"{pt.drawdown_amount:.2f}", f"{pt.drawdown_pct:.2f}", pt.position_side.value])

    return {
        "candles_count": len(candles),
        "min_p": min(c.low for c in candles),
        "max_p": max(c.high for c in candles),
        "m_full_raw": m_full_raw,
        "m_full_real": m_full_real,
        "m_dev_real": m_dev_real,
        "m_val_real": m_val_real,
        "m_oos_real": m_oos_real,
        "trades": engine_full_real.closed_trades,
        "equity_curve": engine_full_real.equity_curve
    }


if __name__ == "__main__":
    generate_all_xauusd_results()
