"""
Self-contained runner that executes the entire RSI strategy pipeline,
calculates all quantitative metrics, and generates all required artifacts.
"""

import math
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

# Execute the full pipeline directly
from rsi_trend_pullback.data.loader import Candle
from rsi_trend_pullback.data.dataset_gen import DatasetGenerator
from rsi_trend_pullback.indicator.rsi import WilderRSI
from rsi_trend_pullback.state_machine.states import StrategyState, SignalType, PositionSide
from rsi_trend_pullback.state_machine.engine import RSIStateMachine
from rsi_trend_pullback.execution.simulator import ExecutionEngine, ExecutionConfig
from rsi_trend_pullback.strategy.rsi_strategy import RSIStrategyEngine
from rsi_trend_pullback.metrics.performance import MetricsCalculator
from rsi_trend_pullback.reports.generator import ReportGenerator
from rsi_trend_pullback.tests.test_all_19 import run_all_unit_tests


def execute_and_export_all():
    # 1. Run all 19 unit tests
    test_result = run_all_unit_tests()
    assert test_result is True, "Unit tests failed!"

    # 2. Run Dataset A (In-Sample / Dev: 2000 bars)
    dataset_a = DatasetGenerator.generate_deterministic_dataset_a(bars=2000)
    
    # Dataset A - Raw
    engine_a_raw = RSIStrategyEngine(execution_config=ExecutionConfig.create_raw())
    engine_a_raw.run_backtest(dataset_a)
    metrics_a_raw = MetricsCalculator.calculate(engine_a_raw.closed_trades, engine_a_raw.equity_curve)

    # Dataset A - Realistic
    engine_a_real = RSIStrategyEngine(execution_config=ExecutionConfig.create_realistic(
        commission_rate=0.0002, spread=0.0001, slippage=0.00005
    ))
    engine_a_real.run_backtest(dataset_a)
    metrics_a_real = MetricsCalculator.calculate(engine_a_real.closed_trades, engine_a_real.equity_curve)

    # 3. Run Dataset B (Out-of-Sample: 2000 bars)
    dataset_b = DatasetGenerator.generate_deterministic_dataset_b(bars=2000)

    # Dataset B - Raw
    engine_b_raw = RSIStrategyEngine(execution_config=ExecutionConfig.create_raw())
    engine_b_raw.run_backtest(dataset_b)
    metrics_b_raw = MetricsCalculator.calculate(engine_b_raw.closed_trades, engine_b_raw.equity_curve)

    # Dataset B - Realistic
    engine_b_real = RSIStrategyEngine(execution_config=ExecutionConfig.create_realistic(
        commission_rate=0.0002, spread=0.0001, slippage=0.00005
    ))
    engine_b_real.run_backtest(dataset_b)
    metrics_b_real = MetricsCalculator.calculate(engine_b_real.closed_trades, engine_b_real.equity_curve)

    # Export all logs and reports
    out_dir = "d:/Kaeha/rsi_trend_pullback/output"
    ReportGenerator.export_trade_log_csv(engine_a_real.closed_trades, f"{out_dir}/dataset_a_realistic_trades.csv")
    ReportGenerator.export_state_log_csv(engine_a_real.transition_history, f"{out_dir}/dataset_a_state_transitions.csv")
    ReportGenerator.export_trade_log_csv(engine_b_real.closed_trades, f"{out_dir}/dataset_b_realistic_trades.csv")
    ReportGenerator.export_state_log_csv(engine_b_real.transition_history, f"{out_dir}/dataset_b_state_transitions.csv")

    report_content = (
        "# RSI(14) Trend Pullback Re-entry — Strategy V1 Quantitative Report\n\n"
        "> **Specification Status:** 100% Locked Spec | Zero Parameter Optimization | Locked: RSI(14), 60/50/40\n\n"
        + ReportGenerator.format_markdown_summary("Dataset A (In-Sample / Dev: 2,000 Bars)", metrics_a_real, is_realistic=True)
        + "\n\n---\n\n"
        + ReportGenerator.format_markdown_summary("Dataset A (Raw Baseline: Zero Cost)", metrics_a_raw, is_realistic=False)
        + "\n\n---\n\n"
        + ReportGenerator.format_markdown_summary("Dataset B (Out-of-Sample Validation: 2,000 Bars)", metrics_b_real, is_realistic=True)
        + "\n\n---\n\n"
        + ReportGenerator.format_markdown_summary("Dataset B (Raw Baseline: Zero Cost)", metrics_b_raw, is_realistic=False)
    )

    with open(f"{out_dir}/backtest_comprehensive_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)

    return {
        "metrics_a_real": metrics_a_real,
        "metrics_a_raw": metrics_a_raw,
        "metrics_b_real": metrics_b_real,
        "metrics_b_raw": metrics_b_raw,
        "trades_a_real": engine_a_real.closed_trades,
        "trades_b_real": engine_b_real.closed_trades,
        "transitions_a": engine_a_real.transition_history,
        "transitions_b": engine_b_real.transition_history,
        "report_content": report_content
    }
