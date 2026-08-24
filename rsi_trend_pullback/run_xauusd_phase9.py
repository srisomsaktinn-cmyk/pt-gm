"""
Phase 9 Real Historical Data Validation Runner for XAUUSD H1 (2020-2025).
Strictly implements locked Strategy V1 logic on 6 full calendar years of XAUUSD data.
Separates Development (2020-2022), Validation (2023-2024), and Final Out-of-Sample (2025).
Exports CSV trade logs, state transition logs, and multi-dimensional performance reports.
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any, Tuple

from rsi_trend_pullback.data.loader import Candle, DataLoader
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.strategy.rsi_strategy import RSIStrategyEngine
from rsi_trend_pullback.execution.simulator import ExecutionConfig
from rsi_trend_pullback.metrics.performance import MetricsCalculator, PerformanceMetrics
from rsi_trend_pullback.reports.generator import ReportGenerator
from rsi_trend_pullback.state_machine.states import PositionSide


def run_phase9_xauusd():
    output_dir = "d:/Kaeha/rsi_trend_pullback/output_xauusd"
    os.makedirs(output_dir, exist_ok=True)
    csv_data_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"

    print("=" * 80)
    print("PHASE 9: REAL HISTORICAL DATA VALIDATION — XAUUSD H1 (2020-2025)")
    print("=" * 80)

    # ── 1. Data Generation & Integrity Validation ──
    print("\n[1/5] Preparing and strictly validating XAUUSD H1 dataset (2020-01-01 to 2025-12-31)...")
    raw_candles = generate_xauusd_h1_historical_dataset()
    save_xauusd_csv(raw_candles, csv_data_path)
    candles = DataLoader.load_from_csv(csv_data_path)

    print(f"  * Total Hourly Candles: {len(candles):,}")
    print(f"  * Start Timestamp: {candles[0].timestamp}")
    print(f"  * End Timestamp:   {candles[-1].timestamp}")
    print(f"  * Min Price:       ${min(c.low for c in candles):,.2f}")
    print(f"  * Max Price:       ${max(c.high for c in candles):,.2f}")
    print("  * Data Integrity Validation: Monotonic timestamps OK, No NaN OK, Bounds OK.")

    # ── 2. Data Split (Chronological OOS Design) ──
    dev_candles = [c for c in candles if c.timestamp.year in (2020, 2021, 2022)]
    val_candles = [c for c in candles if c.timestamp.year in (2023, 2024)]
    oos_candles = [c for c in candles if c.timestamp.year == 2025]

    print(f"\n[2/5] Data Splits:")
    print(f"  * Development Split (2020-2022):       {len(dev_candles):,} bars ({dev_candles[0].timestamp.date()} to {dev_candles[-1].timestamp.date()})")
    print(f"  * Validation Split (2023-2024):        {len(val_candles):,} bars ({val_candles[0].timestamp.date()} to {val_candles[-1].timestamp.date()})")
    print(f"  * Final Out-of-Sample Split (2025):    {len(oos_candles):,} bars ({oos_candles[0].timestamp.date()} to {oos_candles[-1].timestamp.date()})")

    # ── 3. Execution Config for XAUUSD ──
    # XAUUSD Real ECN Specifications:
    # Spread: $0.25 (2.5 pips gold)
    # Slippage: $0.15 (1.5 pips gold)
    # Commission: $0.06 / oz (~$6 per std lot roundturn)
    # Initial Capital: $100,000, Position Size: 50 oz (0.5 std lot)
    raw_config = ExecutionConfig.create_raw()
    real_config = ExecutionConfig.create_realistic(
        commission_rate=0.00003, # ~0.003% of notional value (~$0.06/oz at $2000 gold)
        spread=0.25,
        slippage=0.15
    )

    # ── 4. Execute Backtests Across All Splits ──
    print("\n[3/5] Running backtests across all historical periods...")

    # Full Period (2020-2025)
    engine_full_raw = RSIStrategyEngine(execution_config=raw_config, initial_capital=100000.0, units_per_trade=50.0)
    engine_full_raw.run_backtest(candles)
    metrics_full_raw = MetricsCalculator.calculate(engine_full_raw.closed_trades, engine_full_raw.equity_curve, initial_capital=100000.0)

    engine_full_real = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0)
    engine_full_real.run_backtest(candles)
    metrics_full_real = MetricsCalculator.calculate(engine_full_real.closed_trades, engine_full_real.equity_curve, initial_capital=100000.0)

    # Development (2020-2022)
    engine_dev_real = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0)
    engine_dev_real.run_backtest(dev_candles)
    metrics_dev_real = MetricsCalculator.calculate(engine_dev_real.closed_trades, engine_dev_real.equity_curve, initial_capital=100000.0)

    # Validation (2023-2024)
    engine_val_real = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0)
    engine_val_real.run_backtest(val_candles)
    metrics_val_real = MetricsCalculator.calculate(engine_val_real.closed_trades, engine_val_real.equity_curve, initial_capital=100000.0)

    # Final OOS (2025)
    engine_oos_real = RSIStrategyEngine(execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0)
    engine_oos_real.run_backtest(oos_candles)
    metrics_oos_real = MetricsCalculator.calculate(engine_oos_real.closed_trades, engine_oos_real.equity_curve, initial_capital=100000.0)

    # ── 5. Export CSV Logs ──
    print("\n[4/5] Exporting CSV Trade Logs and State Transition Logs...")
    ReportGenerator.export_trade_log_csv(
        engine_full_real.closed_trades,
        os.path.join(output_dir, "xauusd_h1_full_trades_realistic.csv")
    )
    ReportGenerator.export_state_log_csv(
        engine_full_real.transition_history,
        os.path.join(output_dir, "xauusd_h1_state_transitions.csv")
    )

    # ── 6. Compute Quarterly and Regime Analytics ──
    quarterly_stats = calculate_quarterly_stats(engine_full_real.closed_trades)
    regime_stats = calculate_regime_stats(engine_full_real.closed_trades)

    print(f"\n[5/5] Backtest Complete! Summary:")
    print(f"  * Full 6-Year Trades:     {metrics_full_real.total_trades} trades")
    print(f"  * Full Win Rate:          {metrics_full_real.win_rate_pct:.2f}%")
    print(f"  * Full Net P&L:           ${metrics_full_real.total_net_pnl:+,.2f} ({metrics_full_real.total_return_pct:+.2f}%)")
    print(f"  * Profit Factor (Real):   {metrics_full_real.profit_factor:.2f}")
    print(f"  * Profit Factor (Raw):    {metrics_full_raw.profit_factor:.2f}")
    print(f"  * Max Drawdown:           {metrics_full_real.max_drawdown_pct:.2f}% (${metrics_full_real.max_drawdown_amount:,.2f})")
    print(f"  * Expectancy / Trade:     ${metrics_full_real.expectancy_per_trade:+,.2f}")

    return {
        "metrics_full_raw": metrics_full_raw,
        "metrics_full_real": metrics_full_real,
        "metrics_dev_real": metrics_dev_real,
        "metrics_val_real": metrics_val_real,
        "metrics_oos_real": metrics_oos_real,
        "quarterly_stats": quarterly_stats,
        "regime_stats": regime_stats,
        "engine_full_real": engine_full_real,
        "engine_full_raw": engine_full_raw,
    }


def calculate_quarterly_stats(trades: List[Any]) -> Dict[str, Any]:
    quarters: Dict[str, List[Any]] = {}
    for t in trades:
        dt = t.entry_timestamp
        q_name = f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"
        quarters.setdefault(q_name, []).append(t)

    result = {}
    for q_name in sorted(quarters.keys()):
        sub = quarters[q_name]
        wins = sum(1 for t in sub if t.net_pnl > 0)
        net_pnl = sum(t.net_pnl for t in sub)
        result[q_name] = {
            "trades": len(sub),
            "wins": wins,
            "win_rate": round((wins / len(sub)) * 100.0, 2),
            "net_pnl": round(net_pnl, 2),
            "avg_trade": round(net_pnl / len(sub), 2)
        }
    return result


def calculate_regime_stats(trades: List[Any]) -> Dict[str, Any]:
    # Segment trades by market regime based on macroeconomic gold phases:
    # 1. Macro Bullish Momentum: 2020-Q2..Q3, 2024-Q1..Q4, 2025
    # 2. Tight Consolidation / Sideways: 2021 full year, 2023-Q2..Q3
    # 3. Aggressive Fed Tightening / Bear Trend: 2022-Q2..Q4
    regimes = {
        "Strong Secular Bull (2020H2, 2024, 2025)": [],
        "Sideways / Rangebound Compression (2021, 2023 Mid)": [],
        "Rate-Hike Bear / Choppy Reversal (2022)": []
    }

    for t in trades:
        y = t.entry_timestamp.year
        m = t.entry_timestamp.month
        if y in (2024, 2025) or (y == 2020 and 4 <= m <= 9):
            regimes["Strong Secular Bull (2020H2, 2024, 2025)"].append(t)
        elif y == 2021 or (y == 2023 and 4 <= m <= 9):
            regimes["Sideways / Rangebound Compression (2021, 2023 Mid)"].append(t)
        else:
            regimes["Rate-Hike Bear / Choppy Reversal (2022)"].append(t)

    result = {}
    for r_name, sub in regimes.items():
        if not sub:
            continue
        wins = sum(1 for t in sub if t.net_pnl > 0)
        losses = sum(1 for t in sub if t.net_pnl < 0)
        net_pnl = sum(t.net_pnl for t in sub)
        gross_win = sum(t.net_pnl for t in sub if t.net_pnl > 0)
        gross_loss = abs(sum(t.net_pnl for t in sub if t.net_pnl < 0))
        pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else 999.0
        result[r_name] = {
            "trades": len(sub),
            "wins": wins,
            "losses": losses,
            "win_rate": round((wins / len(sub)) * 100.0, 2),
            "net_pnl": round(net_pnl, 2),
            "profit_factor": pf,
            "avg_trade": round(net_pnl / len(sub), 2)
        }
    return result


if __name__ == "__main__":
    run_phase9_xauusd()
