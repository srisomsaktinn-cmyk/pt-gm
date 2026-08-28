"""
Overnight Missed Trade Checker for Strategy V2.6 (Live MT5 Multi-Asset).
Auto-resolves broker symbol aliases (BTC / BTCUSD, US500 / SPX500 / US500Cash, XAUUSD / GOLD).
Scans the last 24-48 hours across all 5 assets.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Ensure project package is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rsi_trend_pullback.data.loader import Candle
from rsi_trend_pullback.indicator.rsi import WilderRSI
from rsi_trend_pullback.indicator.kaufman_er import KaufmanER
from rsi_trend_pullback.indicator.atr import WilderATR
from rsi_trend_pullback.state_machine.states import StrategyState, SignalType
from rsi_trend_pullback.state_machine.engine_v2 import RSIStateMachineV2


PORTFOLIO_ASSETS = {
    "XAUUSD": {"aliases": ["XAUUSD", "GOLD", "GOLD#", "XAUUSDm"], "friction_ref": 0.46,   "digits": 2},
    "USDJPY": {"aliases": ["USDJPY", "USDJPY#", "USDJPYm"],        "friction_ref": 0.018,  "digits": 3},
    "GBPUSD": {"aliases": ["GBPUSD", "GBPUSD#", "GBPUSDm"],        "friction_ref": 0.00020,"digits": 5},
    "US500":  {"aliases": ["US500Cash#", "US500#", "US500Cash", "US500", "SPX500#", "SPX500", "US500.cash", "SP500", "US500Index"], "friction_ref": 0.80, "digits": 2},
    "BTCUSD": {"aliases": ["BTC", "BTCUSD", "BTCUSD#", "BTCUSDm", "BITCOIN"], "friction_ref": 35.0, "digits": 2},
}

RSI_PERIOD = 14
ER_PERIOD = 14
ATR_PERIOD = 14
UPPER_LEVEL = 60.0
PULLBACK_LEVEL = 50.0
LOWER_LEVEL = 40.0
ER_THRESHOLD = 0.40
ATR_MULTIPLIER = 2.5
MIN_ATR_COST_RATIO = 5.0


def resolve_symbol(aliases: List[str]) -> Optional[str]:
    import MetaTrader5 as mt5
    for a in aliases:
        info = mt5.symbol_info(a)
        if info is not None:
            mt5.symbol_select(a, True)
            return a
    return None


def check_overnight_missed_signals():
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            print("[MT5 ERROR] Could not connect to MetaTrader 5. Please open MT5 terminal first.")
            return
    except ImportError:
        print("[ERROR] MetaTrader5 Python library not installed.")
        return

    print("=" * 80)
    print("OVERNIGHT MISSED SIGNAL AUDIT (Last 24-48 Hours across 5 Assets)")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Offline Window: 16:00 - 09:00 Bangkok Time)")
    print("=" * 80)

    total_missed_count = 0
    now_bangkok = datetime.now()

    for asset_name, spec in PORTFOLIO_ASSETS.items():
        actual_sym = resolve_symbol(spec["aliases"])
        if actual_sym is None:
            print(f"  * [{asset_name}] Warning: Symbol aliases {spec['aliases']} not found in broker MarketWatch.")
            continue

        rates = mt5.copy_rates_from_pos(actual_sym, mt5.TIMEFRAME_H1, 0, 60)
        if rates is None or len(rates) < 20:
            print(f"  * [{actual_sym}] Warning: Could not pull rates.")
            continue

        rates_sorted = sorted(rates, key=lambda x: x['time'])

        rsi = WilderRSI(period=RSI_PERIOD)
        er = KaufmanER(period=ER_PERIOD)
        atr = WilderATR(period=ATR_PERIOD)
        sm = RSIStateMachineV2(upper_level=UPPER_LEVEL, pullback_level=PULLBACK_LEVEL, lower_level=LOWER_LEVEL, er_threshold=ER_THRESHOLD)

        price_hist = []
        asset_signals = []

        for idx, r in enumerate(rates_sorted):
            c_time_utc = datetime.fromtimestamp(r['time'])
            candle = Candle(
                timestamp=c_time_utc,
                open=float(r['open']),
                high=float(r['high']),
                low=float(r['low']),
                close=float(r['close']),
                volume=float(r['tick_volume'])
            )
            price_hist.append(candle.close)
            r_val = rsi.update(candle.close)
            e_val = er.update(candle.close)
            a_val = atr.update(candle)

            chg14 = None
            if len(price_hist) > ER_PERIOD:
                chg14 = candle.close - price_hist[-1 - ER_PERIOD]

            vol_ok = (a_val / spec["friction_ref"]) >= MIN_ATR_COST_RATIO if (a_val and spec["friction_ref"] > 0) else False
            eff_er = e_val if vol_ok else 0.0

            sig = sm.evaluate_bar(bar_index=idx, timestamp=c_time_utc, current_rsi=r_val, current_er=eff_er, close_change_14=chg14)

            if sig and sig.signal_type in (SignalType.LONG_ENTRY_SIGNAL, SignalType.SHORT_ENTRY_SIGNAL):
                exec_time_utc = c_time_utc + timedelta(hours=1)
                exec_time_bkk = exec_time_utc + timedelta(hours=7)

                if (now_bangkok - exec_time_bkk).total_seconds() <= 86400:
                    hour_bkk = exec_time_bkk.hour
                    is_offline = not ((9 <= hour_bkk < 16) or (17 <= hour_bkk < 22))

                    theo_entry = rates_sorted[idx + 1]['open'] if idx + 1 < len(rates_sorted) else candle.close
                    direction = "LONG" if sig.signal_type == SignalType.LONG_ENTRY_SIGNAL else "SHORT"
                    hard_sl = theo_entry - (ATR_MULTIPLIER * a_val) if direction == "LONG" else theo_entry + (ATR_MULTIPLIER * a_val)

                    curr_price = rates_sorted[-1]['close']
                    pnl_diff = (curr_price - theo_entry) if direction == "LONG" else (theo_entry - curr_price)
                    is_profit = pnl_diff > 0

                    asset_signals.append({
                        "symbol": actual_sym,
                        "time_bkk": exec_time_bkk,
                        "direction": direction,
                        "is_offline": is_offline,
                        "theo_entry": theo_entry,
                        "hard_sl": hard_sl,
                        "curr_price": curr_price,
                        "pnl_diff": pnl_diff,
                        "is_profit": is_profit,
                        "reason": sig.reason,
                        "digits": spec["digits"]
                    })

        if asset_signals:
            for s in asset_signals:
                status_tag = "🔴 [MISSED OVERNIGHT]" if s["is_offline"] else "🟢 [ONLINE WINDOW]"
                pnl_tag = f"กำไร (+{s['pnl_diff']:.2f} pts)" if s["is_profit"] else f"ติดลบ ({s['pnl_diff']:.2f} pts)"
                if s["is_offline"]:
                    total_missed_count += 1

                print(f"{status_tag} {s['symbol']} {s['direction']} สัญญาณเกิดเวลา: {s['time_bkk'].strftime('%d/%m %H:%M น.')}")
                print(f"   * ราคาเข้าตามทฤษฎี : {s['theo_entry']:.{s['digits']}f} (SL: {s['hard_sl']:.{s['digits']}f})")
                print(f"   * ราคาตลาดปัจจุบัน  : {s['curr_price']:.{s['digits']}f} -> สถานะปัจจุบัน: {pnl_tag}")
                print(f"   * เหตุผลสัญญาณ      : {s['reason']}")
                print("-" * 80)

    if total_missed_count == 0:
        print("✅ ผลการตรวจสอบ: เมื่อคืนนี้ช่วงปิดคอม (16:00 - 09:00 น.) ไม่มีสัญญาณ Strategy V2.6 ตกหล่นเลย!")
        print("   (คุณไม่ได้พลาดโอกาสการเทรดใด ๆ ในช่วงที่ปิดคอมพิวเตอร์ครับ)")
    else:
        print(f"⚠️ ผลการตรวจสอบ: ตรวจพบสัญญาณที่เกิดช่วงปิดคอมทั้งหมด {total_missed_count} สัญญาณ ตามรายละเอียดด้านบนครับ")
    print("=" * 80)


if __name__ == "__main__":
    check_overnight_missed_signals()
