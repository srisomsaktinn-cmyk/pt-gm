"""
Production-Ready Multi-Asset Automated MetaTrader 5 Paper / Demo Trading Bot for Strategy V2.6 (Frozen Spec).
Features Auto-Compounding Dynamic Position Sizing (3.0% Balanced Risk per Trade).
Auto-resolves broker symbol aliases (BTC / BTCUSD, US500 / SPX500 / US500Cash, XAUUSD / GOLD).

Monitors and trades the Top 5 Qualified Trending Assets simultaneously on H1:
1. XAUUSD (Spot Gold)
2. USDJPY (US Dollar / Japanese Yen)
3. GBPUSD (British Pound / US Dollar)
4. US500  (S&P 500 Equity Index CFD)
5. BTCUSD / BTC (Bitcoin / US Dollar)

Usage:
  python mt5_multi_asset_paper_trader.py
  (or run_multi_bot.bat)
"""

import time
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

# Ensure project package is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rsi_trend_pullback.data.loader import Candle
from rsi_trend_pullback.indicator.rsi import WilderRSI
from rsi_trend_pullback.indicator.kaufman_er import KaufmanER
from rsi_trend_pullback.indicator.atr import WilderATR
from rsi_trend_pullback.state_machine.states import StrategyState, SignalType, TradingSignal
from rsi_trend_pullback.state_machine.engine_v2 import RSIStateMachineV2
from rsi_trend_pullback.paper_trading.audit_logger import (
    ShadowAuditRecord,
    ShadowAuditLogger,
    ExitTriggerType,
    DivergenceCategory
)
from rsi_trend_pullback.paper_trading.reporter import PeriodicBatchReporter


# ═════════════════════════════════════════════════════════════════════════════
# BALANCED RISK & MULTI-ASSET CONFIGURATION (STRATEGY V2.6 FROZEN)
# ═════════════════════════════════════════════════════════════════════════════
TIMEFRAME_STRING = "H1"
BALANCED_RISK_PER_TRADE = 0.03  # 3.0% Balanced Risk per Trade with Auto-Compounding

PORTFOLIO_ASSETS = {
    "XAUUSD": {"aliases": ["XAUUSD", "GOLD", "GOLD#", "XAUUSDm"], "default_lot": 0.01, "units": 1.0,     "friction_ref": 0.46,   "digits": 2, "magic": 20260801},
    "USDJPY": {"aliases": ["USDJPY", "USDJPY#", "USDJPYm"],        "default_lot": 0.01, "units": 1000.0,  "friction_ref": 0.018,  "digits": 3, "magic": 20260802},
    "GBPUSD": {"aliases": ["GBPUSD", "GBPUSD#", "GBPUSDm"],        "default_lot": 0.01, "units": 1000.0,  "friction_ref": 0.00020,"digits": 5, "magic": 20260803},
    "US500":  {"aliases": ["US500Cash#", "US500#", "US500Cash", "US500", "SPX500#", "SPX500", "US500.cash", "SP500", "US500Index"], "default_lot": 0.10, "units": 0.10, "friction_ref": 0.80, "digits": 2, "magic": 20260804},
    "BTCUSD": {"aliases": ["BTC", "BTCUSD", "BTCUSD#", "BTCUSDm", "BITCOIN"], "default_lot": 0.01, "units": 0.01, "friction_ref": 35.0, "digits": 2, "magic": 20260805},
}

# Strategy V2.6 Frozen Parameters
RSI_PERIOD = 14
ER_PERIOD = 14
ATR_PERIOD = 14
UPPER_LEVEL = 60.0
PULLBACK_LEVEL = 50.0
LOWER_LEVEL = 40.0
ER_THRESHOLD = 0.40
ATR_MULTIPLIER = 2.5
MIN_ATR_COST_RATIO = 5.0

MT5_ACCOUNT = 0
MT5_SERVER = ""
MT5_PASSWORD = ""


