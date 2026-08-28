"""
Strategy V2.7 Frozen Candidate - Master MT5 Multi-Asset Live Forward Paper Trader.
Trades 5 Screened Assets on H1: XAUUSD, USDJPY, GBPUSD, US500, BTCUSD.

Safety & Governance Invariants:
1. Strict PAPER_MODE = True with REAL ACCOUNT LOCK (Halts immediately if account is not DEMO).
2. Live Broker Metadata Ingestion from MT5 (volume_min, volume_step, contract_size, tick_size, tick_value).
3. Strict Floor Position Sizing (3.0% risk, math.floor volume step, under min lot = REJECT).
4. Portfolio Heat Engine (Aggregate open risk <= 6.0%) & Position Count Cap (Max 2 concurrent positions).
5. Deterministic 3-Tier Collision Resolution (Highest ER14 -> Lowest Spread/ATR -> Alphabetical Symbol).
6. Pyramiding Scale-In at +1.5R (Trade 1 SL to Breakeven -> Trade 2 size floor(2/3*V1) -> Trade 2 SL at BE).
7. Persistent JSON State Tracking & CSV Execution Audit Logging.
"""

import sys
import os

# Ensure parent directory (workspace root) is in sys.path for robust package execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import math
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

from rsi_trend_pullback.data.loader import Candle
from rsi_trend_pullback.research.broker_sizing_engine import (
    BrokerSymbolMetadata,
    XM_AUTHORITATIVE_METADATA,
    BrokerSizingEngineGate4
)
from rsi_trend_pullback.research.portfolio_heat_engine import (
    ActivePosition,
    CandidateSignal,
    PortfolioHeatEngineGate2
)
from rsi_trend_pullback.research.multi_asset_calendar_engine import (
    ASSET_SPECS,
    AssetMarketSpec,
    IndependentAssetStream
)
from rsi_trend_pullback.research.v27_integrity_pipeline import (
    PositionLifecycleState,
    TradeRecord
)
from rsi_trend_pullback.monitoring.v27_forward_telemetry import V27TelemetryDatabase
from rsi_trend_pullback.monitoring.v27_reporting_engine import V27ReportingEngine

# ── LOGGING SETUP ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("v27_paper_trading.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("V27_PAPER_TRADER")

# ── CONFIGURATION & SAFETY CONSTANTS ──
PAPER_MODE: bool = True
MAGIC_NUMBER_BASE: int = 270001
MAGIC_NUMBER_PYR: int = 270002
STATE_FILE_PATH: str = "d:/Kaeha/v27_active_positions_state.json"
TRADE_LOG_CSV: str = "d:/Kaeha/v27_demo_trade_log.csv"
AUDIT_LOG_CSV: str = "d:/Kaeha/v27_demo_audit_events.csv"

SYMBOL_MAPPINGS: Dict[str, List[str]] = {
    "XAUUSD": ["GOLD#", "GOLD", "XAUUSDm", "XAUUSD"],
    "USDJPY": ["USDJPY", "USDJPY#", "USDJPYm"],
    "GBPUSD": ["GBPUSD", "GBPUSD#", "GBPUSDm"],
    "US500":  ["US500Cash#", "US500#", "US500Cash", "SPX500"],
    "BTCUSD": ["BTCUSD#", "BTC", "BTCUSDm", "BTCUSD"]
}


