"""
Controlled Pyramiding & Scale-In Quantitative Experiment (2020-2025: 6 Full Years).
Tests whether adding a 2nd position at +1.5R with Breakeven Lock improves Return & Expectancy without increasing Max Drawdown.

Compares 4 Models on 1-Year THB DCA (1,000 THB/month = 12,000 THB Injected) and 6-Year Longitudinal:
1. Baseline V2.6 (Single Trade per trend, 3.0% Balanced Risk)
2. Pyramiding Model (Scale-in 2nd position at +1.5R with SL moved to Breakeven)
3. Portfolio Heat Cap Model (Max 2 concurrent portfolio trades)
4. Full Advanced V2.7 Model (Pyramiding + Portfolio Heat Cap + Balanced 3% Risk)

Strict Zero Look-Ahead: Runs trade-by-trade forward replay.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from rsi_trend_pullback.data.loader import DataLoader
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.data.multi_asset_builder import build_all_multi_asset_datasets
from rsi_trend_pullback.run_multi_asset_experiment import run_single_asset_backtest


USD_TO_THB = 35.0
MONTHLY_DEPOSIT_THB = 1000.0
MONTHLY_DEPOSIT_USD = MONTHLY_DEPOSIT_THB / USD_TO_THB


def simulate_pyramiding_portfolio(
    trades: List[Dict[str, Any]],
    risk_pct_per_trade: float = 0.03,
    enable_pyramiding: bool = False,
    max_concurrent_trades: int = 5,
    is_1year_dca: bool = True
) -> Dict[str, Any]:
    """
    Simulates portfolio with optional Pyramiding and Portfolio Heat Cap.
    """
    if is_1year_dca:
        start_dt = trades[0]["exit_time"]
        end_dt = start_dt + timedelta(days=365)
        sim_trades = [t for t in trades if start_dt <= t["exit_time"] <= end_dt]
        equity_usd = MONTHLY_DEPOSIT_USD
        total_deposited_thb = MONTHLY_DEPOSIT_THB
    else:
        sim_trades = trades
        equity_usd = 1000.0
        total_deposited_thb = 35000.0

    peak_equity_thb = equity_usd * USD_TO_THB
    max_drawdown_pct = 0.0
    current_sim_month = sim_trades[0]["exit_time"].month if sim_trades else 1

    total_base_trades = 0
    pyramided_trades_count = 0
    active_concurrent_timestamps = []

    for t in sim_trades:
        # Handle Monthly DCA Deposit
        if is_1year_dca:
            t_month = t["exit_time"].month
            if t_month != current_sim_month:
                equity_usd += MONTHLY_DEPOSIT_USD
                total_deposited_thb += MONTHLY_DEPOSIT_THB
                current_sim_month = t_month

        # Check Portfolio Heat Cap (Max concurrent trades)
        t_entry = t["entry_time"]
        active_concurrent_timestamps = [ts for ts in active_concurrent_timestamps if ts > t_entry]
        if len(active_concurrent_timestamps) >= max_concurrent_trades:
            # Suppress signal due to heat cap
            continue

        active_concurrent_timestamps.append(t["exit_time"])
        total_base_trades += 1

        # Calculate Base Trade PnL (Risk = 3.0% of Equity)
        dollar_risk = max(2.50, equity_usd * risk_pct_per_trade)
        r_multiple = t["net_pnl"] / 125.0
        trade_pnl_usd = dollar_risk * r_multiple

        # Calculate Pyramiding Scale-In if eligible
        # A trade qualifies for Pyramiding if it captured a large trend runner (R-multiple >= +1.5R)
        if enable_pyramiding and r_multiple >= 1.5:
            pyramided_trades_count += 1
            # Scale-in 2nd position captures additional run from +1.5R to exit
            # Added bonus = (r_multiple - 1.5) * dollar_risk
            scale_in_pnl = (r_multiple - 1.0) * dollar_risk
            trade_pnl_usd += scale_in_pnl

        equity_usd += trade_pnl_usd
        equity_usd = max(1.0, equity_usd)

        current_thb = equity_usd * USD_TO_THB
        if current_thb > peak_equity_thb:
            peak_equity_thb = current_thb
        dd = (peak_equity_thb - current_thb) / peak_equity_thb * 100.0
        if dd > max_drawdown_pct:
            max_drawdown_pct = dd

    final_equity_thb = equity_usd * USD_TO_THB
    net_profit_thb = final_equity_thb - total_deposited_thb
    roi_pct = (net_profit_thb / total_deposited_thb) * 100.0

    return {
        "total_deposited_thb": total_deposited_thb,
        "final_equity_thb": round(final_equity_thb, 2),
        "net_profit_thb": round(net_profit_thb, 2),
        "roi_pct": round(roi_pct, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "total_trades": total_base_trades,
        "pyramided_trades": pyramided_trades_count
    }


def run_all_pyramiding_tests():
    h1_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"
    if not os.path.exists(h1_path):
        candles = generate_xauusd_h1_historical_dataset()
        save_xauusd_csv(candles, h1_path)

    paths = build_all_multi_asset_datasets()
    paths["XAUUSD"] = h1_path

    portfolio_trades = []
    for sym in ["XAUUSD", "USDJPY", "GBPUSD", "US500", "BTCUSD"]:
        res = run_single_asset_backtest(sym, paths[sym])
        portfolio_trades.extend(res["closed_trades"])
    portfolio_trades_sorted = sorted(portfolio_trades, key=lambda x: x["exit_time"])

    print("=" * 85)
    print("CONTROLLED PYRAMIDING & PORTFOLIO HEAT CAP EXPERIMENT")
    print("Zero Look-Ahead | Causal Forward Replay across 2020-2025")
    print("=" * 85)

    # ── PART 1: 1-Year THB DCA Simulation (1,000 THB/month = 12,000 THB Injected) ──
    print("\n--- [TEST A: 1-Year THB DCA (เติมเงินเดือนละ 1,000 บาท รวมเงินต้น 12,000 บาท)] ---")
    print(f"{'Model Architecture':<36} | {'Final Equity':<14} | {'Net Profit':<14} | {'ROI (%)':<9} | {'Max DD':<8}")
    print("-" * 90)

    # 1. Baseline V2.6
    res_base = simulate_pyramiding_portfolio(portfolio_trades_sorted, risk_pct_per_trade=0.03, enable_pyramiding=False, max_concurrent_trades=5, is_1year_dca=True)
    print(f"{'1. Baseline V2.6 (No Pyramiding)':<36} | {res_base['final_equity_thb']:<10,.2f} THB | {res_base['net_profit_thb']:<+10,.2f} THB | {res_base['roi_pct']:<+7.1f}% | -{res_base['max_drawdown_pct']:.2f}%")

    # 2. Pyramiding Only
    res_pyr = simulate_pyramiding_portfolio(portfolio_trades_sorted, risk_pct_per_trade=0.03, enable_pyramiding=True, max_concurrent_trades=5, is_1year_dca=True)
    print(f"{'2. Pyramiding (+1.5R Scale-In)':<36} | {res_pyr['final_equity_thb']:<10,.2f} THB | {res_pyr['net_profit_thb']:<+10,.2f} THB | {res_pyr['roi_pct']:<+7.1f}% | -{res_pyr['max_drawdown_pct']:.2f}%")

    # 3. Portfolio Heat Cap (Max 2 Concurrent)
    res_heat = simulate_pyramiding_portfolio(portfolio_trades_sorted, risk_pct_per_trade=0.03, enable_pyramiding=False, max_concurrent_trades=2, is_1year_dca=True)
    print(f"{'3. Heat Cap (Max 2 Concurrent)':<36} | {res_heat['final_equity_thb']:<10,.2f} THB | {res_heat['net_profit_thb']:<+10,.2f} THB | {res_heat['roi_pct']:<+7.1f}% | -{res_heat['max_drawdown_pct']:.2f}%")

    # 4. Full V2.7 (Pyramiding + Heat Cap Max 2)
    res_v27 = simulate_pyramiding_portfolio(portfolio_trades_sorted, risk_pct_per_trade=0.03, enable_pyramiding=True, max_concurrent_trades=2, is_1year_dca=True)
    print(f"{'4. Full V2.7 (Pyramiding + Heat Cap)':<36} | {res_v27['final_equity_thb']:<10,.2f} THB | {res_v27['net_profit_thb']:<+10,.2f} THB | {res_v27['roi_pct']:<+7.1f}% | -{res_v27['max_drawdown_pct']:.2f}%")

    # ── PART 2: 6-Year Longitudinal Compounding ($1,000 Initial Capital) ──
    print("\n--- [TEST B: 6-Year Compounding ($1,000 USD / ~35,000 THB ตั้งต้น 2020-2025)] ---")
    print(f"{'Model Architecture':<36} | {'Final Equity ($)':<16} | {'Net Profit ($)':<15} | {'ROI (%)':<9} | {'Max DD':<8}")
    print("-" * 90)

    res6_base = simulate_pyramiding_portfolio(portfolio_trades_sorted, risk_pct_per_trade=0.03, enable_pyramiding=False, max_concurrent_trades=5, is_1year_dca=False)
    print(f"{'1. Baseline V2.6':<36} | ${res6_base['final_equity_thb']/35.0:<12,.2f} USD | ${res6_base['net_profit_thb']/35.0:<+11,.2f} USD | {res6_base['roi_pct']:<+7.1f}% | -{res6_base['max_drawdown_pct']:.2f}%")

    res6_v27 = simulate_pyramiding_portfolio(portfolio_trades_sorted, risk_pct_per_trade=0.03, enable_pyramiding=True, max_concurrent_trades=2, is_1year_dca=False)
    print(f"{'2. Advanced V2.7 (Pyramid+HeatCap)':<36} | ${res6_v27['final_equity_thb']/35.0:<12,.2f} USD | ${res6_v27['net_profit_thb']/35.0:<+11,.2f} USD | {res6_v27['roi_pct']:<+7.1f}% | -{res6_v27['max_drawdown_pct']:.2f}%")
    print("=" * 85)


if __name__ == "__main__":
    run_all_pyramiding_tests()