class SingleAssetContext:
    def __init__(self, symbol: str, actual_symbol: str, config: Dict[str, Any]):
        self.symbol = symbol
        self.actual_symbol = actual_symbol
        self.config = config
        self.default_lot = config["default_lot"]
        self.units = config["units"]
        self.friction_ref = config["friction_ref"]
        self.digits = config["digits"]
        self.magic = config["magic"]

        self.indicator_rsi = WilderRSI(period=RSI_PERIOD)
        self.indicator_er = KaufmanER(period=ER_PERIOD)
        self.indicator_atr = WilderATR(period=ATR_PERIOD)
        self.state_machine = RSIStateMachineV2(
            upper_level=UPPER_LEVEL,
            pullback_level=PULLBACK_LEVEL,
            lower_level=LOWER_LEVEL,
            er_threshold=ER_THRESHOLD
        )

        self.price_history: List[float] = []
        self.last_processed_candle_time: Optional[datetime] = None
        self.active_record: Optional[ShadowAuditRecord] = None
        self.active_direction: Optional[str] = None
        self.active_ticket: Optional[int] = None
        self.active_lot_size: float = config["default_lot"]
        self.pending_signal: Optional[TradingSignal] = None

        self.latest_atr: Optional[float] = None
        self.latest_er: Optional[float] = None
        self.latest_rsi: Optional[float] = None


