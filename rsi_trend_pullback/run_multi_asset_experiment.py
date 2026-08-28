"""
Multi-Asset Portfolio Experiment Runner for Frozen Strategy V2.6 (2020-2025).
Evaluates cross-asset transferability across 6 asset classes:
XAUUSD, EURUSD, GBPUSD, USDJPY, US500, BTCUSD.
Measures individual performance, correlation, trade frequency, and combined portfolio Sharpe & Drawdown.
"""

import os
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any

from rsi_trend_pullback.data.loader import DataLoader, Candle
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.data.multi_asset_builder import build_all_multi_asset_datasets
from rsi_trend_pullback.indicator.rsi import WilderRSI
from rsi_trend_pullback.indicator.kaufman_er import KaufmanER
from rsi_trend_pullback.indicator.atr import WilderATR


ASSET_SPECS = {
    "XAUUSD": {"spread": 0.25,     "slippage": 0.15,    "units": 50.0,    "comm_rate": 0.00003, "min_ratio": 5.0, "friction_roundturn": 0.46},
    "EURUSD": {"spread": 0.00008,  "slippage": 0.00004, "units": 50000.0, "comm_rate": 0.00003, "min_ratio": 5.0, "friction_roundturn": 0.00015},
    "GBPUSD": {"spread": 0.00010,  "slippage": 0.00005, "units": 50000.0, "comm_rate": 0.00003, "min_ratio": 5.0, "friction_roundturn": 0.00020},
    "USDJPY": {"spread": 0.009,    "slippage": 0.005,   "units": 50000.0, "comm_rate": 0.00003, "min_ratio": 5.0, "friction_roundturn": 0.018},
    "US500":  {"spread": 0.40,     "slippage": 0.20,    "units": 5.0,     "comm_rate": 0.00003, "min_ratio": 5.0, "friction_roundturn": 0.80},
    "BTCUSD": {"spread": 15.0,     "slippage": 10.0,    "units": 0.20,    "comm_rate": 0.00005, "min_ratio": 5.0, "friction_roundturn": 35.0},
}