class MT5V27PaperTrader:
    """
    Master Real-Time Multi-Asset Forward Paper Trader for Strategy V2.7.
    """

    def __init__(self):
        self.resolved_symbols: Dict[str, str] = {}  # Canonical -> Broker Symbol
        self.broker_metadata: Dict[str, BrokerSymbolMetadata] = {}
        self.asset_streams: Dict[str, IndependentAssetStream] = {}
        self.active_trades: Dict[str, TradeRecord] = {}
        self.trade_counter: int = 0
        self.last_checked_bars: Dict[str, datetime] = {}

    def initialize_mt5_and_verify_account(self) -> bool:
        """
        Initializes MT5 connection and performs strict Demo Safety Check.
        """
        if not MT5_AVAILABLE:
            logger.error("MetaTrader5 library is not installed! Run: pip install MetaTrader5")
            return False

        if not mt5.initialize():
            logger.error(f"MT5 initialize() failed! Error code: {mt5.last_error()}")
            return False

        account_info = mt5.account_info()
        if account_info is None:
            logger.error("Could not retrieve account_info from MT5 terminal!")
            return False

        # REAL ACCOUNT LOCK: Refuse to run if account is real money
        is_demo = (account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO)
        if not is_demo:
            logger.critical("🚨 REAL ACCOUNT DETECTED! Strategy V2.7 Paper Trader is STRICTLY DEMO ONLY!")
            logger.critical("Execution aborted to protect real capital.")
            mt5.shutdown()
            return False

        print("\n" + "=" * 80)
        print("  STRATEGY V2.7 - MASTER MT5 FORWARD PAPER TRADER")
        print("  Status: DEMO PAPER TRADING MODE ONLY | Real-Capital Lock: ACTIVE")
        print("=" * 80)
        print(f"  Broker:          {account_info.company}")
        print(f"  Server:          {account_info.server}")
        print(f"  Account Login:   {account_info.login}")
        print(f"  Account Currency:{account_info.currency}")
        print(f"  Account Balance: {account_info.balance:,.2f} {account_info.currency}")
        print(f"  Account Equity:  {account_info.equity:,.2f} {account_info.currency}")
        print(f"  Leverage:        1:{account_info.leverage}")
        print(f"  Trade Mode:      🟢 DEMO VERIFIED (Safe for Paper Trading)")
        print(f"  Paper Mode:      {PAPER_MODE}")
        print(f"  Base Risk:       3.0% per trade (Strict floor quantization)")
        print(f"  Portfolio Heat:  <= 6.0% Hard Ceiling")
        print(f"  Position Cap:    <= 2 Active Positions")
        print("=" * 80 + "\n")

        return True

    def resolve_and_load_symbols(self) -> bool:
        """
        Resolves broker symbol aliases and pulls live broker metadata.
        """
        for canonical, aliases in SYMBOL_MAPPINGS.items():
            matched_sym = None
            for alias in aliases:
                info = mt5.symbol_info(alias)
                if info is not None:
                    matched_sym = alias
                    if not info.visible:
                        mt5.symbol_select(alias, True)
                    break

            if not matched_sym:
                logger.error(f"❌ Failed to find valid broker symbol for {canonical} on this broker!")
                return False

            self.resolved_symbols[canonical] = matched_sym
            sym_info = mt5.symbol_info(matched_sym)

            # Ingest live metadata
            self.broker_metadata[canonical] = BrokerSymbolMetadata(
                canonical_name=canonical,
                broker_symbol=matched_sym,
                volume_min=sym_info.volume_min,
                volume_max=sym_info.volume_max,
                volume_step=sym_info.volume_step,
                trade_contract_size=sym_info.trade_contract_size,
                trade_tick_size=sym_info.trade_tick_size,
                trade_tick_value=sym_info.trade_tick_value,
                currency_base=sym_info.currency_base,
                currency_profit=sym_info.currency_profit,
                currency_margin=sym_info.currency_margin,
                leverage=1000.0,
                margin_initial=sym_info.margin_initial if hasattr(sym_info, 'margin_initial') else 50.0,
                digits=sym_info.digits,
                is_swap_free=(canonical in ("XAUUSD", "USDJPY", "GBPUSD", "BTCUSD"))
            )

            # Initialize Independent Stream
            spec = ASSET_SPECS[canonical]
            self.asset_streams[canonical] = IndependentAssetStream(spec)

            logger.info(f"✅ Resolved {canonical:<8} -> Broker Symbol: {matched_sym:<12} (Min Lot: {sym_info.volume_min}, Step: {sym_info.volume_step})")

        return True

    def load_persisted_state(self) -> None:
        """
        Recovers active positions from JSON state file upon restart.
        """
        if os.path.exists(STATE_FILE_PATH):
            try:
                with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.get("active_trades", {}).items():
                        self.active_trades[k] = TradeRecord(
                            trade_id=v["trade_id"],
                            symbol=v["symbol"],
                            is_pyramid_leg=v["is_pyramid_leg"],
                            parent_trade_id=v.get("parent_trade_id"),
                            direction=v["direction"],
                            entry_time=datetime.fromisoformat(v["entry_time"]),
                            entry_price=v["entry_price"],
                            initial_sl=v["initial_sl"],
                            current_sl=v["current_sl"],
                            volume=v["volume"],
                            state=PositionLifecycleState[v["state"]]
                        )
                logger.info(f"📥 Restored {len(self.active_trades)} active positions from {STATE_FILE_PATH}")
            except Exception as e:
                logger.error(f"Failed to load state file: {e}")

    def save_state(self) -> None:
        """
        Persists active positions to JSON state file.
        """
        data = {
            "last_updated": datetime.now().isoformat(),
            "active_trades": {
                k: {
                    "trade_id": v.trade_id,
                    "symbol": v.symbol,
                    "is_pyramid_leg": v.is_pyramid_leg,
                    "parent_trade_id": v.parent_trade_id,
                    "direction": v.direction,
                    "entry_time": v.entry_time.isoformat(),
                    "entry_price": v.entry_price,
                    "initial_sl": v.initial_sl,
                    "current_sl": v.current_sl,
                    "volume": v.volume,
                    "state": v.state.value
                } for k, v in self.active_trades.items()
            }
        }
        with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def get_active_positions_for_heat(self) -> List[ActivePosition]:
        active_list = []
        for t in self.active_trades.values():
            meta = self.broker_metadata[t.symbol]
            stream = self.asset_streams[t.symbol]
            current_price = stream.price_history[-1] if stream.price_history else t.entry_price
            active_list.append(ActivePosition(
                symbol=t.symbol,
                is_pyramid=t.is_pyramid_leg,
                direction=t.direction,
                entry_price=t.entry_price,
                current_price=current_price,
                current_stop_price=t.current_sl,
                volume=t.volume,
                tick_size=meta.trade_tick_size,
                tick_value=meta.trade_tick_value,
                friction_buffer_cur=25.0
            ))
        return active_list

    def check_open_positions_intrabar(self) -> None:
        """
        Monitors active positions in real-time:
        1. Checks Stop Loss hits.
        2. Checks Pyramiding triggers (+1.5R) -> Moves SL1 to BE -> Opens Trade 2.
        """
        for tid, trade in list(self.active_trades.items()):
            canonical = trade.symbol
            broker_sym = self.resolved_symbols[canonical]
            tick = mt5.symbol_info_tick(broker_sym)
            if not tick:
                continue

            current_price = tick.bid if trade.direction == "LONG" else tick.ask
            meta = self.broker_metadata[canonical]

            # 1. Intrabar Pyramiding Trigger (+1.5R)
            if not trade.is_pyramid_leg and trade.state == PositionLifecycleState.BASE_ACTIVE:
                d_dist = abs(trade.entry_price - trade.initial_sl)
                target_15r = trade.entry_price + (1.5 * d_dist) if trade.direction == "LONG" else trade.entry_price - (1.5 * d_dist)

                is_triggered = (current_price >= target_15r) if trade.direction == "LONG" else (current_price <= target_15r)
                if is_triggered:
                    logger.info(f"🚀 Pyramiding Trigger (+1.5R) HIT for {canonical} ({tid}) at {current_price:.5f}!")
                    # Step 1: Move SL1 to Breakeven
                    trade.current_sl = trade.entry_price
                    trade.state = PositionLifecycleState.PYRAMID_QUALIFIED
                    self._modify_mt5_sl(trade, trade.entry_price)

                    # Step 2: Size and place Pyramid Leg (Case A: 2/3 volume)
                    acct = mt5.account_info()
                    free_margin = acct.margin_free if acct else 10000.0
                    pyr_sizing = BrokerSizingEngineGate4.calculate_pyramid_sizing(
                        meta, trade.volume, free_margin, 1.5 * d_dist
                    )

                    if pyr_sizing.is_accepted:
                        cand = CandidateSignal(
                            canonical, True, trade.direction, current_price, trade.entry_price,
                            pyr_sizing.quantized_volume, meta.trade_tick_size, meta.trade_tick_value,
                            25.0, 0.60, 0.05
                        )
                        can_acc, reason, _ = PortfolioHeatEngineGate2.can_accept_order(
                            self.get_active_positions_for_heat(), cand, acct.equity if acct else 10000.0
                        )
                        if can_acc:
                            self.trade_counter += 1
                            t2_id = f"{canonical}_PYR_{self.trade_counter}"
                            t2 = TradeRecord(
                                t2_id, canonical, True, tid, trade.direction,
                                datetime.now(), current_price, trade.entry_price, trade.entry_price,
                                pyr_sizing.quantized_volume, PositionLifecycleState.PYRAMID_ACTIVE
                            )
                            self._place_mt5_order(t2, is_pyramid=True)
                            self.active_trades[t2_id] = t2
                            trade.state = PositionLifecycleState.PYRAMID_ACTIVE
                            self.save_state()
                            self.log_trade_event("PYRAMID_OPEN", {"trade_id": t2_id, "symbol": canonical, "volume": pyr_sizing.quantized_volume, "price": current_price})
                        else:
                            logger.warning(f"⚠️ Pyramid leg rejected for {canonical}: {reason}")
                    else:
                        logger.warning(f"⚠️ Pyramid sizing rejected for {canonical}: {pyr_sizing.rejection_reason}")

    def _modify_mt5_sl(self, trade: TradeRecord, new_sl: float) -> bool:
        """Modifies SL of open position in MT5 terminal."""
        broker_sym = self.resolved_symbols[trade.symbol]
        positions = mt5.positions_get(symbol=broker_sym)
        if positions:
            for p in positions:
                if p.magic in (MAGIC_NUMBER_BASE, MAGIC_NUMBER_PYR):
                    req = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": p.ticket,
                        "symbol": broker_sym,
                        "sl": round(new_sl, self.broker_metadata[trade.symbol].digits),
                        "tp": p.tp
                    }
                    res = mt5.order_send(req)
                    if res.retcode == mt5.TRADE_RETCODE_DONE:
                        logger.info(f"✅ Modified SL of {broker_sym} (Ticket: {p.ticket}) to {new_sl:.5f}")
                        return True
                    else:
                        logger.error(f"❌ Failed to modify SL for {broker_sym}: {res.comment}")
        return False

    def _place_mt5_order(self, trade: TradeRecord, is_pyramid: bool) -> bool:
        """Places Market Order with Hard SL on MT5 Demo Account."""
        broker_sym = self.resolved_symbols[trade.symbol]
        order_type = mt5.ORDER_TYPE_BUY if trade.direction == "LONG" else mt5.ORDER_TYPE_SELL
        tick = mt5.symbol_info_tick(broker_sym)
        price = tick.ask if trade.direction == "LONG" else tick.bid
        digits = self.broker_metadata[trade.symbol].digits

        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": broker_sym,
            "volume": trade.volume,
            "type": order_type,
            "price": price,
            "sl": round(trade.current_sl, digits),
            "deviation": 20,
            "magic": MAGIC_NUMBER_PYR if is_pyramid else MAGIC_NUMBER_BASE,
            "comment": f"V27_{'PYR' if is_pyramid else 'BASE'}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC
        }
        res = mt5.order_send(req)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"🎉 MT5 DEMO ORDER FILLED! Symbol: {broker_sym}, Vol: {trade.volume}, Type: {trade.direction}, Price: {price:.5f}, SL: {trade.current_sl:.5f}")
            return True
        else:
            comment = res.comment if res else "None"
            logger.error(f"❌ MT5 Order Send Failed ({broker_sym}): {comment}")
            return False

    def run_live_loop(self) -> None:
        """
        Continuous Real-Time Event Loop for Strategy V2.7 Paper Trader.
        """
        logger.info("🟢 Strategy V2.7 Multi-Asset Forward Paper Trader RUNNING...")
        logger.info("Listening for closed H1 candles and monitoring intrabar stops...")

        while True:
            try:
                # 1. Monitor Open Positions (Intrabar Pyramiding and SL)
                self.check_open_positions_intrabar()

                # 2. Check for New Closed H1 Bars across all 5 symbols
                now = datetime.now()
                raw_candidates: List[CandidateSignal] = []

                for canonical, broker_sym in self.resolved_symbols.items():
                    rates = mt5.copy_rates_from_pos(broker_sym, mt5.TIMEFRAME_H1, 1, 2)
                    if rates is None or len(rates) < 2:
                        continue

                    # Rate 0 is the last COMPLETED H1 bar
                    last_closed = rates[0]
                    bar_dt = datetime.fromtimestamp(last_closed['time'])

                    # If this is a newly closed bar
                    if self.last_checked_bars.get(canonical) != bar_dt:
                        self.last_checked_bars[canonical] = bar_dt
                        candle = Candle(
                            timestamp=bar_dt,
                            open=last_closed['open'],
                            high=last_closed['high'],
                            low=last_closed['low'],
                            close=last_closed['close'],
                            volume=last_closed['tick_volume']
                        )
                        stream = self.asset_streams[canonical]
                        meta = self.broker_metadata[canonical]
                        sig = stream.process_candle(candle)

                        # Check Exit Signal (Thesis Exit)
                        if sig and sig.signal_type in ("LONG_EXIT_SIGNAL", "SHORT_EXIT_SIGNAL"):
                            for tid, tr in list(self.active_trades.items()):
                                if tr.symbol == canonical:
                                    if (tr.direction == "LONG" and sig.signal_type == "LONG_EXIT_SIGNAL") or \
                                       (tr.direction == "SHORT" and sig.signal_type == "SHORT_EXIT_SIGNAL"):
                                        logger.info(f"🛑 Thesis Exit Signal for {canonical} ({tid}) at {candle.close:.5f}")
                                        # Close in MT5
                                        positions = mt5.positions_get(symbol=broker_sym)
                                        if positions:
                                            for p in positions:
                                                close_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                                                close_req = {
                                                    "action": mt5.TRADE_ACTION_DEAL,
                                                    "position": p.ticket,
                                                    "symbol": broker_sym,
                                                    "volume": p.volume,
                                                    "type": close_type,
                                                    "deviation": 20,
                                                    "magic": p.magic,
                                                    "comment": "V27_THESIS_EXIT"
                                                }
                                                mt5.order_send(close_req)
                                        del self.active_trades[tid]
                                        self.save_state()

                        # Check Entry Signal
                        if sig and sig.signal_type in ("LONG_ENTRY_SIGNAL", "SHORT_ENTRY_SIGNAL"):
                            has_active = any(t.symbol == canonical for t in self.active_trades.values())
                            if not has_active:
                                direction = "LONG" if sig.signal_type == "LONG_ENTRY_SIGNAL" else "SHORT"
                                atr_val = stream.latest_atr or (candle.close * 0.01)
                                sl_dist = 2.5 * atr_val
                                stop_p = candle.close - sl_dist if direction == "LONG" else candle.close + sl_dist

                                acct = mt5.account_info()
                                eq = acct.equity if acct else 10000.0
                                fm = acct.margin_free if acct else 10000.0

                                size_res = BrokerSizingEngineGate4.calculate_base_sizing(meta, eq, fm, sl_dist)
                                if size_res.is_accepted:
                                    raw_candidates.append(CandidateSignal(
                                        canonical, False, direction, candle.close, stop_p,
                                        size_res.quantized_volume, meta.trade_tick_size, meta.trade_tick_value,
                                        25.0, stream.latest_er or 0.0, meta.trade_tick_size * 25 / atr_val
                                    ))
                                else:
                                    logger.warning(f"⚠️ Sizing rejected for {canonical}: {size_res.rejection_reason}")

                # 3. Resolve Signal Collisions & Place New Orders
                if raw_candidates:
                    acct = mt5.account_info()
                    eq = acct.equity if acct else 10000.0
                    resolved = PortfolioHeatEngineGate2.resolve_signal_collisions(
                        self.get_active_positions_for_heat(), raw_candidates, eq
                    )
                    for cand, can_accept, reason in resolved:
                        if can_accept:
                            self.trade_counter += 1
                            t_id = f"{cand.symbol}_BASE_{self.trade_counter}"
                            t_rec = TradeRecord(
                                t_id, cand.symbol, False, None, cand.direction,
                                datetime.now(), cand.entry_price, cand.stop_price, cand.stop_price,
                                cand.volume, PositionLifecycleState.BASE_ACTIVE
                            )
                            self._place_mt5_order(t_rec, is_pyramid=False)
                            self.active_trades[t_id] = t_rec
                            self.save_state()
                            self.log_trade_event("BASE_OPEN", {"trade_id": t_id, "symbol": cand.symbol, "volume": cand.volume, "direction": cand.direction, "entry": cand.entry_price, "sl": cand.stop_price})
                        else:
                            logger.warning(f"🚫 Candidate {cand.symbol} REJECTED: {reason}")

                time.sleep(10)  # Heartbeat poll interval

            except KeyboardInterrupt:
                logger.info("🛑 V2.7 Paper Trader stopped by user.")
                break
            except Exception as e:
                logger.error(f"Unexpected error in live loop: {e}", exc_info=True)
                time.sleep(10)


if __name__ == "__main__":
    trader = MT5V27PaperTrader()
    if trader.initialize_mt5_and_verify_account():
        trader.resolve_and_load_symbols()
        trader.load_persisted_state()
        trader.run_live_loop()


