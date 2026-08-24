"""
Comprehensive Backtest Runner & CLI for RSI(14) Trend Pullback Re-entry — Strategy V1.
Executes test suite, runs Dataset A (In-sample/Dev) and Dataset B (Out-of-sample),
exports CSV logs, and generates formatted reports.
"""

import os
import sys
from datetime import datetime

from .data.dataset_gen import DatasetGenerator
from .strategy.rsi_strategy import RSIStrategyEngine
from .execution.simulator import ExecutionConfig
from .metrics.performance import MetricsCalculator
from .reports.generator import ReportGenerator
from .tests.test_all_19 import run_all_unit_tests


def run_full_pipeline(output_dir: str = "d:/Kaeha/rsi_trend_pullback/output") -> None:
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 80)
    print("RSI(14) TREND PULLBACK RE-ENTRY — STRATEGY V1 BACKTEST PIPELINE")
    print("=" * 80)

    # ── Phase 1: Run Unit Tests ──
    tests_passed = run_all_unit_tests()
    if not tests_passed:
        print("Pipeline aborted due to unit test failures.")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("RUNNING BACKTESTS ON DATASET A & DATASET B")
    print("=" * 80)

    # ── Phase 2: Dataset A (In-Sample / Dev: 2000 bars) ──
    print("\n>>> Generating Dataset A (Development / Sanity Dataset: 2,000 bars)...")
    dataset_a = DatasetGenerator.generate_deterministic_dataset_a(bars=2000)

    # Raw execution
    engine_a_raw = RSIStrategyEngine(execution_config=ExecutionConfig.create_raw())
    engine_a_raw.run_backtest(dataset_a)
    metrics_a_raw = MetricsCalculator.calculate(engine_a_raw.closed_trades, engine_a_raw.equity_curve)

    # Realistic execution
    engine_a_real = RSIStrategyEngine(execution_config=ExecutionConfig.create_realistic(
        commission_rate=0.0002, spread=0.0001, slippage=0.00005
    ))
    engine_a_real.run_backtest(dataset_a)
    metrics_a_real = MetricsCalculator.calculate(engine_a_real.closed_trades, engine_a_real.equity_curve)

    # Export Dataset A Logs
    ReportGenerator.export_trade_log_csv(
        engine_a_real.closed_trades,
        os.path.join(output_dir, "dataset_a_realistic_trades.csv")
    )
    ReportGenerator.export_state_log_csv(
        engine_a_real.transition_history,
        os.path.join(output_dir, "dataset_a_state_transitions.csv")
    )

    print(f"Dataset A Realistic: {metrics_a_real.total_trades} trades | Win Rate: {metrics_a_real.win_rate_pct:.1f}% | Net P&L: ${metrics_a_real.total_net_pnl:+,.2f} | PF: {metrics_a_real.profit_factor:.2f}")

    # ── Phase 3: Dataset B (Out-of-Sample: 2000 bars) ──
    print("\n>>> Generating Dataset B (Out-of-Sample Validation Dataset: 2,000 bars)...")
    dataset_b = DatasetGenerator.generate_deterministic_dataset_b(bars=2000)

    # Raw execution
    engine_b_raw = RSIStrategyEngine(execution_config=ExecutionConfig.create_raw())
    engine_b_raw.run_backtest(dataset_b)
    metrics_b_raw = MetricsCalculator.calculate(engine_b_raw.closed_trades, engine_b_raw.equity_curve)

    # Realistic execution
    engine_b_real = RSIStrategyEngine(execution_config=ExecutionConfig.create_realistic(
        commission_rate=0.0002, spread=0.0001, slippage=0.00005
    ))
    engine_b_real.run_backtest(dataset_b)
    metrics_b_real = MetricsCalculator.calculate(engine_b_real.closed_trades, engine_b_real.equity_curve)

    # Export Dataset B Logs
    ReportGenerator.export_trade_log_csv(
        engine_b_real.closed_trades,
        os.path.join(output_dir, "dataset_b_realistic_trades.csv")
    )
    ReportGenerator.export_state_log_csv(
        engine_b_real.transition_history,
        os.path.join(output_dir, "dataset_b_state_transitions.csv")
    )

    print(f"Dataset B Realistic: {metrics_b_real.total_trades} trades | Win Rate: {metrics_b_real.win_rate_pct:.1f}% | Net P&L: ${metrics_b_real.total_net_pnl:+,.2f} | PF: {metrics_b_real.profit_factor:.2f}")

    # ── Generate Markdown Reports ──
    report_md_path = os.path.join(output_dir, "backtest_comprehensive_report.md")
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("# RSI(14) Trend Pullback Re-entry — Strategy V1 Quantitative Report\n\n")
        f.write("> **Specification Status:** 100% Locked Spec | Zero Optimization | Locked Parameters: RSI(14), 60/50/40\n\n")
        f.write(ReportGenerator.format_markdown_summary("Dataset A (In-Sample / Dev)", metrics_a_real, is_realistic=True))
        f.write("\n\n---\n\n")
        f.write(ReportGenerator.format_markdown_summary("Dataset A (Raw Zero-Cost Baseline)", metrics_a_raw, is_realistic=False))
        f.write("\n\n---\n\n")
        f.write(ReportGenerator.format_markdown_summary("Dataset B (Out-of-Sample Validation)", metrics_b_real, is_realistic=True))
        f.write("\n\n---\n\n")
        f.write(ReportGenerator.format_markdown_summary("Dataset B (Raw Zero-Cost Baseline)", metrics_b_raw, is_realistic=False))

    print(f"\n[DONE] Reports and CSV logs exported to: {output_dir}")


if __name__ == "__main__":
    run_full_pipeline()