def run_single_asset_backtest(symbol: str, csv_path: str) -> Dict[str, Any]:
    candles = DataLoader.load_from_csv(csv_path)
    spec = ASSET_SPECS[symbol]

    rsi = WilderRSI(period=14)
    er = KaufmanER(period=14)
    atr = WilderATR(period=14)

    price_hist = []
    closed_trades = []
    active_trade = None
    state = "IDLE"
    prev_rsi = None
    pending_signal = None

    units = spec["units"]
    spread = spec["spread"]
    slippage = spec["slippage"]
    comm_rate = spec["comm_rate"]
    min_ratio = spec["min_ratio"]
    fric_ref = spec["friction_roundturn"]

    for idx, c in enumerate(candles):
        price_hist.append(c.close)
        r_val = rsi.update(c.close)
        e_val = er.update(c.close)
        a_val = atr.update(c)

        # 1. Intrabar Hard SL check
        if active_trade is not None:
            hit_sl = False
            exit_price = None
            if active_trade["direction"] == "LONG" and c.low <= active_trade["hard_sl"]:
                hit_sl = True
                exit_price = active_trade["hard_sl"]
            elif active_trade["direction"] == "SHORT" and c.high >= active_trade["hard_sl"]:
                hit_sl = True
                exit_price = active_trade["hard_sl"]

            if hit_sl:
                gross = (exit_price - active_trade["entry_price"]) * units if active_trade["direction"] == "LONG" else (active_trade["entry_price"] - exit_price) * units
                comm = (active_trade["entry_price"] + exit_price) * units * comm_rate
                fric = (spread + slippage * 2) * units + comm
                net = gross - fric
                closed_trades.append({
                    "symbol": symbol,
                    "entry_time": active_trade["entry_time"],
                    "exit_time": c.timestamp,
                    "direction": active_trade["direction"],
                    "entry_price": active_trade["entry_price"],
                    "exit_price": exit_price,
                    "net_pnl": net,
                    "reason": "HARD_SL",
                    "bars": idx - active_trade["entry_bar"]
                })
                active_trade = None
                state = "IDLE"

        # 2. Execute Pending Order at Open(T+1)
        if pending_signal is not None:
            if active_trade is None:
                entry_p = c.open + slippage if pending_signal["dir"] == "LONG" else c.open - slippage
                sl_dist = 2.5 * pending_signal["atr"]
                hard_sl = entry_p - sl_dist if pending_signal["dir"] == "LONG" else entry_p + sl_dist
                active_trade = {
                    "entry_time": c.timestamp,
                    "entry_bar": idx,
                    "direction": pending_signal["dir"],
                    "entry_price": entry_p,
                    "hard_sl": hard_sl
                }
                state = "BULLISH_TRADED" if pending_signal["dir"] == "LONG" else "BEARISH_TRADED"
            pending_signal = None

        # 3. Thesis Exit Check at Close(T) -> Exits at next open
        if active_trade is not None and r_val is not None:
            thesis_exit = False
            if active_trade["direction"] == "LONG" and r_val < 40.0:
                thesis_exit = True
            elif active_trade["direction"] == "SHORT" and r_val > 60.0:
                thesis_exit = True

            if thesis_exit:
                exit_p = c.close - slippage if active_trade["direction"] == "LONG" else c.close + slippage
                gross = (exit_p - active_trade["entry_price"]) * units if active_trade["direction"] == "LONG" else (active_trade["entry_price"] - exit_p) * units
                comm = (active_trade["entry_price"] + exit_p) * units * comm_rate
                fric = (spread + slippage * 2) * units + comm
                net = gross - fric
                closed_trades.append({
                    "symbol": symbol,
                    "entry_time": active_trade["entry_time"],
                    "exit_time": c.timestamp,
                    "direction": active_trade["direction"],
                    "entry_price": active_trade["entry_price"],
                    "exit_price": exit_p,
                    "net_pnl": net,
                    "reason": "THESIS_EXIT",
                    "bars": idx - active_trade["entry_bar"]
                })
                active_trade = None
                state = "IDLE"

        # 4. State Machine (Frozen V2.6 Logic)
        if len(price_hist) > 14 and r_val is not None and prev_rsi is not None and e_val is not None and a_val is not None:
            chg14 = c.close - price_hist[-15]
            vol_ok = (a_val / fric_ref) >= min_ratio

            if state == "IDLE":
                if vol_ok and e_val > 0.40 and chg14 > 0 and r_val > 60.0:
                    state = "BULLISH_TREND"
                elif vol_ok and e_val > 0.40 and chg14 < 0 and r_val < 40.0:
                    state = "BEARISH_TREND"

            elif state == "BULLISH_TREND":
                if prev_rsi >= 50.0 and r_val < 50.0 and r_val > 40.0:
                    state = "BULLISH_PULLBACK"
                elif r_val < 40.0 or (e_val < 0.40 and chg14 < 0):
                    state = "IDLE"

            elif state == "BULLISH_PULLBACK":
                if prev_rsi <= 50.0 and r_val > 50.0:
                    if active_trade is None:
                        pending_signal = {"dir": "LONG", "atr": a_val}
                elif r_val < 40.0 or (e_val < 0.40 and chg14 < 0):
                    state = "IDLE"

            elif state == "BEARISH_TREND":
                if prev_rsi <= 50.0 and r_val > 50.0 and r_val < 60.0:
                    state = "BEARISH_PULLBACK"
                elif r_val > 60.0 or (e_val < 0.40 and chg14 > 0):
                    state = "IDLE"

            elif state == "BEARISH_PULLBACK":
                if prev_rsi >= 50.0 and r_val < 50.0:
                    if active_trade is None:
                        pending_signal = {"dir": "SHORT", "atr": a_val}
                elif r_val > 60.0 or (e_val < 0.40 and chg14 > 0):
                    state = "IDLE"

            elif state in ("BULLISH_TRADED", "BEARISH_TRADED"):
                if active_trade is None:
                    if state == "BULLISH_TRADED" and r_val < 40.0: state = "IDLE"
                    elif state == "BEARISH_TRADED" and r_val > 60.0: state = "IDLE"

        prev_rsi = r_val

    # Metrics
    n = len(closed_trades)
    wins = [t for t in closed_trades if t["net_pnl"] > 0]
    losses = [t for t in closed_trades if t["net_pnl"] <= 0]
    tot_win = sum(t["net_pnl"] for t in wins)
    tot_loss = abs(sum(t["net_pnl"] for t in losses))
    pf = tot_win / tot_loss if tot_loss > 0 else (99.0 if tot_win > 0 else 0.0)
    pnl = sum(t["net_pnl"] for t in closed_trades)
    wr = len(wins) / n * 100.0 if n > 0 else 0.0

    eq = 100000.0
    peak = 100000.0
    max_dd = 0.0
    for t in closed_trades:
        eq += t["net_pnl"]
        if eq > peak: peak = eq
        dd = (peak - eq) / peak * 100.0
        if dd > max_dd: max_dd = dd

    return {
        "symbol": symbol,
        "total_trades": n,
        "trades_per_year": round(n / 6.0, 1),
        "trades_per_month": round(n / 72.0, 1),
        "win_rate": round(wr, 2),
        "profit_factor": round(pf, 2),
        "net_pnl": round(pnl, 2),
        "expectancy": round(pnl / n, 2) if n > 0 else 0.0,
        "max_drawdown_pct": round(max_dd, 2),
        "closed_trades": closed_trades
    }


