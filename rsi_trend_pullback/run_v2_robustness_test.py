"""
Comprehensive Robustness, Parameter Plateau, Opportunity Loss, and Cost Stress Test for Strategy V2.
Tests:
1. Parameter Neighborhoods: ER in [0.30, 0.35, 0.40, 0.45, 0.50]
2. Trade Opportunity Loss Analysis: Audit of all 156 filtered-out trades (did we miss >3R / >$30/oz winners?)
3. Cost Stress Test Matrix: Varying spread ($0.15 to $0.50) and slippage ($0.05 to $0.35)
4. Out-of-Sample Stability across all neighbor thresholds
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any, Tuple

from rsi_trend_pullback.data.loader import Candle, DataLoader
from rsi_trend_pullback.strategy.rsi_strategy import RSIStrategyEngine
from rsi_trend_pullback.strategy.v2_strategy import RSIStrategyV2Engine
from rsi_trend_pullback.execution.simulator import ExecutionConfig
from rsi_trend_pullback.metrics.performance import MetricsCalculator, PerformanceMetrics
from rsi_trend_pullback.portfolio.position import TradeRecord


def run_comprehensive_v2_robustness():
    output_dir = "d:/Kaeha/rsi_trend_pullback/output_v2_robustness"
    os.makedirs(output_dir, exist_ok=True)
    csv_data_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"

    candles = DataLoader.load_from_csv(csv_data_path)
    dev_candles = [c for c in candles if c.timestamp.year in (2020, 2021, 2022)]
    val_candles = [c for c in candles if c.timestamp.year in (2023, 2024)]
    oos_candles = [c for c in candles if c.timestamp.year == 2025]

    # Baseline Realistic ECN Config
    base_real_config = ExecutionConfig.create_realistic(
        commission_rate=0.00003,
        spread=0.25,
        slippage=0.15
    )

    # ═════════════════════════════════════════════════════════════════════════
    # 1. PARAMETER NEIGHBORHOOD / PLATEAU TEST (ER = 0.30, 0.35, 0.40, 0.45, 0.50)
    # ═════════════════════════════════════════════════════════════════════════
    er_thresholds = [0.30, 0.35, 0.40, 0.45, 0.50]
    plateau_results = {}

    for er_th in er_thresholds:
        # Full 2020-2025
        eng_full = RSIStrategyV2Engine(er_threshold=er_th, execution_config=base_real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(candles)
        m_full = MetricsCalculator.calculate(eng_full.closed_trades, eng_full.equity_curve, initial_capital=100000.0)

        # Dev
        eng_dev = RSIStrategyV2Engine(er_threshold=er_th, execution_config=base_real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(dev_candles)
        m_dev = MetricsCalculator.calculate(eng_dev.closed_trades, eng_dev.equity_curve, initial_capital=100000.0)

        # Val
        eng_val = RSIStrategyV2Engine(er_threshold=er_th, execution_config=base_real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(val_candles)
        m_val = MetricsCalculator.calculate(eng_val.closed_trades, eng_val.equity_curve, initial_capital=100000.0)

        # OOS
        eng_oos = RSIStrategyV2Engine(er_threshold=er_th, execution_config=base_real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(oos_candles)
        m_oos = MetricsCalculator.calculate(eng_oos.closed_trades, eng_oos.equity_curve, initial_capital=100000.0)

        plateau_results[er_th] = {
            "m_full": m_full,
            "m_dev": m_dev,
            "m_val": m_val,
            "m_oos": m_oos,
            "trades": eng_full.closed_trades
        }

    # ═════════════════════════════════════════════════════════════════════════
    # 2. TRADE OPPORTUNITY LOSS AUDIT (Examining Filtered-Out Trades)
    # ═════════════════════════════════════════════════════════════════════════
    # Run V1 (342 trades) and V2 (186 trades) to identify exactly which trades were filtered
    eng_v1 = RSIStrategyEngine(execution_config=base_real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(candles)
    v1_trades = eng_v1.closed_trades
    v2_trades = plateau_results[0.40]["trades"]

    # Match trades by signal_bar_index or entry_bar_index
    v2_entry_bars = {t.entry_bar_index for t in v2_trades}
    filtered_trades = [t for t in v1_trades if t.entry_bar_index not in v2_entry_bars]

    # Analyze filtered trades:
    filtered_wins = [t for t in filtered_trades if t.net_pnl > 0]
    filtered_losses = [t for t in filtered_trades if t.net_pnl < 0]
    
    # Big runners missed (e.g. Net PnL > $1,000 = +$20/oz on 50 oz, or +3R)
    big_runners_missed = [t for t in filtered_trades if t.net_pnl >= 1000.0]
    moderate_runners_missed = [t for t in filtered_trades if 500.0 <= t.net_pnl < 1000.0]
    small_wins_missed = [t for t in filtered_trades if 0 < t.net_pnl < 500.0]
    
    # Big disasters avoided (e.g. Net PnL < -$500)
    big_losses_avoided = [t for t in filtered_trades if t.net_pnl <= -500.0]
    moderate_losses_avoided = [t for t in filtered_trades if -500.0 < t.net_pnl <= -250.0]
    small_losses_avoided = [t for t in filtered_trades if -250.0 < t.net_pnl < 0]

    # ═════════════════════════════════════════════════════════════════════════
    # 3. COST STRESS TEST MATRIX FOR V2 (ER = 0.40)
    # ═════════════════════════════════════════════════════════════════════════
    cost_scenarios = [
        ("Ultra-Tight ECN", 0.00002, 0.15, 0.05),    # $0.15 spread, $0.05 slip
        ("Standard ECN (Baseline)", 0.00003, 0.25, 0.15), # $0.25 spread, $0.15 slip
        ("Moderate Friction", 0.00004, 0.35, 0.20),   # $0.35 spread, $0.20 slip
        ("High Friction / Retail", 0.00005, 0.45, 0.25), # $0.45 spread, $0.25 slip
        ("Extreme Stress", 0.00006, 0.60, 0.35),      # $0.60 spread, $0.35 slip
    ]
    cost_stress_results = {}

    for name, comm, sp, sl in cost_scenarios:
        cfg = ExecutionConfig.create_realistic(commission_rate=comm, spread=sp, slippage=sl)
        eng = RSIStrategyV2Engine(er_threshold=0.40, execution_config=cfg, initial_capital=100000.0, units_per_trade=50.0).run_backtest(candles)
        m = MetricsCalculator.calculate(eng.closed_trades, eng.equity_curve, initial_capital=100000.0)
        cost_stress_results[name] = {
            "spread": sp, "slippage": sl, "commission": comm,
            "net_pnl": m.total_net_pnl, "profit_factor": m.profit_factor,
            "win_rate": m.win_rate_pct, "expectancy": m.expectancy_per_trade,
            "max_dd": m.max_drawdown_pct, "fees_paid": m.total_fees + m.total_slippage
        }

    return {
        "plateau_results": plateau_results,
        "filtered_trades_count": len(filtered_trades),
        "filtered_wins_count": len(filtered_wins),
        "filtered_losses_count": len(filtered_losses),
        "filtered_net_pnl": sum(t.net_pnl for t in filtered_trades),
        "big_runners_missed": big_runners_missed,
        "moderate_runners_missed": moderate_runners_missed,
        "small_wins_missed": small_wins_missed,
        "big_losses_avoided": big_losses_avoided,
        "moderate_losses_avoided": moderate_losses_avoided,
        "small_losses_avoided": small_losses_avoided,
        "cost_stress_results": cost_stress_results
    }


if __name__ == "__main__":
    res = run_comprehensive_v2_robustness()
    print("Robustness Test Completed Successfully.")
