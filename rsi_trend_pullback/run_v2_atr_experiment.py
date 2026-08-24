"""
Side-by-side Controlled Experiment: Strategy V2 Baseline vs Strategy V2 + ATR Stop Loss.
Evaluates ATR multipliers [1.5x, 2.0x, 2.5x, 3.0x] to determine whether a downside volatility
stop preserves capital without suffocating trend runners.
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any

from rsi_trend_pullback.data.loader import Candle, DataLoader
from rsi_trend_pullback.strategy.v2_strategy import RSIStrategyV2Engine
from rsi_trend_pullback.strategy.v2_atr_strategy import RSIStrategyV2ATREngine
from rsi_trend_pullback.execution.simulator import ExecutionConfig
from rsi_trend_pullback.metrics.performance import MetricsCalculator, PerformanceMetrics
from rsi_trend_pullback.reports.generator import ReportGenerator


def run_atr_stop_experiment():
    output_dir = "d:/Kaeha/rsi_trend_pullback/output_v2_atr"
    os.makedirs(output_dir, exist_ok=True)
    csv_data_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"

    candles = DataLoader.load_from_csv(csv_data_path)
    dev_candles = [c for c in candles if c.timestamp.year in (2020, 2021, 2022)]
    val_candles = [c for c in candles if c.timestamp.year in (2023, 2024)]
    oos_candles = [c for c in candles if c.timestamp.year == 2025]

    real_config = ExecutionConfig.create_realistic(
        commission_rate=0.00003,
        spread=0.25,
        slippage=0.15
    )

    # 1. Baseline V2 (No Price Stop Loss)
    eng_v2_base = RSIStrategyV2Engine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(candles)
    m_v2_base = MetricsCalculator.calculate(eng_v2_base.closed_trades, eng_v2_base.equity_curve, initial_capital=100000.0)

    # 2. ATR Stop Variations
    atr_mults = [1.5, 2.0, 2.5, 3.0]
    atr_results = {}

    for mult in atr_mults:
        # Full 6-Year
        eng_full = RSIStrategyV2ATREngine(atr_multiplier=mult, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(candles)
        m_full = MetricsCalculator.calculate(eng_full.closed_trades, eng_full.equity_curve, initial_capital=100000.0)

        # Dev
        eng_dev = RSIStrategyV2ATREngine(atr_multiplier=mult, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(dev_candles)
        m_dev = MetricsCalculator.calculate(eng_dev.closed_trades, eng_dev.equity_curve, initial_capital=100000.0)

        # Val
        eng_val = RSIStrategyV2ATREngine(atr_multiplier=mult, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(val_candles)
        m_val = MetricsCalculator.calculate(eng_val.closed_trades, eng_val.equity_curve, initial_capital=100000.0)

        # OOS
        eng_oos = RSIStrategyV2ATREngine(atr_multiplier=mult, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(oos_candles)
        m_oos = MetricsCalculator.calculate(eng_oos.closed_trades, eng_oos.equity_curve, initial_capital=100000.0)

        # Export CSV for each variation
        ReportGenerator.export_trade_log_csv(eng_full.closed_trades, f"{output_dir}/xauusd_v2_atr_{mult}x_trades.csv")

        atr_results[mult] = {
            "m_full": m_full,
            "m_dev": m_dev,
            "m_val": m_val,
            "m_oos": m_oos,
            "trades": eng_full.closed_trades,
            "equity_curve": eng_full.equity_curve
        }

    return {
        "m_v2_base": m_v2_base,
        "v2_base_trades": eng_v2_base.closed_trades,
        "atr_results": atr_results
    }


if __name__ == "__main__":
    run_atr_stop_experiment()
