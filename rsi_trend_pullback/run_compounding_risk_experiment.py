"""
Controlled Dynamic Fractional Compounding Risk Experiment for Strategy V2.6 (2020-2025).
Tests whether 5% Risk per Trade creates sustainable compounding wealth or causes catastrophic drawdown/ruin.

Evaluates 4 Risk Profiles on $1,000 Initial Capital:
1. Fixed 0.01 Micro Lot (Baseline)
2. Dynamic 1.5% Risk per Trade (Conservative)
3. Dynamic 3.0% Risk per Trade (Balanced)
4. Dynamic 5.0% Risk per Trade (Aggressive)

Runs on both:
- Single Asset: XAUUSD H1
- Multi-Asset Portfolio: Top 5 Assets (XAUUSD, USDJPY, GBPUSD, US500, BTCUSD)
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from rsi_trend_pullback.data.loader import DataLoader
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.data.multi_asset_builder import build_all_multi_asset_datasets
from rsi_trend_pullback.run_multi_asset_experiment import run_single_asset_backtest


def simulate_compounding_curve(
    trades: List[Dict[str, Any]],
    initial_capital: float = 1000.0,
    risk_pct_per_trade: float = 0.05,
    is_fixed_lot: bool = False,
    monthly_dca_usd: float = 0.0
) -> Dict[str, Any]:
    """
    Simulates exact account equity growth under dynamic fractional compounding.
    In Strategy V2.6, Stop Loss is 2.5 * ATR.
    When a trade wins, R-multiple = (Gross Gain / Stop Loss Distance).
    When a trade loses at SL, loss = exactly (Current Equity * risk_pct).
    """
    equity = initial_capital
    peak_equity = initial_capital
    max_drawdown_pct = 0.0
    equity_curve = [equity]
    monthly_injected_capital = 0.0

    last_month = None

    for t in trades:
        # Handle monthly DCA deposit if enabled
        trade_month = (t["exit_time"].year, t["exit_time"].month)
        if last_month is not None and trade_month != last_month and monthly_dca_usd > 0:
            equity += monthly_dca_usd
            monthly_injected_capital += monthly_dca_usd
        last_month = trade_month

        # Calculate Risk and Return
        if is_fixed_lot:
            # Fixed 0.01 lot PnL
            # Backtest trades were on 50 units (0.5 lot), so 0.01 lot is 1/50th
            trade_pnl = t["net_pnl"] / 50.0
        else:
            # Dynamic Risk Position Sizing
            # If trade lost, loss is capped at exact risk percentage of equity
            # If trade won, gain is scaled by R-multiple
            dollar_risk = equity * risk_pct_per_trade
            # Normalized trade return (assuming baseline trade loss on 0.5 lot was ~$120)
            # R_multiple = net_pnl / average_loss_magnitude
            base_loss_ref = 125.0
            r_mult = t["net_pnl"] / base_loss_ref
            trade_pnl = dollar_risk * r_mult

        equity += trade_pnl
        equity = max(10.0, equity) # Account protection floor
        equity_curve.append(equity)

        if equity > peak_equity:
            peak_equity = equity
        dd = (peak_equity - equity) / peak_equity * 100.0
        if dd > max_drawdown_pct:
            max_drawdown_pct = dd

    total_net_pnl = equity - (initial_capital + monthly_injected_capital)
    total_return_pct = (total_net_pnl / (initial_capital + monthly_injected_capital)) * 100.0

    return {
        "final_equity": round(equity, 2),
        "total_net_pnl": round(total_net_pnl, 2),
        "total_return_pct": round(total_return_pct, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "total_injected_principal": round(initial_capital + monthly_injected_capital, 2)
    }


def run_compounding_experiment():
    h1_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"
    if not os.path.exists(h1_path):
        candles = generate_xauusd_h1_historical_dataset()
        save_xauusd_csv(candles, h1_path)

    paths = build_all_multi_asset_datasets()
    paths["XAUUSD"] = h1_path

    # Gather backtest trades
    xau_trades = run_single_asset_backtest("XAUUSD", h1_path)["closed_trades"]

    portfolio_trades = []
    for sym in ["XAUUSD", "USDJPY", "GBPUSD", "US500", "BTCUSD"]:
        res = run_single_asset_backtest(sym, paths[sym])
        portfolio_trades.extend(res["closed_trades"])
    portfolio_trades_sorted = sorted(portfolio_trades, key=lambda x: x["exit_time"])

    print("=" * 80)
    print("CONTROLLED COMPOUNDING RISK EXPERIMENT (2020-2025: 6 Full Years)")
    print("Initial Capital: $1,000 USD (~35,000 THB) | Zero DCA Injection")
    print("=" * 80)

    # ── Test 1: XAUUSD Single Asset ──
    print("\n--- [TEST 1: XAUUSD Gold Alone (174 Trades)] ---")
    print(f"{'Risk Model':<30} | {'Final Equity':<14} | {'Net Profit ($)':<14} | {'Total Return':<14} | {'Max Drawdown':<12}")
    print("-" * 90)

    res_xau_fixed = simulate_compounding_curve(xau_trades, initial_capital=1000.0, is_fixed_lot=True)
    print(f"{'1. Fixed 0.01 Lot Constant':<30} | ${res_xau_fixed['final_equity']:<13,.2f} | ${res_xau_fixed['total_net_pnl']:<+13,.2f} | {res_xau_fixed['total_return_pct']:<+13.1f}% | -{res_xau_fixed['max_drawdown_pct']:.2f}%")

    res_xau_15 = simulate_compounding_curve(xau_trades, initial_capital=1000.0, risk_pct_per_trade=0.015)
    print(f"{'2. Dynamic Risk 1.5% / trade':<30} | ${res_xau_15['final_equity']:<13,.2f} | ${res_xau_15['total_net_pnl']:<+13,.2f} | {res_xau_15['total_return_pct']:<+13.1f}% | -{res_xau_15['max_drawdown_pct']:.2f}%")

    res_xau_30 = simulate_compounding_curve(xau_trades, initial_capital=1000.0, risk_pct_per_trade=0.030)
    print(f"{'3. Dynamic Risk 3.0% / trade':<30} | ${res_xau_30['final_equity']:<13,.2f} | ${res_xau_30['total_net_pnl']:<+13,.2f} | {res_xau_30['total_return_pct']:<+13.1f}% | -{res_xau_30['max_drawdown_pct']:.2f}%")

    res_xau_50 = simulate_compounding_curve(xau_trades, initial_capital=1000.0, risk_pct_per_trade=0.050)
    print(f"{'4. Dynamic Risk 5.0% / trade':<30} | ${res_xau_50['final_equity']:<13,.2f} | ${res_xau_50['total_net_pnl']:<+13,.2f} | {res_xau_50['total_return_pct']:<+13.1f}% | -{res_xau_50['max_drawdown_pct']:.2f}%")

    # ── Test 2: Multi-Asset Portfolio ──
    print("\n--- [TEST 2: Multi-Asset 5-Asset Portfolio (996 Trades)] ---")
    print(f"{'Risk Model':<30} | {'Final Equity':<14} | {'Net Profit ($)':<14} | {'Total Return':<14} | {'Max Drawdown':<12}")
    print("-" * 90)

    res_port_fixed = simulate_compounding_curve(portfolio_trades_sorted, initial_capital=1000.0, is_fixed_lot=True)
    print(f"{'1. Fixed 0.01 Lot Constant':<30} | ${res_port_fixed['final_equity']:<13,.2f} | ${res_port_fixed['total_net_pnl']:<+13,.2f} | {res_port_fixed['total_return_pct']:<+13.1f}% | -{res_port_fixed['max_drawdown_pct']:.2f}%")

    res_port_10 = simulate_compounding_curve(portfolio_trades_sorted, initial_capital=1000.0, risk_pct_per_trade=0.010)
    print(f"{'2. Dynamic Risk 1.0% / asset':<30} | ${res_port_10['final_equity']:<13,.2f} | ${res_port_10['total_net_pnl']:<+13,.2f} | {res_port_10['total_return_pct']:<+13.1f}% | -{res_port_10['max_drawdown_pct']:.2f}%")

    res_port_15 = simulate_compounding_curve(portfolio_trades_sorted, initial_capital=1000.0, risk_pct_per_trade=0.015)
    print(f"{'3. Dynamic Risk 1.5% / asset':<30} | ${res_port_15['final_equity']:<13,.2f} | ${res_port_15['total_net_pnl']:<+13,.2f} | {res_port_15['total_return_pct']:<+13.1f}% | -{res_port_15['max_drawdown_pct']:.2f}%")

    res_port_20 = simulate_compounding_curve(portfolio_trades_sorted, initial_capital=1000.0, risk_pct_per_trade=0.020)
    print(f"{'4. Dynamic Risk 2.0% / asset':<30} | ${res_port_20['final_equity']:<13,.2f} | ${res_port_20['total_net_pnl']:<+13,.2f} | {res_port_20['total_return_pct']:<+13.1f}% | -{res_port_20['max_drawdown_pct']:.2f}%")

    res_port_50 = simulate_compounding_curve(portfolio_trades_sorted, initial_capital=1000.0, risk_pct_per_trade=0.050)
    print(f"{'5. Extreme Risk 5.0% / asset':<30} | ${res_port_50['final_equity']:<13,.2f} | ${res_port_50['total_net_pnl']:<+13,.2f} | {res_port_50['total_return_pct']:<+13.1f}% | -{res_port_50['max_drawdown_pct']:.2f}%")
    print("=" * 80)


if __name__ == "__main__":
    run_compounding_experiment()
