"""
Side-by-Side Controlled Experiment Runner: Strategy V1 vs Strategy V2 (Kaufman ER > 0.40).
Executes on exact identical XAUUSD H1 2020-2025 dataset with identical execution and cost parameters.
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any

from rsi_trend_pullback.data.loader import Candle, DataLoader
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.strategy.rsi_strategy import RSIStrategyEngine
from rsi_trend_pullback.strategy.v2_strategy import RSIStrategyV2Engine
from rsi_trend_pullback.execution.simulator import ExecutionConfig
from rsi_trend_pullback.metrics.performance import MetricsCalculator, PerformanceMetrics
from rsi_trend_pullback.reports.generator import ReportGenerator


def run_v1_vs_v2_experiment():
    output_dir = "d:/Kaeha/rsi_trend_pullback/output_v2_experiment"
    os.makedirs(output_dir, exist_ok=True)
    csv_data_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"

    # 1. Load Data
    if not os.path.exists(csv_data_path):
        raw_candles = generate_xauusd_h1_historical_dataset()
        save_xauusd_csv(raw_candles, csv_data_path)
    candles = DataLoader.load_from_csv(csv_data_path)

    dev_candles = [c for c in candles if c.timestamp.year in (2020, 2021, 2022)]
    val_candles = [c for c in candles if c.timestamp.year in (2023, 2024)]
    oos_candles = [c for c in candles if c.timestamp.year == 2025]

    # Realistic ECN Config for Gold (Identical for V1 & V2)
    real_config = ExecutionConfig.create_realistic(
        commission_rate=0.00003, # 0.003% notional (~$0.06/oz)
        spread=0.25,             # $0.25/oz (2.5 pips)
        slippage=0.15            # $0.15/oz (1.5 pips)
    )
    raw_config = ExecutionConfig.create_raw()

    # ── Run V1 (Locked Baseline) ──
    v1_real = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0)
    v1_real.run_backtest(candles)
    m_v1_real = MetricsCalculator.calculate(v1_real.closed_trades, v1_real.equity_curve, initial_capital=100000.0)

    v1_dev = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(dev_candles)
    m_v1_dev = MetricsCalculator.calculate(v1_dev.closed_trades, v1_dev.equity_curve, initial_capital=100000.0)

    v1_val = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(val_candles)
    m_v1_val = MetricsCalculator.calculate(v1_val.closed_trades, v1_val.equity_curve, initial_capital=100000.0)

    v1_oos = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(oos_candles)
    m_v1_oos = MetricsCalculator.calculate(v1_oos.closed_trades, v1_oos.equity_curve, initial_capital=100000.0)

    # ── Run V2 (With ER > 0.40 Regime Filter) ──
    v2_real = RSIStrategyV2Engine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0)
    v2_real.run_backtest(candles)
    m_v2_real = MetricsCalculator.calculate(v2_real.closed_trades, v2_real.equity_curve, initial_capital=100000.0)

    v2_dev = RSIStrategyV2Engine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(dev_candles)
    m_v2_dev = MetricsCalculator.calculate(v2_dev.closed_trades, v2_dev.equity_curve, initial_capital=100000.0)

    v2_val = RSIStrategyV2Engine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(val_candles)
    m_v2_val = MetricsCalculator.calculate(v2_val.closed_trades, v2_val.equity_curve, initial_capital=100000.0)

    v2_oos = RSIStrategyV2Engine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(oos_candles)
    m_v2_oos = MetricsCalculator.calculate(v2_oos.closed_trades, v2_oos.equity_curve, initial_capital=100000.0)

    # Export CSVs
    ReportGenerator.export_trade_log_csv(v1_real.closed_trades, f"{output_dir}/xauusd_v1_trades.csv")
    ReportGenerator.export_trade_log_csv(v2_real.closed_trades, f"{output_dir}/xauusd_v2_trades.csv")
    ReportGenerator.export_state_log_csv(v2_real.transition_history, f"{output_dir}/xauusd_v2_state_transitions.csv")

    return {
        "m_v1_real": m_v1_real, "m_v2_real": m_v2_real,
        "m_v1_dev": m_v1_dev,   "m_v2_dev": m_v2_dev,
        "m_v1_val": m_v1_val,   "m_v2_val": m_v2_val,
        "m_v1_oos": m_v1_oos,   "m_v2_oos": m_v2_oos,
        "v1_trades": v1_real.closed_trades,
        "v2_trades": v2_real.closed_trades,
    }


if __name__ == "__main__":
    run_v1_vs_v2_experiment()
