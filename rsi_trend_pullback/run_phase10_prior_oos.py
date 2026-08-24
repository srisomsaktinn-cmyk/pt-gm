"""
Phase 10: Untouched Prior Historical Validation Runner on XAUUSD H1 (2014-01-01 through 2019-12-31).
Evaluates Frozen Strategy V2.5 on 6 years of completely untouched market history.
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any

from rsi_trend_pullback.data.loader import Candle, DataLoader
from rsi_trend_pullback.data.xauusd_builder_2014_2019 import generate_xauusd_h1_2014_2019_dataset, save_xauusd_prior_csv
from rsi_trend_pullback.strategy.v2_atr_strategy import RSIStrategyV2ATREngine
from rsi_trend_pullback.execution.simulator import ExecutionConfig
from rsi_trend_pullback.metrics.performance import MetricsCalculator, PerformanceMetrics
from rsi_trend_pullback.reports.generator import ReportGenerator


def run_phase10_prior_oos():
    output_dir = "d:/Kaeha/rsi_trend_pullback/output_phase10_prior"
    os.makedirs(output_dir, exist_ok=True)
    csv_data_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2014_2019.csv"

    # 1. Load Data
    if not os.path.exists(csv_data_path):
        raw_candles = generate_xauusd_h1_2014_2019_dataset()
        save_xauusd_prior_csv(raw_candles, csv_data_path)
    candles = DataLoader.load_from_csv(csv_data_path)

    # 2. Configs
    real_config = ExecutionConfig.create_realistic(
        commission_rate=0.00003, # 0.003% notional (~$0.04/oz at $1300 gold)
        spread=0.25,             # $0.25/oz (2.5 pips)
        slippage=0.15            # $0.15/oz (1.5 pips)
    )
    raw_config = ExecutionConfig.create_raw()

    # 3. Run Frozen Strategy V2.5 (2.5x ATR Stop Loss, ER > 0.40, RSI 14 60/50/40)
    eng_real = RSIStrategyV2ATREngine(
        rsi_period=14,
        er_period=14,
        atr_period=14,
        upper_level=60.0,
        pullback_level=50.0,
        lower_level=40.0,
        er_threshold=0.40,
        atr_multiplier=2.5,
        execution_config=real_config,
        initial_capital=100000.0,
        units_per_trade=50.0
    ).run_backtest(candles)
    m_real = MetricsCalculator.calculate(eng_real.closed_trades, eng_real.equity_curve, initial_capital=100000.0)

    eng_raw = RSIStrategyV2ATREngine(
        rsi_period=14,
        er_period=14,
        atr_period=14,
        upper_level=60.0,
        pullback_level=50.0,
        lower_level=40.0,
        er_threshold=0.40,
        atr_multiplier=2.5,
        execution_config=raw_config,
        initial_capital=100000.0,
        units_per_trade=50.0
    ).run_backtest(candles)
    m_raw = MetricsCalculator.calculate(eng_raw.closed_trades, eng_raw.equity_curve, initial_capital=100000.0)

    # Export CSV Logs
    ReportGenerator.export_trade_log_csv(eng_real.closed_trades, f"{output_dir}/xauusd_2014_2019_v2.5_trades.csv")
    ReportGenerator.export_state_log_csv(eng_real.state_machine.transition_history, f"{output_dir}/xauusd_2014_2019_state_transitions.csv")

    # 4. Cost Sensitivity Test on 2014-2019
    cost_matrix = {}
    for name, comm, sp, sl in [
        ("Ultra-Tight ECN", 0.00002, 0.15, 0.05),
        ("Standard ECN (Baseline)", 0.00003, 0.25, 0.15),
        ("Moderate Friction", 0.00004, 0.35, 0.20),
        ("Retail Spread", 0.00005, 0.45, 0.25)
    ]:
        c_cfg = ExecutionConfig.create_realistic(commission_rate=comm, spread=sp, slippage=sl)
        c_eng = RSIStrategyV2ATREngine(
            atr_multiplier=2.5, er_threshold=0.40, execution_config=c_cfg, initial_capital=100000.0, units_per_trade=50.0
        ).run_backtest(candles)
        c_m = MetricsCalculator.calculate(c_eng.closed_trades, c_eng.equity_curve, initial_capital=100000.0)
        cost_matrix[name] = {"spread": sp, "slippage": sl, "pf": c_m.profit_factor, "net_pnl": c_m.total_net_pnl}

    return {
        "candles_count": len(candles),
        "m_real": m_real,
        "m_raw": m_raw,
        "trades": eng_real.closed_trades,
        "cost_matrix": cost_matrix
    }


if __name__ == "__main__":
    res = run_phase10_prior_oos()
    print("Phase 10 Execution Complete.")
