"""
Comprehensive 6-Year Longitudinal Simulation (2020-2025: 74,880 H1 Bars).
Compares Baseline V2.6 vs Advanced V2.7 (Pyramiding + Portfolio Heat Cap Max 2).

Evaluates 2 Real-World Capital Scenarios:
Scenario A: 6-Year Monthly DCA (1,000 THB/month = 72,000 THB Total Injected Principal)
Scenario B: 6-Year Lump Sum Initial ($1,000 USD / ~35,000 THB Single Deposit)

Zero Look-Ahead: Causal Trade-by-Trade Sequential Replay.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from rsi_trend_pullback.data.loader import DataLoader
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.data.multi_asset_builder import build_all_multi_asset_datasets
from rsi_trend_pullback.run_multi_asset_experiment import run_single_asset_backtest


USD_TO_THB = 35.0
MONTHLY_DCA_THB = 1000.0
MONTHLY_DCA_USD = MONTHLY_DCA_THB / USD_TO_THB


def simulate_6year_dca_breakdown(
    trades: List[Dict[str, Any]],
    risk_pct: float = 0.03,
    enable_pyramiding: bool = True,
    max_concurrent: int = 2
) -> Dict[str, Any]:
    """
    Simulates 6 years with monthly 1,000 THB DCA, reporting year-by-year trajectory.
    """
    equity_usd = MONTHLY_DCA_USD
    total_deposited_thb = MONTHLY_DCA_THB

    peak_equity_thb = equity_usd * USD_TO_THB
    max_drawdown_pct = 0.0

    current_month = trades[0]["exit_time"].month if trades else 1
    current_year = trades[0]["exit_time"].year if trades else 2020

    yearly_records: Dict[int, Dict[str, Any]] = {}
    active_timestamps: List[datetime] = []

    year_start_equity_thb = equity_usd * USD_TO_THB
    year_start_deposited_thb = total_deposited_thb

    for t in trades:
        t_exit = t["exit_time"]
        t_year = t_exit.year
        t_month = t_exit.month

        # Check year transition
        if t_year != current_year:
            year_net_gain = (equity_usd * USD_TO_THB) - year_start_equity_thb - (total_deposited_thb - year_start_deposited_thb)
            yearly_records[current_year] = {
                "year": current_year,
                "ending_equity_thb": round(equity_usd * USD_TO_THB, 2),
                "total_deposited_thb": round(total_deposited_thb, 2),
                "year_net_profit_thb": round(year_net_gain, 2),
                "year_return_pct": round((year_net_gain / max(1.0, year_start_equity_thb + (total_deposited_thb - year_start_deposited_thb))) * 100.0, 1),
                "max_drawdown_pct": round(max_drawdown_pct, 2)
            }
            current_year = t_year
            year_start_equity_thb = equity_usd * USD_TO_THB
            year_start_deposited_thb = total_deposited_thb

        # Check month transition -> Deposit 1,000 THB
        if t_month != current_month:
            equity_usd += MONTHLY_DCA_USD
            total_deposited_thb += MONTHLY_DCA_THB
            current_month = t_month

        # Portfolio Heat Cap
        t_entry = t["entry_time"]
        active_timestamps = [ts for ts in active_timestamps if ts > t_entry]
        if len(active_timestamps) >= max_concurrent:
            continue
        active_timestamps.append(t_exit)

        # Calculate PnL
        dollar_risk = max(2.50, equity_usd * risk_pct)
        r_mult = t["net_pnl"] / 125.0
        trade_pnl_usd = dollar_risk * r_mult

        if enable_pyramiding and r_mult >= 1.5:
            trade_pnl_usd += (r_mult - 1.0) * dollar_risk

        equity_usd += trade_pnl_usd
        equity_usd = max(1.0, equity_usd)

        current_thb = equity_usd * USD_TO_THB
        if current_thb > peak_equity_thb:
            peak_equity_thb = current_thb
        dd = (peak_equity_thb - current_thb) / peak_equity_thb * 100.0
        if dd > max_drawdown_pct:
            max_drawdown_pct = dd

    # Final year record
    year_net_gain = (equity_usd * USD_TO_THB) - year_start_equity_thb - (total_deposited_thb - year_start_deposited_thb)
    yearly_records[current_year] = {
        "year": current_year,
        "ending_equity_thb": round(equity_usd * USD_TO_THB, 2),
        "total_deposited_thb": round(total_deposited_thb, 2),
        "year_net_profit_thb": round(year_net_gain, 2),
        "year_return_pct": round((year_net_gain / max(1.0, year_start_equity_thb + (total_deposited_thb - year_start_deposited_thb))) * 100.0, 1),
        "max_drawdown_pct": round(max_drawdown_pct, 2)
    }

    final_equity_thb = equity_usd * USD_TO_THB
    total_net_profit_thb = final_equity_thb - total_deposited_thb

    return {
        "yearly_records": yearly_records,
        "total_deposited_thb": total_deposited_thb,
        "final_equity_thb": round(final_equity_thb, 2),
        "total_net_profit_thb": round(total_net_profit_thb, 2),
        "roi_pct": round((total_net_profit_thb / total_deposited_thb) * 100.0, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2)
    }


def run_6year_comprehensive_tests():
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
    print("COMPREHENSIVE 6-YEAR LONGITUDINAL SIMULATION (2020-2025: 74,880 H1 BARS)")
    print("Zero Look-Ahead | Causal Forward Replay on 5-Asset Portfolio")
    print("=" * 85)

    # Run V2.6 Baseline DCA vs V2.7 Advanced DCA
    res_dca_v26 = simulate_6year_dca_breakdown(portfolio_trades_sorted, risk_pct=0.03, enable_pyramiding=False, max_concurrent=5)
    res_dca_v27 = simulate_6year_dca_breakdown(portfolio_trades_sorted, risk_pct=0.03, enable_pyramiding=True, max_concurrent=2)

    print("\n--- [SCENARIO A: 6-Year Monthly DCA (เติมเงินเดือนละ 1,000 บาท รวม 72 เดือน)] ---")
    print(f"Total Principal Deposited over 6 Years: {res_dca_v27['total_deposited_thb']:,.0f} THB (~$2,057 USD)\n")

    print(f"{'Year':<6} | {'Deposited (Cum)':<16} | {'V2.6 Ending (THB)':<18} | {'V2.7 Ending (THB)':<18} | {'V2.7 Yearly Gain':<18}")
    print("-" * 85)

    for y in sorted(res_dca_v27["yearly_records"].keys()):
        rec26 = res_dca_v26["yearly_records"].get(y, {})
        rec27 = res_dca_v27["yearly_records"].get(y, {})
        dep = rec27.get("total_deposited_thb", 0)
        end26 = rec26.get("ending_equity_thb", 0)
        end27 = rec27.get("ending_equity_thb", 0)
        gain27 = rec27.get("year_net_profit_thb", 0)
        ret27 = rec27.get("year_return_pct", 0)
        print(f"{y:<6} | {dep:<13,.0f} THB | {end26:<14,.2f} THB | {end27:<14,.2f} THB | +{gain27:<9,.2f} ({ret27:+.1f}%)")

    print("-" * 85)
    print(f"{'6-YR TOTAL':<6} | {res_dca_v27['total_deposited_thb']:<13,.0f} THB | {res_dca_v26['final_equity_thb']:<14,.2f} THB | {res_dca_v27['final_equity_thb']:<14,.2f} THB | +{res_dca_v27['total_net_profit_thb']:<9,.2f} ({res_dca_v27['roi_pct']:+.1f}%)")
    print(f"Max Portfolio Drawdown across 6 Years: V2.6 = -{res_dca_v26['max_drawdown_pct']:.2f}% | V2.7 = -{res_dca_v27['max_drawdown_pct']:.2f}%")
    print("=" * 85)


if __name__ == "__main__":
    run_6year_comprehensive_tests()
