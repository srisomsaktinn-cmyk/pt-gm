"""
Exact 1-Year THB Monthly DCA (1,000 THB/month) Simulation for Strategy V2.6.
Enforces realistic micro-lot broker physics on XM / MT5:
- Injected Capital: 1,000 THB at the start of every month (12,000 THB total principal over 12 months)
- Exchange rate: 35.0 THB / USD (1,000 THB = $28.57 USD / month)
- Minimum broker order size: 0.01 lot
- Tests 4 Risk Models: Fixed 0.01 Lot, 1.5% Risk, 3.0% Risk, 5.0% Risk per trade
- No look-ahead: Walks forward trade-by-trade across historical test slices (2020-2025)
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
MONTHLY_DEPOSIT_USD = MONTHLY_DEPOSIT_THB / USD_TO_THB # $28.57


def simulate_1year_thb_dca(
    trades: List[Dict[str, Any]],
    risk_pct_per_trade: float,
    is_fixed_lot: bool = False
) -> Dict[str, Any]:
    """
    Simulates 12 months of trading with 1,000 THB deposit on day 1 of each month.
    Respects minimum 0.01 lot floor.
    """
    equity_usd = MONTHLY_DEPOSIT_USD
    total_deposited_thb = MONTHLY_DEPOSIT_THB
    total_deposited_usd = MONTHLY_DEPOSIT_USD

    peak_equity_thb = equity_usd * USD_TO_THB
    max_drawdown_pct = 0.0

    current_month_idx = 0
    trade_count = 0
    win_count = 0
    loss_count = 0

    # Filter to exact 1-year trade slice (12 months = approx 160 multi-asset trades)
    # Using 1-year rolling slice
    start_dt = trades[0]["exit_time"]
    end_dt = start_dt + timedelta(days=365)
    year_trades = [t for t in trades if start_dt <= t["exit_time"] <= end_dt]

    current_sim_month = start_dt.month

    for t in year_trades:
        # Check if new month arrived -> Deposit 1,000 THB
        t_month = t["exit_time"].month
        if t_month != current_sim_month:
            equity_usd += MONTHLY_DEPOSIT_USD
            total_deposited_thb += MONTHLY_DEPOSIT_THB
            total_deposited_usd += MONTHLY_DEPOSIT_USD
            current_sim_month = t_month

        trade_count += 1
        is_win = t["net_pnl"] > 0
        if is_win: win_count += 1
        else: loss_count += 1

        if is_fixed_lot:
            # 0.01 lot fixed PnL (1/50th of 0.5 lot backtest trade)
            trade_pnl_usd = t["net_pnl"] / 50.0
        else:
            # Dynamic Risk with 0.01 lot minimum floor
            # R-Multiple = net_pnl / 125.0
            r_mult = t["net_pnl"] / 125.0
            target_dollar_risk = equity_usd * risk_pct_per_trade
            # Minimum 0.01 lot floor risk (approx $2.50 USD on 0.01 lot)
            min_floor_risk = 2.50
            actual_dollar_risk = max(min_floor_risk, target_dollar_risk)
            trade_pnl_usd = actual_dollar_risk * r_mult

        equity_usd += trade_pnl_usd
        equity_usd = max(1.0, equity_usd) # Protection floor

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
        "total_trades": trade_count,
        "win_rate": round(win_count / trade_count * 100.0, 1) if trade_count > 0 else 0.0
    }


def run_all_thb_simulations():
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

    print("=" * 80)
    print("1-YEAR THB REALISTIC DCA SIMULATION (1,000 THB / Month = 12,000 THB Injected)")
    print("Enforcing Realistic 0.01 Micro-Lot Broker Floor (No Cheating / No Future Peeking)")
    print("=" * 80)
    print(f"{'Risk Model':<28} | {'Principal':<11} | {'Final Equity':<14} | {'Net Profit':<14} | {'ROI (%)':<9} | {'Max DD':<8}")
    print("-" * 90)

    # 1. Fixed 0.01 Lot
    res_fix = simulate_1year_thb_dca(portfolio_trades_sorted, risk_pct_per_trade=0.0, is_fixed_lot=True)
    print(f"{'1. Fixed 0.01 Lot Constant':<28} | {res_fix['total_deposited_thb']:,.0f} THB | {res_fix['final_equity_thb']:<10,.2f} THB | {res_fix['net_profit_thb']:<+10,.2f} THB | {res_fix['roi_pct']:<+7.1f}% | -{res_fix['max_drawdown_pct']:.2f}%")

    # 2. Risk 1.5%
    res_15 = simulate_1year_thb_dca(portfolio_trades_sorted, risk_pct_per_trade=0.015)
    print(f"{'2. Dynamic Risk 1.5% / trade':<28} | {res_15['total_deposited_thb']:,.0f} THB | {res_15['final_equity_thb']:<10,.2f} THB | {res_15['net_profit_thb']:<+10,.2f} THB | {res_15['roi_pct']:<+7.1f}% | -{res_15['max_drawdown_pct']:.2f}%")

    # 3. Risk 3.0%
    res_30 = simulate_1year_thb_dca(portfolio_trades_sorted, risk_pct_per_trade=0.030)
    print(f"{'3. Dynamic Risk 3.0% / trade':<28} | {res_30['total_deposited_thb']:,.0f} THB | {res_30['final_equity_thb']:<10,.2f} THB | {res_30['net_profit_thb']:<+10,.2f} THB | {res_30['roi_pct']:<+7.1f}% | -{res_30['max_drawdown_pct']:.2f}%")

    # 4. Risk 5.0%
    res_50 = simulate_1year_thb_dca(portfolio_trades_sorted, risk_pct_per_trade=0.050)
    print(f"{'4. Dynamic Risk 5.0% / trade':<28} | {res_50['total_deposited_thb']:,.0f} THB | {res_50['final_equity_thb']:<10,.2f} THB | {res_50['net_profit_thb']:<+10,.2f} THB | {res_50['roi_pct']:<+7.1f}% | -{res_50['max_drawdown_pct']:.2f}%")
    print("=" * 80)


if __name__ == "__main__":
    run_all_thb_simulations()
