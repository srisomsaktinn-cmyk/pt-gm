"""
Part-Time Schedule Viability Experiment for Frozen Strategy V2.6 (XAUUSD H1).
Tests whether running Strategy V2.6 strictly during user availability hours:
- Mon-Fri 09:00-16:00 and 17:00-22:00 (Asia/Bangkok UTC+7)
maintains economic edge, profitability, and acceptable drawdown.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from rsi_trend_pullback.data.loader import Candle, DataLoader
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.indicator.rsi import WilderRSI
from rsi_trend_pullback.indicator.kaufman_er import KaufmanER
from rsi_trend_pullback.indicator.atr import WilderATR
from rsi_trend_pullback.state_machine.states import StrategyState, SignalType


def run_part_time_simulation():
    h1_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"
    if not os.path.exists(h1_path):
        candles = generate_xauusd_h1_historical_dataset()
        save_xauusd_csv(candles, h1_path)

    candles = DataLoader.load_from_csv(h1_path)

    # Strategy Parameters (Frozen V2.6)
    rsi = WilderRSI(period=14)
    er = KaufmanER(period=14)
    atr = WilderATR(period=14)
    units = 50.0 # 0.5 lot
    spread = 0.25
    slippage = 0.15
    friction_per_trade = (spread + slippage * 2) * units + (2000.0 * 2 * 0.00003 * units) # ~$23.00

    def is_online(dt_utc: datetime) -> bool:
        # Convert UTC to Bangkok (UTC+7)
        bkk_dt = dt_utc + timedelta(hours=7)
        if bkk_dt.weekday() >= 5: # Saturday/Sunday
            return False
        h = bkk_dt.hour
        return (9 <= h < 16) or (17 <= h < 22)

    # ── Simulation 1: 24/7 Full Baseline ──
    # ── Simulation 2: Part-Time Schedule ──
    for mode in ["24_7_BASELINE", "PART_TIME_DESKTOP"]:
        price_hist = []
        rsi.reset()
        er.reset()
        atr = WilderATR(period=14)

        active_trade = None
        closed_trades = []
        state = "IDLE"
        prev_rsi = None
        pending_signal = None

        for idx, c in enumerate(candles):
            price_hist.append(c.close)
            r_val = rsi.update(c.close)
            e_val = er.update(c.close)
            a_val = atr.update(c)

            bkk_time = c.timestamp + timedelta(hours=7)
            bot_active = True if mode == "24_7_BASELINE" else is_online(c.timestamp)

            # 1. Check Intrabar SL on open trade (Broker SL executes on server 24/7!)
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
                    net = gross - friction_per_trade
                    closed_trades.append({
                        "entry_time": active_trade["entry_time"],
                        "exit_time": c.timestamp,
                        "direction": active_trade["direction"],
                        "net_pnl": net,
                        "reason": "HARD_SL",
                        "bars": idx - active_trade["entry_bar"]
                    })
                    active_trade = None
                    state = "IDLE"

            # 2. Execute Pending Order at Open(T+1)
            if pending_signal is not None:
                exec_ok = True if mode == "24_7_BASELINE" else is_online(c.timestamp)
                if exec_ok and active_trade is None:
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

            # 3. Thesis Exit Check (Only when bot is online or in 24/7 mode)
            if active_trade is not None and bot_active and r_val is not None:
                thesis_exit = False
                if active_trade["direction"] == "LONG" and r_val < 40.0:
                    thesis_exit = True
                elif active_trade["direction"] == "SHORT" and r_val > 60.0:
                    thesis_exit = True

                if thesis_exit:
                    # Exit at next open or close
                    exit_p = c.close - slippage if active_trade["direction"] == "LONG" else c.close + slippage
                    gross = (exit_p - active_trade["entry_price"]) * units if active_trade["direction"] == "LONG" else (active_trade["entry_price"] - exit_p) * units
                    net = gross - friction_per_trade
                    closed_trades.append({
                        "entry_time": active_trade["entry_time"],
                        "exit_time": c.timestamp,
                        "direction": active_trade["direction"],
                        "net_pnl": net,
                        "reason": "THESIS_EXIT",
                        "bars": idx - active_trade["entry_bar"]
                    })
                    active_trade = None
                    state = "IDLE"

            # 4. State Machine Evaluation (Closed Bar T)
            if len(price_hist) > 14 and r_val is not None and prev_rsi is not None and e_val is not None and a_val is not None:
                chg14 = c.close - price_hist[-15]
                vol_ok = (a_val / 0.46) >= 5.0

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
                        # Entry Signal!
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
                        # Entry Signal!
                        if active_trade is None:
                            pending_signal = {"dir": "SHORT", "atr": a_val}
                    elif r_val > 60.0 or (e_val < 0.40 and chg14 > 0):
                        state = "IDLE"

                elif state in ("BULLISH_TRADED", "BEARISH_TRADED"):
                    if active_trade is None:
                        if state == "BULLISH_TRADED" and r_val < 40.0:
                            state = "IDLE"
                        elif state == "BEARISH_TRADED" and r_val > 60.0:
                            state = "IDLE"

            prev_rsi = r_val

        # Summary Metrics
        n = len(closed_trades)
        wins = [t for t in closed_trades if t["net_pnl"] > 0]
        losses = [t for t in closed_trades if t["net_pnl"] <= 0]
        tot_win = sum(t["net_pnl"] for t in wins)
        tot_loss = abs(sum(t["net_pnl"] for t in losses))
        pf = tot_win / tot_loss if tot_loss > 0 else 999.0
        pnl = sum(t["net_pnl"] for t in closed_trades)
        wr = len(wins) / n * 100.0 if n > 0 else 0.0

        # Drawdown
        eq = 100000.0
        peak = 100000.0
        max_dd = 0.0
        for t in closed_trades:
            eq += t["net_pnl"]
            if eq > peak: peak = eq
            dd = (peak - eq) / peak * 100.0
            if dd > max_dd: max_dd = dd

        print("=" * 80)
        print(f"RESULTS FOR MODE: {mode}")
        print(f"  * Total Completed Trades : {n} trades ({n/6.0:.1f} trades/year)")
        print(f"  * Win Rate               : {wr:.2f}% ({len(wins)}W / {len(losses)}L)")
        print(f"  * Profit Factor (ECN)    : {pf:.2f}")
        print(f"  * Total Net P&L (ECN)    : ${pnl:+,.2f}")
        print(f"  * Expectancy / Trade     : ${pnl/n:+,.2f} / trade" if n > 0 else "N/A")
        print(f"  * Maximum Drawdown       : -{max_dd:.2f}%")
        print("=" * 80)


if __name__ == "__main__":
    run_part_time_simulation()
