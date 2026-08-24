"""
Controlled Experiment Runner: Strategy V2.5 Baseline vs Strategy V2.6 (3-Layer Volatility-Cost Filter).
Evaluates Discovery Split (2014-2017), Validation Split (2018-2019), and Full Out-of-Sample (2020-2025).
"""

import os
import csv
from datetime import datetime
from typing import List, Dict, Any

from rsi_trend_pullback.data.loader import Candle, DataLoader
from rsi_trend_pullback.data.xauusd_builder_2014_2019 import generate_xauusd_h1_2014_2019_dataset, save_xauusd_prior_csv
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.strategy.v2_atr_strategy import RSIStrategyV2ATREngine
from rsi_trend_pullback.strategy.v26_strategy import RSIStrategyV26Engine
from rsi_trend_pullback.execution.simulator import ExecutionConfig
from rsi_trend_pullback.metrics.performance import MetricsCalculator, PerformanceMetrics
from rsi_trend_pullback.reports.generator import ReportGenerator


def run_volatility_experiment():
    output_dir = "d:/Kaeha/rsi_trend_pullback/output_v26_volatility"
    os.makedirs(output_dir, exist_ok=True)
    
    path_2014_2019 = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2014_2019.csv"
    path_2020_2025 = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"

    if not os.path.exists(path_2014_2019):
        c1 = generate_xauusd_h1_2014_2019_dataset()
        save_xauusd_prior_csv(c1, path_2014_2019)
    if not os.path.exists(path_2020_2025):
        c2 = generate_xauusd_h1_historical_dataset()
        save_xauusd_csv(c2, path_2020_2025)

    candles_prior = DataLoader.load_from_csv(path_2014_2019)
    candles_recent = DataLoader.load_from_csv(path_2020_2025)

    # ── Strict Splits ──
    discovery_candles = [c for c in candles_prior if 2014 <= c.timestamp.year <= 2017] # 2014-2017 (Discovery)
    validation_candles = [c for c in candles_prior if 2018 <= c.timestamp.year <= 2019] # 2018-2019 (Validation)
    oos_candles = candles_recent # 2020-2025 (Full Out-of-Sample)

    real_config = ExecutionConfig.create_realistic(
        commission_rate=0.00003,
        spread=0.25,
        slippage=0.15
    )

    # ── 1. Discovery Phase (2014-2017) ──
    # V2.5 Baseline
    eng_v25_disc = RSIStrategyV2ATREngine(atr_multiplier=2.5, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(discovery_candles)
    m_v25_disc = MetricsCalculator.calculate(eng_v25_disc.closed_trades, eng_v25_disc.equity_curve, initial_capital=100000.0)

    # V2.6 with Friction Ratio = 5.0x ($ATR >= $2.30)
    eng_v26_disc_5 = RSIStrategyV26Engine(min_atr_cost_ratio=5.0, atr_multiplier=2.5, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(discovery_candles)
    m_v26_disc_5 = MetricsCalculator.calculate(eng_v26_disc_5.closed_trades, eng_v26_disc_5.equity_curve, initial_capital=100000.0)

    # V2.6 with Friction Ratio = 6.0x ($ATR >= $2.76)
    eng_v26_disc_6 = RSIStrategyV26Engine(min_atr_cost_ratio=6.0, atr_multiplier=2.5, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(discovery_candles)
    m_v26_disc_6 = MetricsCalculator.calculate(eng_v26_disc_6.closed_trades, eng_v26_disc_6.equity_curve, initial_capital=100000.0)

    # ── 2. Validation Phase (2018-2019) ──
    eng_v25_val = RSIStrategyV2ATREngine(atr_multiplier=2.5, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(validation_candles)
    m_v25_val = MetricsCalculator.calculate(eng_v25_val.closed_trades, eng_v25_val.equity_curve, initial_capital=100000.0)

    eng_v26_val = RSIStrategyV26Engine(min_atr_cost_ratio=5.0, atr_multiplier=2.5, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(validation_candles)
    m_v26_val = MetricsCalculator.calculate(eng_v26_val.closed_trades, eng_v26_val.equity_curve, initial_capital=100000.0)

    # ── 3. Final Out-of-Sample Phase (2020-2025) ──
    eng_v25_oos = RSIStrategyV2ATREngine(atr_multiplier=2.5, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(oos_candles)
    m_v25_oos = MetricsCalculator.calculate(eng_v25_oos.closed_trades, eng_v25_oos.equity_curve, initial_capital=100000.0)

    eng_v26_oos = RSIStrategyV26Engine(min_atr_cost_ratio=5.0, atr_multiplier=2.5, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(oos_candles)
    m_v26_oos = MetricsCalculator.calculate(eng_v26_oos.closed_trades, eng_v26_oos.equity_curve, initial_capital=100000.0)

    # ── 4. Full 12-Year Combined (2014-2025) ──
    all_candles = candles_prior + candles_recent
    eng_v25_all = RSIStrategyV2ATREngine(atr_multiplier=2.5, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(all_candles)
    m_v25_all = MetricsCalculator.calculate(eng_v25_all.closed_trades, eng_v25_all.equity_curve, initial_capital=100000.0)

    eng_v26_all = RSIStrategyV26Engine(min_atr_cost_ratio=5.0, atr_multiplier=2.5, execution_config=real_config, initial_capital=100000.0, units_per_trade=50.0).run_backtest(all_candles)
    m_v26_all = MetricsCalculator.calculate(eng_v26_all.closed_trades, eng_v26_all.equity_curve, initial_capital=100000.0)

    # Export CSV
    ReportGenerator.export_trade_log_csv(eng_v26_all.closed_trades, f"{output_dir}/xauusd_12yr_v26_trades.csv")

    return {
        "m_v25_disc": m_v25_disc, "m_v26_disc_5": m_v26_disc_5, "m_v26_disc_6": m_v26_disc_6,
        "m_v25_val": m_v25_val, "m_v26_val": m_v26_val,
        "m_v25_oos": m_v25_oos, "m_v26_oos": m_v26_oos,
        "m_v25_all": m_v25_all, "m_v26_all": m_v26_all,
        "trades_v26_all": eng_v26_all.closed_trades
    }


if __name__ == "__main__":
    res = run_volatility_experiment()
    print("V2.6 Volatility Experiment Complete.")