class MT5MultiAssetPaperTrader:

    def __init__(self, output_csv_path: str = "d:/Kaeha/rsi_trend_pullback/output_paper_trading/multi_asset_v26_shadow_audit_log.csv"):
        self.output_csv_path = output_csv_path
        os.makedirs(os.path.dirname(os.path.abspath(output_csv_path)), exist_ok=True)
        self.contexts: Dict[str, SingleAssetContext] = {}
        self._trade_counter: int = 0
        self._completed_records: List[ShadowAuditRecord] = []

    def calculate_dynamic_lot_size(self, sym: str, sl_distance: float) -> float:
        import MetaTrader5 as mt5
        acc = mt5.account_info()
        equity = acc.equity if acc else 1000.0
        dollar_risk = equity * BALANCED_RISK_PER_TRADE

        sym_info = mt5.symbol_info(sym)
        if sym_info is None or sl_distance <= 0:
            return self.contexts[sym].default_lot

        tick_size = sym_info.trade_tick_size or (10 ** -sym_info.digits)
        tick_value = sym_info.trade_tick_value or 1.0

        loss_per_1_lot = (sl_distance / tick_size) * tick_value
        if loss_per_1_lot <= 0:
            return self.contexts[sym].default_lot

        raw_lot = dollar_risk / loss_per_1_lot
        step = sym_info.volume_step or 0.01
        rounded_lot = round(raw_lot / step) * step
        min_v = sym_info.volume_min or 0.01
        max_v = sym_info.volume_max or 5.0
        final_lot = max(min_v, min(max_v, rounded_lot))

        print(f"[AUTO-RISK 3.0%] {sym} Equity=${equity:,.2f} | Risk Amount=${dollar_risk:,.2f} | SL Distance={sl_distance:.4f} -> Sized Lot: {final_lot:.2f} lot")
        return round(final_lot, 2)

    def initialize_mt5(self) -> bool:
        try:
            import MetaTrader5 as mt5
            if not mt5.initialize():
                print(f"[MT5 ERROR] initialize() failed: {mt5.last_error()}")
                return False

            if MT5_ACCOUNT > 0:
                authorized = mt5.login(MT5_ACCOUNT, password=MT5_PASSWORD, server=MT5_SERVER)
                if not authorized:
                    print(f"[MT5 ERROR] Login failed for account {MT5_ACCOUNT}: {mt5.last_error()}")
                    return False

            account_info = mt5.account_info()
            print("=" * 80)
            print("METATRADER 5 MULTI-ASSET LIVE CONNECTION ESTABLISHED")
            if account_info:
                print(f"  * Account    : {account_info.login} ({account_info.company})")
                print(f"  * Balance    : ${account_info.balance:,.2f} {account_info.currency} (Equity: ${account_info.equity:,.2f})")
                print(f"  * Leverage   : 1:{account_info.leverage}")
                print(f"  * Sizing Mode: Balanced Dynamic Risk (3.0% Auto-Compounding)")
            print("=" * 80)

            # Resolve broker aliases
            for canonical_name, cfg in PORTFOLIO_ASSETS.items():
                resolved = None
                for alias in cfg["aliases"]:
                    info = mt5.symbol_info(alias)
                    if info is not None:
                        mt5.symbol_select(alias, True)
                        resolved = alias
                        break
                if resolved:
                    self.contexts[resolved] = SingleAssetContext(canonical_name, resolved, cfg)
                    print(f"  * Mapped [{canonical_name}] -> MT5 Broker Symbol: '{resolved}'")
                else:
                    print(f"  * Warning: Could not find broker symbol for [{canonical_name}] (Aliases: {cfg['aliases']})")

            return True
        except ImportError:
            print("[WARNING] 'MetaTrader5' Python library not installed.")
            return False

    def warm_up_all_assets(self, num_bars: int = 150) -> bool:
        import MetaTrader5 as mt5

        print("\n[WARM-UP] Priming indicator buffers for all mapped portfolio assets...")
        for sym, ctx in self.contexts.items():
            mt5.symbol_select(sym, True)
            rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 1, num_bars)
            if rates is None or len(rates) == 0:
                print(f"  * [{sym}] Warning: Could not pull rates.")
                continue

            rates_sorted = sorted(rates, key=lambda x: x['time'])
            for r in rates_sorted:
                c_time = datetime.fromtimestamp(r['time'])
                candle = Candle(
                    timestamp=c_time,
                    open=float(r['open']),
                    high=float(r['high']),
                    low=float(r['low']),
                    close=float(r['close']),
                    volume=float(r['tick_volume'])
                )
                ctx.price_history.append(candle.close)
                ctx.latest_rsi = ctx.indicator_rsi.update(candle.close)
                ctx.latest_er = ctx.indicator_er.update(candle.close)
                ctx.latest_atr = ctx.indicator_atr.update(candle)
                ctx.last_processed_candle_time = c_time

            existing_pos = mt5.positions_get(symbol=sym)
            active_pos = [p for p in (existing_pos or []) if p.magic == ctx.magic]
            if active_pos:
                pos = active_pos[0]
                ctx.active_ticket = pos.ticket
                ctx.active_direction = "LONG" if pos.type == mt5.ORDER_TYPE_BUY else "SHORT"
                ctx.active_lot_size = pos.volume
                ctx.state_machine._state = StrategyState.BULLISH_TRADED if ctx.active_direction == "LONG" else StrategyState.BEARISH_TRADED
                print(f"  * [{sym}] Found active position #{pos.ticket} ({ctx.active_direction} {pos.volume} lot). State={ctx.state_machine.current_state.value}")
            else:
                ctx.state_machine._state = StrategyState.IDLE
                print(f"  * [{sym}] Ready. Clean Startup (IDLE) | RSI={ctx.latest_rsi:.1f}, ER={ctx.latest_er:.2f}, ATR={ctx.latest_atr:.4f}")

        print("[WARM-UP COMPLETE] All portfolio assets ready with Auto-Risk 3.0%.\n")
        return True

    def check_all_intrabar_stops(self) -> None:
        import MetaTrader5 as mt5

        for sym, ctx in self.contexts.items():
            if ctx.active_record is not None and ctx.active_ticket is not None:
                positions = mt5.positions_get(ticket=ctx.active_ticket)
                if positions is not None and len(positions) == 0:
                    deals = mt5.history_deals_get(position=ctx.active_ticket)
                    exit_price = ctx.active_record.hard_stop_price
                    exit_time = datetime.now()
                    slip = 0.0

                    if deals and len(deals) >= 2:
                        exit_deal = deals[-1]
                        exit_price = float(exit_deal.price)
                        exit_time = datetime.fromtimestamp(exit_deal.time)
                        slip = abs(exit_price - ctx.active_record.hard_stop_price)

                    print(f"\n[INTRABAR HARD STOP] {sym} #{ctx.active_ticket} stopped out @ {exit_price} (Time: {exit_time})")
                    ctx.active_record.finalize_trade(
                        exit_trigger_type=ExitTriggerType.HARD_STOP,
                        exit_trigger_time=exit_time,
                        exit_trigger_price=ctx.active_record.hard_stop_price,
                        exit_execution_time=exit_time,
                        exit_signal_time=exit_time,
                        theoretical_exit=ctx.active_record.hard_stop_price,
                        actual_exit=exit_price,
                        exit_slippage=slip,
                        exit_reason=f"HARD_STOP: Touch {ctx.active_record.hard_stop_price}",
                        units=ctx.active_lot_size * 100.0
                    )
                    self._completed_records.append(ctx.active_record)
                    ShadowAuditLogger.export_audit_csv(self._completed_records, self.output_csv_path)

                    ctx.active_record = None
                    ctx.active_direction = None
                    ctx.active_ticket = None

    def process_asset_candle_close(self, sym: str, closed_candle: Candle, current_open_candle: Candle) -> None:
        import MetaTrader5 as mt5
        ctx = self.contexts[sym]

        if ctx.pending_signal is not None:
            sig = ctx.pending_signal
            ctx.pending_signal = None
            theo_open = current_open_candle.open

            if sig.signal_type in (SignalType.LONG_EXIT_SIGNAL, SignalType.SHORT_EXIT_SIGNAL):
                if ctx.active_ticket is not None:
                    print(f"[THESIS EXIT] Closing {sym} position #{ctx.active_ticket} ({sig.reason})...")
                    tick = mt5.symbol_info_tick(sym)
                    order_type = mt5.ORDER_TYPE_SELL if ctx.active_direction == "LONG" else mt5.ORDER_TYPE_BUY
                    close_price = tick.bid if ctx.active_direction == "LONG" else tick.ask

                    req = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": sym,
                        "volume": float(ctx.active_lot_size),
                        "type": order_type,
                        "position": ctx.active_ticket,
                        "price": close_price,
                        "deviation": 20,
                        "magic": ctx.magic,
                        "comment": f"V2.6 Multi {sym} Exit",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    res = mt5.order_send(req)
                    actual_exit = res.price if (res and res.retcode == mt5.TRADE_RETCODE_DONE) else close_price
                    slip = abs(actual_exit - theo_open)

                    ctx.active_record.finalize_trade(
                        exit_trigger_type=ExitTriggerType.THESIS_EXIT,
                        exit_trigger_time=closed_candle.timestamp,
                        exit_trigger_price=theo_open,
                        exit_execution_time=datetime.now(),
                        exit_signal_time=closed_candle.timestamp,
                        theoretical_exit=theo_open,
                        actual_exit=actual_exit,
                        exit_slippage=slip,
                        exit_reason=sig.reason,
                        units=ctx.active_lot_size * 100.0
                    )
                    self._completed_records.append(ctx.active_record)
                    ShadowAuditLogger.export_audit_csv(self._completed_records, self.output_csv_path)

                    print(f"[THESIS EXIT DONE] {sym} #{ctx.active_ticket} Closed @ {actual_exit} (PnL logged to CSV)")
                    ctx.active_record = None
                    ctx.active_direction = None
                    ctx.active_ticket = None

            elif sig.signal_type in (SignalType.LONG_ENTRY_SIGNAL, SignalType.SHORT_ENTRY_SIGNAL):
                if ctx.active_record is None:
                    self._trade_counter += 1
                    direction = "LONG" if sig.signal_type == SignalType.LONG_ENTRY_SIGNAL else "SHORT"
                    tick = mt5.symbol_info_tick(sym)
                    order_type = mt5.ORDER_TYPE_BUY if direction == "LONG" else mt5.ORDER_TYPE_SELL
                    req_price = tick.ask if direction == "LONG" else tick.bid
                    spread = round(tick.ask - tick.bid, ctx.digits)

                    atr_val = ctx.latest_atr or (req_price * 0.01)
                    sl_dist = ATR_MULTIPLIER * atr_val
                    hard_sl = round(req_price - sl_dist if direction == "LONG" else req_price + sl_dist, ctx.digits)

                    dynamic_lot = self.calculate_dynamic_lot_size(sym, sl_dist)

                    req = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": sym,
                        "volume": float(dynamic_lot),
                        "type": order_type,
                        "price": req_price,
                        "sl": float(hard_sl),
                        "deviation": 20,
                        "magic": ctx.magic,
                        "comment": f"V2.6 Multi {sym}",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    t0 = time.time()
                    res = mt5.order_send(req)
                    latency = (time.time() - t0) * 1000.0

                    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                        actual_fill = res.price
                        ticket = res.order
                        print(f"\n[ORDER FILLED] {sym} #{ticket} {direction} {dynamic_lot} lots @ {actual_fill} (SL: {hard_sl}, Latency: {latency:.1f}ms)")
                    else:
                        actual_fill = req_price
                        ticket = 999000 + self._trade_counter
                        print(f"\n[ORDER SIMULATED] {sym} {direction} @ {actual_fill} (Broker retcode: {res.retcode if res else 'None'})")

                    entry_slip = actual_fill - theo_open if direction == "LONG" else theo_open - actual_fill
                    state_before = ctx.state_machine.current_state.value
                    ctx.state_machine.notify_order_executed(len(ctx.price_history), current_open_candle.timestamp)
                    state_after = ctx.state_machine.current_state.value

                    vol_ratio = (atr_val / ctx.friction_ref) if (atr_val and ctx.friction_ref > 0) else 0.0

                    ctx.active_record = ShadowAuditRecord(
                        trade_id=self._trade_counter,
                        timestamp=current_open_candle.timestamp,
                        direction=f"{sym}_{direction}",
                        theoretical_entry=theo_open,
                        actual_entry=actual_fill,
                        entry_slippage=round(entry_slip, ctx.digits),
                        spread_at_entry=spread,
                        execution_delay_ms=round(latency, 1),
                        atr_14=round(atr_val, ctx.digits),
                        er_14=round(ctx.latest_er or 0.0, 4),
                        volatility_ratio=round(vol_ratio, 2),
                        rsi_14=round(ctx.latest_rsi or 0.0, 2),
                        hard_stop_price=hard_sl,
                        state_before=state_before,
                        state_after=state_after
                    )
                    ctx.active_direction = direction
                    ctx.active_ticket = ticket
                    ctx.active_lot_size = dynamic_lot

        ctx.price_history.append(closed_candle.close)
        rsi_val = ctx.indicator_rsi.update(closed_candle.close)
        er_val = ctx.indicator_er.update(closed_candle.close)
        atr_val = ctx.indicator_atr.update(closed_candle)

        ctx.latest_rsi = rsi_val
        ctx.latest_er = er_val
        ctx.latest_atr = atr_val

        close_change_14 = None
        if len(ctx.price_history) > ER_PERIOD:
            close_change_14 = closed_candle.close - ctx.price_history[-1 - ER_PERIOD]

        is_vol_sufficient = (atr_val / ctx.friction_ref) >= MIN_ATR_COST_RATIO if (atr_val and ctx.friction_ref > 0) else False
        effective_er = er_val if is_vol_sufficient else 0.0

        signal = ctx.state_machine.evaluate_bar(
            bar_index=len(ctx.price_history),
            timestamp=closed_candle.timestamp,
            current_rsi=rsi_val,
            current_er=effective_er,
            close_change_14=close_change_14
        )

        if signal is not None:
            print(f"[{sym} SIGNAL] {signal.signal_type.value} at {signal.timestamp} (RSI={rsi_val:.1f}, ER={er_val:.2f}, Reason: {signal.reason})")
            if signal.signal_type in (SignalType.LONG_EXIT_SIGNAL, SignalType.SHORT_EXIT_SIGNAL):
                if ctx.active_record is not None:
                    ctx.pending_signal = signal
            else:
                if ctx.active_record is None:
                    ctx.pending_signal = signal

        completed_count = len(self._completed_records)
        if completed_count > 0 and completed_count % 10 == 0:
            batch_num = completed_count // 10
            print(f"\n{PeriodicBatchReporter.generate_10_trade_summary(self._completed_records, batch_num)}")

    def run_live_loop(self) -> None:
        import MetaTrader5 as mt5

        print("=" * 80)
        print(f"[ACTIVE] Multi-Asset Portfolio Bot (Auto-Risk 3.0% Balanced) is POLLING {len(self.contexts)} Assets on H1...")
        print(f"[AUDIT LOG] Output destination: {self.output_csv_path}")
        print("=" * 80)

        while True:
            try:
                self.check_all_intrabar_stops()

                for sym, ctx in self.contexts.items():
                    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 2)
                    if rates is not None and len(rates) >= 2:
                        rates_sorted = sorted(rates, key=lambda x: x['time'])
                        closed_rate = rates_sorted[0]
                        forming_rate = rates_sorted[1]

                        closed_bar_time = datetime.fromtimestamp(closed_rate['time'])
                        forming_bar_time = datetime.fromtimestamp(forming_rate['time'])

                        if ctx.last_processed_candle_time is None or closed_bar_time > ctx.last_processed_candle_time:
                            closed_c = Candle(
                                timestamp=closed_bar_time,
                                open=float(closed_rate['open']),
                                high=float(closed_rate['high']),
                                low=float(closed_rate['low']),
                                close=float(closed_rate['close']),
                                volume=float(closed_rate['tick_volume'])
                            )
                            forming_c = Candle(
                                timestamp=forming_bar_time,
                                open=float(forming_rate['open']),
                                high=float(forming_rate['high']),
                                low=float(forming_rate['low']),
                                close=float(forming_rate['close']),
                                volume=float(forming_rate['tick_volume'])
                            )
                            print(f"[{sym} H1 CLOSED: {closed_bar_time}] Close=${closed_c.close} | Open(T+1)=${forming_c.open}")
                            self.process_asset_candle_close(sym, closed_c, forming_c)
                            ctx.last_processed_candle_time = closed_bar_time

                time.sleep(2)

            except KeyboardInterrupt:
                print("\n[STOPPED] Multi-Asset Bot terminated by user.")
                break
            except Exception as e:
                print(f"[MULTI-ASSET EXCEPTION] {e}")
                time.sleep(5)


if __name__ == "__main__":
    runner = MT5MultiAssetPaperTrader()
    if runner.initialize_mt5():
        if runner.warm_up_all_assets(num_bars=150):
            runner.run_live_loop()
    else:
        print("[EXIT] Could not connect to MetaTrader 5.")
