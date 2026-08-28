"""
Controlled Timeframe Experiment Runner: Strategy V2.6 on XAUUSD H1 vs XAUUSD M15 (2020-2025).
Evaluates whether Strategy V2.6 preserves positive expectancy on M15 or degrades due to noise and friction drag.
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any

from rsi_trend_pullback.data.loader import Candle, DataLoader
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.data.xauusd_m15_builder import generate_xauusd_m15_historical_dataset, save_xauusd_m15_csv
from rsi_trend_pullback.strategy.v26_strategy import RSIStrategyV26Engine
from rsi_trend_pullback.execution.simulator import ExecutionConfig
from rsi_trend_pullback.metrics.performance import MetricsCalculator, PerformanceMetrics
from rsi_trend_pullback.reports.generator import ReportGenerator


def run_timeframe_experiment():
    output_dir = "d:/Kaeha/rsi_trend_pullback/output_timeframe_experiment"
    os.makedirs(output_dir, exist_ok=True)

    path_h1 = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"
    path_m15 = "d:/Kaeha/rsi_trend_pullback/data/xauusd_m15_2020_2025.csv"

    if not os.path.exists(path_h1):
        c_h1 = generate_xauusd_h1_historical_dataset()
        save_xauusd_csv(c_h1, path_h1)
    if not os.path.exists(path_m15):
        c_m15 = generate_xauusd_m15_historical_dataset()
        save_xauusd_m15_csv(c_m15, path_m15)

    candles_h1 = DataLoader.load_from_csv(path_h1)
    candles_m15 = DataLoader.load_from_csv(path_m15)

    # Identical Realistic ECN Configuration
    real_config = ExecutionConfig.create_realistic(
        commission_rate=0.00003,
        spread=0.25,
        slippage=0.15
    )
    raw_config = ExecutionConfig.create_raw()

    # ── 1. Run H1 Baseline ──
    eng_h1_real = RSIStrategyV26Engine(
        atr_multiplier=2.5, min_atr_cost_ratio=5.0, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0
    ).run_backtest(candles_h1)
    m_h1_real = MetricsCalculator.calculate(eng_h1_real.closed_trades, eng_h1_real.equity_curve, initial_capital=100000.0)

    eng_h1_raw = RSIStrategyV26Engine(
        atr_multiplier=2.5, min_atr_cost_ratio=5.0, execution_config=raw_config, initial_capital=100000.0, units_per_trade=50.0
    ).run_backtest(candles_h1)
    m_h1_raw = MetricsCalculator.calculate(eng_h1_raw.closed_trades, eng_h1_raw.equity_curve, initial_capital=100000.0)

    # ── 2. Run M15 Research Candidate (100% Frozen V2.6 Logic) ──
    eng_m15_real = RSIStrategyV26Engine(
        atr_multiplier=2.5, min_atr_cost_ratio=5.0, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0
    ).run_backtest(candles_m15)
    m_m15_real = MetricsCalculator.calculate(eng_m15_real.closed_trades, eng_m15_real.equity_curve, initial_capital=100000.0)

    eng_m15_raw = RSIStrategyV26Engine(
        atr_multiplier=2.5, min_atr_cost_ratio=5.0, execution_config=raw_config, initial_capital=100000.0, units_per_trade=50.0
    ).run_backtest(candles_m15)
    m_m15_raw = MetricsCalculator.calculate(eng_m15_raw.closed_trades, eng_m15_raw.equity_curve, initial_capital=100000.0)

    # Export CSV trade logs
    ReportGenerator.export_trade_log_csv(eng_h1_real.closed_trades, f"{output_dir}/xauusd_h1_v26_trades.csv")
    ReportGenerator.export_trade_log_csv(eng_m15_real.closed_trades, f"{output_dir}/xauusd_m15_v26_trades.csv")

    return {
        "candles_h1": len(candles_h1),
        "candles_m15": len(candles_m15),
        "m_h1_real": m_h1_real,
        "m_h1_raw": m_h1_raw,
        "m_m15_real": m_m15_real,
        "m_m15_raw": m_m15_raw,
        "trades_h1": eng_h1_real.closed_trades,
        "trades_m15": eng_m15_real.closed_trades
    }


if __name__ == "__main__":
    res = run_timeframe_experiment()
    print("Timeframe Experiment Execution Finished.")