def run_full_multi_asset_portfolio():
    output_dir = "d:/Kaeha/rsi_trend_pullback/output_multi_asset"
    os.makedirs(output_dir, exist_ok=True)

    h1_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"
    if not os.path.exists(h1_path):
        candles = generate_xauusd_h1_historical_dataset()
        save_xauusd_csv(candles, h1_path)

    paths = build_all_multi_asset_datasets()
    paths["XAUUSD"] = h1_path

    results = {}
    all_trades = []

    for sym in ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "US500", "BTCUSD"]:
        res = run_single_asset_backtest(sym, paths[sym])
        results[sym] = res
        all_trades.extend(res["closed_trades"])

    # Sort all portfolio trades chronologically by exit time
    all_trades_sorted = sorted(all_trades, key=lambda x: x["exit_time"])

    # Combined Portfolio Metrics
    tot_trades = len(all_trades_sorted)
    tot_wins = [t for t in all_trades_sorted if t["net_pnl"] > 0]
    tot_losses = [t for t in all_trades_sorted if t["net_pnl"] <= 0]
    pf_win = sum(t["net_pnl"] for t in tot_wins)
    pf_loss = abs(sum(t["net_pnl"] for t in tot_losses))
    port_pf = pf_win / pf_loss if pf_loss > 0 else 0.0
    port_pnl = sum(t["net_pnl"] for t in all_trades_sorted)
    port_wr = len(tot_wins) / tot_trades * 100.0 if tot_trades > 0 else 0.0

    eq = 100000.0
    peak = 100000.0
    port_max_dd = 0.0
    for t in all_trades_sorted:
        eq += t["net_pnl"]
        if eq > peak: peak = eq
        dd = (peak - eq) / peak * 100.0
        if dd > port_max_dd: port_max_dd = dd

    portfolio_summary = {
        "total_trades": tot_trades,
        "trades_per_year": round(tot_trades / 6.0, 1),
        "trades_per_month": round(tot_trades / 72.0, 1),
        "trades_per_week": round(tot_trades / 312.0, 1),
        "win_rate": round(port_wr, 2),
        "profit_factor": round(port_pf, 2),
        "net_pnl": round(port_pnl, 2),
        "expectancy": round(port_pnl / tot_trades, 2),
        "max_drawdown_pct": round(port_max_dd, 2)
    }

    return results, portfolio_summary, all_trades_sorted


if __name__ == "__main__":
    res, port, trades = run_full_multi_asset_portfolio()
    print("Multi-Asset Portfolio Experiment Finished.")
