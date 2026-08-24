"""
Production-Ready Automated MetaTrader 5 Paper / Demo Trading Bot for Strategy V2.6 (Frozen Spec).
Connects to MT5 terminal, polls live H1 candle closes, executes market orders,
and records the complete 33-column Shadow Audit Log line-by-line.

Usage:
  python mt5_paper_trader.py
"""

import time
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

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
# CONFIGURATION (FROZEN PARAMETERS)
# ═════════════════════════════════════════════════════════════════════════════
SYMBOL = "XAUUSD"
TIMEFRAME_STRING = "H1"
UNITS_PER_TRADE = 50.0  # 50 oz = 0.50 standard lot on Gold
LOT_SIZE = 0.50         # MT5 order volume

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
ESTIMATED_ROUNDTURN_FRICTION = 0.46 # $0.46/oz (~4.6 pips)

# MT5 Account Credentials (Optional: Leave 0/empty if MT5 is already logged in)
MT5_ACCOUNT = 0
MT5_SERVER = ""
MT5_PASSWORD = ""
MAGIC_NUMBER = 20260824


class MT5PaperTradingLiveRunner:
    """
    Live MT5 Paper Trading Orchestrator for Strategy V2.6.
    """

    def __init__(self, output_csv_path: str = "d:/Kaeha/rsi_trend_pullback/output_paper_trading/xauusd_v26_shadow_audit_log.csv"):
        self.output_csv_path = output_csv_path
        os.makedirs(os.path.dirname(os.path.abspath(output_csv_path)), exist_ok=True)

        # Frozen Indicators
        self.indicator_rsi = WilderRSI(period=RSI_PERIOD)
        self.indicator_er = KaufmanER(period=ER_PERIOD)
        self.indicator_atr = WilderATR(period=ATR_PERIOD)
        self.state_machine = RSIStateMachineV2(
            upper_level=UPPER_LEVEL,
            pullback_level=PULLBACK_LEVEL,
            lower_level=LOWER_LEVEL,
            er_threshold=ER_THRESHOLD
        )

        self._price_history: List[float] = []
        self._last_processed_candle_time: Optional[datetime] = None
        self._active_record: Optional[ShadowAuditRecord] = None
        self._active_direction: Optional[str] = None
        self._active_ticket: Optional[int] = None
        self._trade_counter: int = 0
        self._completed_records: List[ShadowAuditRecord] = []
        self._pending_signal: Optional[TradingSignal] = None

        self._latest_atr: Optional[float] = None
        self._latest_er: Optional[float] = None
        self._latest_rsi: Optional[float] = None

    def initialize_mt5(self) -> bool:
        """Initializes connection to the MetaTrader 5 terminal."""
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
            print("METATRADER 5 LIVE CONNECTION ESTABLISHED")
            if account_info:
                print(f"  * Account: {account_info.login} ({account_info.company})")
                print(f"  * Balance: ${account_info.balance:,.2f} {account_info.currency}")
                print(f"  * Leverage: 1:{account_info.leverage}")
                print(f"  * Trade Mode: {'Demo/Paper' if account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO else 'Live'}")
            print("=" * 80)
            return True
        except ImportError:
            print("[WARNING] 'MetaTrader5' Python library not installed. Running in Dry-Run / Paper Simulation Mode.")
            return False

    def warm_up_history(self, num_bars: int = 200) -> bool:
        """Pulls historical H1 bars from MT5 to warm up Wilder RSI, Kaufman ER, and Wilder ATR."""
        try:
            import MetaTrader5 as mt5
            rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_H1, 1, num_bars)
            if rates is None or len(rates) == 0:
                print("[MT5 ERROR] Failed to fetch historical warm-up rates.")
                return False

            print(f"[WARM-UP] Warming up indicators with {len(rates)} historical H1 candles...")
            for idx, r in enumerate(rates):
                c_time = datetime.fromtimestamp(r['time'])
                candle = Candle(
                    timestamp=c_time,
                    open=float(r['open']),
                    high=float(r['high']),
                    low=float(r['low']),
                    close=float(r['close']),
                    volume=float(r['tick_volume'])
                )
                self._price_history.append(candle.close)
                rsi_val = self.indicator_rsi.update(candle.close)
                er_val = self.indicator_er.update(candle.close)
                atr_val = self.indicator_atr.update(candle)

                self._latest_rsi = rsi_val
                self._latest_er = er_val
                self._latest_atr = atr_val

                # Evaluate state machine without executing old orders
                close_change_14 = None
                if len(self._price_history) > ER_PERIOD:
                    close_change_14 = candle.close - self._price_history[-1 - ER_PERIOD]

                is_vol_sufficient = (atr_val / ESTIMATED_ROUNDTURN_FRICTION) >= MIN_ATR_COST_RATIO if (atr_val and ESTIMATED_ROUNDTURN_FRICTION > 0) else False
                effective_er = er_val if is_vol_sufficient else 0.0

                self.state_machine.evaluate_bar(
                    bar_index=idx,
                    timestamp=c_time,
                    current_rsi=rsi_val,
                    current_er=effective_er,
                    close_change_14=close_change_14
                )
                self._last_processed_candle_time = c_time

            print(f"[WARM-UP COMPLETE] State={self.state_machine.current_state.value}, RSI={self._latest_rsi:.2f}, ER={self._latest_er:.4f}, ATR=${self._latest_atr:.2f}")
            return True
        except Exception as e:
            print(f"[WARM-UP EXCEPTION] {e}")
            return False

    def check_intrabar_status(self) -> None:
        """Checks if active position was closed intrabar by Stop Loss."""
        if self._active_record is None or self._active_ticket is None:
            return

        try:
            import MetaTrader5 as mt5
            # Check open positions
            positions = mt5.positions_get(ticket=self._active_ticket)
            if positions is not None and len(positions) == 0:
                # Position is no longer open -> Closed by SL or TakeProfit
                deals = mt5.history_deals_get(position=self._active_ticket)
                exit_price = self._active_record.hard_stop_price
                exit_time = datetime.now()
                slip = 0.0

                if deals and len(deals) >= 2:
                    exit_deal = deals[-1]
                    exit_price = float(exit_deal.price)
                    exit_time = datetime.fromtimestamp(exit_deal.time)
                    slip = abs(exit_price - self._active_record.hard_stop_price)

                print(f"\n[INTRABAR HARD STOP TRIGGERED] Ticket #{self._active_ticket} stopped out at ${exit_price:.2f} (Time: {exit_time})")
                self._active_record.finalize_trade(
                    exit_trigger_type=ExitTriggerType.HARD_STOP,
                    exit_trigger_time=exit_time,
                    exit_trigger_price=self._active_record.hard_stop_price,
                    exit_execution_time=exit_time,
                    exit_signal_time=exit_time,
                    theoretical_exit=self._active_record.hard_stop_price,
                    actual_exit=exit_price,
                    exit_slippage=slip,
                    exit_reason=f"HARD_STOP: Touch ${self._active_record.hard_stop_price:.2f}",
                    units=UNITS_PER_TRADE
                )
                self._completed_records.append(self._active_record)
                ShadowAuditLogger.export_audit_csv(self._completed_records, self.output_csv_path)

                self._active_record = None
                self._active_direction = None
                self._active_ticket = None
        except Exception as e:
            print(f"[INTRABAR CHECK ERROR] {e}")

    def on_new_candle_close(self, closed_candle: Candle, current_open_candle: Candle) -> None:
        """
        Executes exactly when a new H1 candle forms:
        1. Executes pending Thesis Exit / Entry order at Open(T+1).
        2. Calculates indicators for Closed Candle(T) and evaluates state machine.
        """
        import MetaTrader5 as mt5

        # ── 1. EXECUTE PENDING ORDER AT BAR OPEN ──
        if self._pending_signal is not None:
            sig = self._pending_signal
            self._pending_signal = None
            theo_open = current_open_candle.open

            # Handle Thesis Exit
            if sig.signal_type in (SignalType.LONG_EXIT_SIGNAL, SignalType.SHORT_EXIT_SIGNAL):
                if self._active_ticket is not None:
                    print(f"[THESIS EXIT SIGNAL] Closing position #{self._active_ticket} at new bar Open ({sig.reason})...")
                    tick = mt5.symbol_info_tick(SYMBOL)
                    order_type = mt5.ORDER_TYPE_SELL if self._active_direction == "LONG" else mt5.ORDER_TYPE_BUY
                    close_req_price = tick.bid if self._active_direction == "LONG" else tick.ask

                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": SYMBOL,
                        "volume": float(LOT_SIZE),
                        "type": order_type,
                        "position": self._active_ticket,
                        "price": close_req_price,
                        "deviation": 20,
                        "magic": MAGIC_NUMBER,
                        "comment": "V2.6 Thesis Exit",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    t0 = time.time()
                    res = mt5.order_send(request)
                    exec_latency = (time.time() - t0) * 1000.0

                    actual_exit = res.price if (res and res.retcode == mt5.TRADE_RETCODE_DONE) else close_req_price
                    slip = abs(actual_exit - theo_open)

                    self._active_record.finalize_trade(
                        exit_trigger_type=ExitTriggerType.THESIS_EXIT,
                        exit_trigger_time=closed_candle.timestamp,
                        exit_trigger_price=theo_open,
                        exit_execution_time=datetime.now(),
                        exit_signal_time=closed_candle.timestamp,
                        theoretical_exit=theo_open,
                        actual_exit=actual_exit,
                        exit_slippage=slip,
                        exit_reason=sig.reason,
                        units=UNITS_PER_TRADE
                    )
                    self._completed_records.append(self._active_record)
                    ShadowAuditLogger.export_audit_csv(self._completed_records, self.output_csv_path)

                    print(f"[THESIS EXIT COMPLETED] Actual Fill=${actual_exit:.2f}, Slippage=${slip:.2f}, Latency={exec_latency:.1f}ms")
                    self._active_record = None
                    self._active_direction = None
                    self._active_ticket = None

            # Handle New Entry
            elif sig.signal_type in (SignalType.LONG_ENTRY_SIGNAL, SignalType.SHORT_ENTRY_SIGNAL):
                if self._active_record is None:
                    self._trade_counter += 1
                    direction = "LONG" if sig.signal_type == SignalType.LONG_ENTRY_SIGNAL else "SHORT"
                    tick = mt5.symbol_info_tick(SYMBOL)
                    order_type = mt5.ORDER_TYPE_BUY if direction == "LONG" else mt5.ORDER_TYPE_SELL
                    req_price = tick.ask if direction == "LONG" else tick.bid
                    spread = round(tick.ask - tick.bid, 2)

                    atr_val = self._latest_atr or 5.0
                    hard_sl = round(req_price - (ATR_MULTIPLIER * atr_val) if direction == "LONG" else req_price + (ATR_MULTIPLIER * atr_val), 2)

                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": SYMBOL,
                        "volume": float(LOT_SIZE),
                        "type": order_type,
                        "price": req_price,
                        "sl": float(hard_sl),
                        "deviation": 20,
                        "magic": MAGIC_NUMBER,
                        "comment": "V2.6 Frozen Entry",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    t0 = time.time()
                    res = mt5.order_send(request)
                    exec_latency = (time.time() - t0) * 1000.0

                    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                        actual_fill = res.price
                        ticket = res.order
                        print(f"\n[ORDER FILLED] #{ticket} {direction} {LOT_SIZE} lots @ ${actual_fill:.2f} (SL: ${hard_sl:.2f}, Latency: {exec_latency:.1f}ms)")
                    else:
                        actual_fill = req_price
                        ticket = 999999 + self._trade_counter
                        print(f"\n[ORDER SIMULATED] {direction} @ ${actual_fill:.2f} (Broker retcode: {res.retcode if res else 'None'})")

                    entry_slip = actual_fill - theo_open if direction == "LONG" else theo_open - actual_fill
                    state_before = self.state_machine.current_state.value
                    self.state_machine.notify_order_executed(len(self._price_history), current_open_candle.timestamp)
                    state_after = self.state_machine.current_state.value

                    vol_ratio = (atr_val / ESTIMATED_ROUNDTURN_FRICTION) if atr_val else 0.0

                    self._active_record = ShadowAuditRecord(
                        trade_id=self._trade_counter,
                        timestamp=current_open_candle.timestamp,
                        direction=direction,
                        theoretical_entry=theo_open,
                        actual_entry=actual_fill,
                        entry_slippage=round(entry_slip, 2),
                        spread_at_entry=spread,
                        execution_delay_ms=round(exec_latency, 1),
                        atr_14=round(atr_val, 2),
                        er_14=round(self._latest_er or 0.0, 4),
                        volatility_ratio=round(vol_ratio, 2),
                        rsi_14=round(self._latest_rsi or 0.0, 2),
                        hard_stop_price=hard_sl,
                        state_before=state_before,
                        state_after=state_after
                    )
                    self._active_direction = direction
                    self._active_ticket = ticket

        # ── 2. BAR CLOSE CALCULATIONS (CLOSED CANDLE T) ──
        self._price_history.append(closed_candle.close)
        rsi_val = self.indicator_rsi.update(closed_candle.close)
        er_val = self.indicator_er.update(closed_candle.close)
        atr_val = self.indicator_atr.update(closed_candle)

        self._latest_rsi = rsi_val
        self._latest_er = er_val
        self._latest_atr = atr_val

        close_change_14 = None
        if len(self._price_history) > ER_PERIOD:
            close_change_14 = closed_candle.close - self._price_history[-1 - ER_PERIOD]

        # LAYER 1: Volatility Sufficiency (ENTRY FILTER ONLY)
        is_vol_sufficient = (atr_val / ESTIMATED_ROUNDTURN_FRICTION) >= MIN_ATR_COST_RATIO if (atr_val and ESTIMATED_ROUNDTURN_FRICTION > 0) else False
        effective_er = er_val if is_vol_sufficient else 0.0

        signal = self.state_machine.evaluate_bar(
            bar_index=len(self._price_history),
            timestamp=closed_candle.timestamp,
            current_rsi=rsi_val,
            current_er=effective_er,
            close_change_14=close_change_14
        )

        if signal is not None:
            print(f"[SIGNAL GENERATED] {signal.signal_type.value} at {signal.timestamp} (RSI={rsi_val:.1f}, ER={er_val:.2f}, Reason: {signal.reason})")
            if signal.signal_type in (SignalType.LONG_EXIT_SIGNAL, SignalType.SHORT_EXIT_SIGNAL):
                if self._active_record is not None:
                    self._pending_signal = signal
            else:
                if self._active_record is None:
                    self._pending_signal = signal

        # ── Periodic 10-Trade Report Check ──
        completed_count = len(self._completed_records)
        if completed_count > 0 and completed_count % 10 == 0:
            batch_num = completed_count // 10
            print(f"\n{PeriodicBatchReporter.generate_10_trade_summary(self._completed_records, batch_num)}")

    def run_live_loop(self) -> None:
        """Main polling loop listening for H1 candle closes and checking intrabar SL."""
        import MetaTrader5 as mt5

        print(f"\n[ACTIVE] Polling {SYMBOL} {TIMEFRAME_STRING} live feed. Strategy V2.6 is running in Frozen Mode...")
        print(f"[AUDIT LOG] Output destination: {self.output_csv_path}\n")

        while True:
            try:
                # 1. Check Intrabar SL touch
                self.check_intrabar_status()

                # 2. Check if new H1 bar has closed
                rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_H1, 0, 2)
                if rates is not None and len(rates) >= 2:
                    current_bar_time = datetime.fromtimestamp(rates[1]['time'])
                    closed_bar_time = datetime.fromtimestamp(rates[0]['time'])

                    if self._last_processed_candle_time is None or closed_bar_time > self._last_processed_candle_time:
                        closed_c = Candle(
                            timestamp=closed_bar_time,
                            open=float(rates[0]['open']),
                            high=float(rates[0]['high']),
                            low=float(rates[0]['low']),
                            close=float(rates[0]['close']),
                            volume=float(rates[0]['tick_volume'])
                        )
                        open_c = Candle(
                            timestamp=current_bar_time,
                            open=float(rates[1]['open']),
                            high=float(rates[1]['high']),
                            low=float(rates[1]['low']),
                            close=float(rates[1]['close']),
                            volume=float(rates[1]['tick_volume'])
                        )
                        print(f"\n--- [H1 CANDLE CLOSED: {closed_bar_time}] Close=${closed_c.close:.2f} | New Bar Open=${open_c.open:.2f} ---")
                        self.on_new_candle_close(closed_c, open_c)
                        self._last_processed_candle_time = closed_bar_time

                # Sleep 2 seconds before next tick poll
                time.sleep(2)

            except KeyboardInterrupt:
                print("\n[STOPPED] Bot terminated by user.")
                break
            except Exception as e:
                print(f"[POLLING EXCEPTION] {e}")
                time.sleep(5)


if __name__ == "__main__":
    runner = MT5PaperTradingLiveRunner()
    connected = runner.initialize_mt5()
    if connected:
        warmed = runner.warm_up_history(num_bars=150)
        if warmed:
            runner.run_live_loop()
    else:
        print("[EXIT] Could not connect to MetaTrader 5 terminal. Please ensure MT5 is open and Algo Trading is enabled.")
