"""
INDEPENDENT REFERENCE BACKTEST VALIDATOR FOR STRATEGY V2.7
Completely standalone implementation built directly from the Frozen Specification,
Authoritative Broker Snapshot, and Raw Historical Market Data.

ZERO IMPORTS FROM EXISTING V2.7 ENGINE / STATE MACHINE / SIZING / PORTFOLIO / PIPELINE.
"""

import os
import sys
import csv
import json
import math
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple


class IndependentCandle:
    __slots__ = ('timestamp', 'open', 'high', 'low', 'close', 'volume')
    def __init__(self, timestamp: datetime, open_p: float, high_p: float, low_p: float, close_p: float, volume: float = 0.0):
        self.timestamp = timestamp
        self.open = open_p
        self.high = high_p
        self.low = low_p
        self.close = close_p
        self.volume = volume


class IndependentDataLoader:
    @staticmethod
    def load_csv(filepath: str) -> List[IndependentCandle]:
        candles = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts_str = row.get("timestamp") or row.get("Date") or row.get("time") or row.get("Time")
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M"):
                    try:
                        dt = datetime.strptime(ts_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    continue

                candles.append(IndependentCandle(
                    timestamp=dt,
                    open_p=float(row.get("open") or row.get("Open")),
                    high_p=float(row.get("high") or row.get("High")),
                    low_p=float(row.get("low") or row.get("Low")),
                    close_p=float(row.get("close") or row.get("Close")),
                    volume=float(row.get("volume") or row.get("Volume") or 0.0)
                ))
        candles.sort(key=lambda c: c.timestamp)
        return candles


class IndependentIndicatorEngine:
    """Independent technical calculation engine for Wilder ATR, Kaufman ER, and Wilder RSI."""
    
    @staticmethod
    def calculate_indicators(candles: List[IndependentCandle]) -> List[Dict[str, Any]]:
        n = len(candles)
        results = [{} for _ in range(n)]
        if n < 15:
            return results

        # 1. True Range & Wilder ATR(14)
        trs = [0.0] * n
        trs[0] = candles[0].high - candles[0].low
        for i in range(1, n):
            hl = candles[i].high - candles[i].low
            hc = abs(candles[i].high - candles[i-1].close)
            lc = abs(candles[i].low - candles[i-1].close)
            trs[i] = max(hl, hc, lc)

        atrs = [None] * n
        first_atr = sum(trs[1:15]) / 14.0
        atrs[14] = first_atr
        for i in range(15, n):
            atrs[i] = (atrs[i-1] * 13.0 + trs[i]) / 14.0

        # 2. Kaufman Efficiency Ratio ER(14)
        ers = [None] * n
        for i in range(14, n):
            direction_change = abs(candles[i].close - candles[i-14].close)
            path_volatility = sum(abs(candles[j].close - candles[j-1].close) for j in range(i-13, i+1))
            ers[i] = (direction_change / path_volatility) if path_volatility > 1e-12 else 0.0

        # 3. Wilder RSI(14)
        gains = [0.0] * n
        losses = [0.0] * n
        for i in range(1, n):
            diff = candles[i].close - candles[i-1].close
            if diff > 0:
                gains[i] = diff
            else:
                losses[i] = -diff

        rsis = [None] * n
        avg_gain = sum(gains[1:15]) / 14.0
        avg_loss = sum(losses[1:15]) / 14.0

        if avg_loss == 0:
            rsis[14] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsis[14] = 100.0 - (100.0 / (1.0 + rs))

        for i in range(15, n):
            avg_gain = (avg_gain * 13.0 + gains[i]) / 14.0
            avg_loss = (avg_loss * 13.0 + losses[i]) / 14.0
            if avg_loss == 0:
                rsis[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsis[i] = 100.0 - (100.0 / (1.0 + rs))

        for i in range(n):
            results[i] = {
                "atr": atrs[i],
                "er": ers[i],
                "rsi": rsis[i],
                "close_14_ago": candles[i-14].close if i >= 14 else None
            }
        return results


class IndependentTradeRecord:
    def __init__(
        self,
        trade_id: str,
        symbol: str,
        is_pyramid: bool,
        parent_id: Optional[str],
        direction: str,
        entry_time: datetime,
        entry_price: float,
        initial_sl: float,
        current_sl: float,
        volume: float
    ):
        self.trade_id = trade_id
        self.symbol = symbol
        self.is_pyramid = is_pyramid
        self.parent_id = parent_id
        self.direction = direction
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.initial_sl = initial_sl
        self.current_sl = current_sl
        self.volume = volume
        self.state = "BASE_ACTIVE" if not is_pyramid else "PYRAMID_ACTIVE"
        self.exit_time: Optional[datetime] = None
        self.exit_price: Optional[float] = None
        self.exit_reason: Optional[str] = None
        self.realized_pnl_thb: float = 0.0


class IndependentV27Validator:
    """
    Complete Independent Reference Engine for Strategy V2.7.
    """

    def __init__(self, broker_snapshot_path: str = "d:/Kaeha/broker_metadata_snapshot.json"):
        with open(broker_snapshot_path, "r", encoding="utf-8") as f:
            snap = json.load(f)
        self.meta = snap["symbols"]
        
        self.equity_thb: float = 10000.0
        self.free_margin_thb: float = 10000.0
        self.total_deposited_thb: float = 10000.0
        self.monthly_dca_thb: float = 1000.0
        self.last_dca_month: Optional[int] = None
        
        self.active_trades: Dict[str, IndependentTradeRecord] = {}
        self.closed_trades: List[IndependentTradeRecord] = []
        self.trade_counter: int = 0
        self.dca_events: List[Dict[str, Any]] = []

        # Pullback State Machine Tracking per Asset
        # States: "IDLE", "LONG_STAGE_1_RSI_ABOVE_60", "LONG_STAGE_2_PULLBACK_UNDER_50",
        #         "SHORT_STAGE_1_RSI_BELOW_40", "SHORT_STAGE_2_PULLBACK_OVER_50"
        self.pullback_state: Dict[str, str] = {s: "IDLE" for s in self.meta.keys()}

    def apply_monthly_dca(self, current_dt: datetime) -> bool:
        if self.last_dca_month is None:
            self.last_dca_month = current_dt.month
            return False

        if current_dt.month != self.last_dca_month:
            self.equity_thb += self.monthly_dca_thb
            self.free_margin_thb += self.monthly_dca_thb
            self.total_deposited_thb += self.monthly_dca_thb
            self.last_dca_month = current_dt.month
            self.dca_events.append({
                "timestamp": current_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_thb": self.monthly_dca_thb,
                "new_equity_thb": round(self.equity_thb, 2)
            })
            return True
        return False

    def calculate_base_sizing(self, symbol: str, sl_dist_price: float) -> Tuple[bool, float, str]:
        m = self.meta[symbol]
        vol_min = m["volume_min"]
        vol_max = m["volume_max"]
        vol_step = m["volume_step"]
        tick_size = m["trade_tick_size"]
        tick_value = m["trade_tick_value"]
        margin_init = m["margin_initial"]

        target_risk_thb = self.equity_thb * 0.030
        loss_per_1_lot = (sl_dist_price / tick_size) * tick_value
        if loss_per_1_lot <= 0:
            return False, 0.0, "INVALID_LOSS_PER_LOT"

        raw_vol = target_risk_thb / loss_per_1_lot
        steps = math.floor(raw_vol / vol_step)
        quantized_vol = round(steps * vol_step, 4)

        if quantized_vol < vol_min:
            return False, 0.0, f"BELOW_MIN_VOLUME ({quantized_vol} < {vol_min})"

        quantized_vol = min(quantized_vol, vol_max)
        req_margin = quantized_vol * margin_init
        if self.free_margin_thb < (req_margin * 1.25):
            return False, 0.0, "INSUFFICIENT_MARGIN"

        return True, quantized_vol, "ACCEPTED"

    def calculate_pyramid_sizing(self, symbol: str, base_vol: float) -> Tuple[bool, float, str]:
        m = self.meta[symbol]
        vol_min = m["volume_min"]
        vol_max = m["volume_max"]
        vol_step = m["volume_step"]
        margin_init = m["margin_initial"]

        raw_vol = (2.0 / 3.0) * base_vol
        steps = math.floor(raw_vol / vol_step)
        quantized_vol = round(steps * vol_step, 4)

        if quantized_vol < vol_min:
            return False, 0.0, f"PYRAMID_BELOW_MIN_VOLUME ({quantized_vol} < {vol_min})"

        quantized_vol = min(quantized_vol, vol_max)
        req_margin = quantized_vol * margin_init
        if self.free_margin_thb < (req_margin * 1.25):
            return False, 0.0, "INSUFFICIENT_MARGIN"

        return True, quantized_vol, "ACCEPTED"

    def calculate_portfolio_heat(self, candidate_loss_thb: float = 0.0) -> float:
        total_open_loss_thb = 0.0
        for t in self.active_trades.values():
            m = self.meta[t.symbol]
            loss_dist = abs(t.entry_price - t.current_sl) if t.direction == "LONG" else abs(t.current_sl - t.entry_price)
            # If SL at BE, potential loss to stop is 0 (plus friction buffer)
            if (t.direction == "LONG" and t.current_sl >= t.entry_price) or (t.direction == "SHORT" and t.current_sl <= t.entry_price):
                loss_thb = 0.0
            else:
                loss_thb = (loss_dist / m["trade_tick_size"]) * m["trade_tick_value"] * (t.volume / 1.0)
            total_open_loss_thb += (loss_thb + 25.0)  # 25 THB standard friction buffer

        total_open_loss_thb += candidate_loss_thb
        return (total_open_loss_thb / self.equity_thb) if self.equity_thb > 0 else 1.0

    def can_accept_order(self, symbol: str, stop_price: float, entry_price: float, volume: float, is_pyramid: bool) -> Tuple[bool, str]:
        # Rule 1: Position Count Cap (Max 2 active positions)
        if len(self.active_trades) >= 2:
            return False, "POSITION_CAP_EXCEEDED"

        # Calculate Candidate Loss
        m = self.meta[symbol]
        dist = abs(entry_price - stop_price)
        if is_pyramid and stop_price == entry_price:
            cand_loss = 25.0
        else:
            cand_loss = ((dist / m["trade_tick_size"]) * m["trade_tick_value"] * (volume / 1.0)) + 25.0

        projected_heat = self.calculate_portfolio_heat(cand_loss)
        if projected_heat > 0.060:
            return False, f"HEAT_CAP_EXCEEDED ({projected_heat*100:.2f}% > 6.0%)"

        return True, "ACCEPTED"

    def close_trade(self, trade: IndependentTradeRecord, exit_time: datetime, exit_price: float, reason: str):
        m = self.meta[trade.symbol]
        price_diff = (exit_price - trade.entry_price) if trade.direction == "LONG" else (trade.entry_price - exit_price)
        gross_pnl = (price_diff / m["trade_tick_size"]) * m["trade_tick_value"] * (trade.volume / 1.0)
        
        # Friction deduction (spread + slippage + comm) ~25 THB per 0.01 lot
        friction = 25.0 * (trade.volume / 0.01) * 0.5  # Standard realistic execution drag
        net_pnl = gross_pnl - friction

        trade.exit_time = exit_time
        trade.exit_price = exit_price
        trade.exit_reason = reason
        trade.realized_pnl_thb = net_pnl

        self.equity_thb += net_pnl
        req_margin = trade.volume * m["margin_initial"]
        self.free_margin_thb += (req_margin + net_pnl)

        self.closed_trades.append(trade)
        del self.active_trades[trade.trade_id]


def run_independent_validation_backtest(
    start_year: int = 2020,
    end_year: int = 2025
) -> Dict[str, Any]:
    """
    Executes independent multi-asset reference backtest.
    """
    # 1. Load Data
    data_files = {
        "XAUUSD": f"d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_{start_year}_{end_year}.csv" if start_year == 2020 else f"d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2014_2025.csv",
        "USDJPY": f"d:/Kaeha/rsi_trend_pullback/data/usdjpy_h1_{start_year}_{end_year}.csv",
        "GBPUSD": f"d:/Kaeha/rsi_trend_pullback/data/gbpusd_h1_{start_year}_{end_year}.csv",
        "US500":  f"d:/Kaeha/rsi_trend_pullback/data/us500_h1_{start_year}_{end_year}.csv",
        "BTCUSD": f"d:/Kaeha/rsi_trend_pullback/data/btcusd_h1_{start_year}_{end_year}.csv",
    }

    raw_candles = {}
    indicators_by_sym = {}
    for sym, path in data_files.items():
        candles = IndependentDataLoader.load_csv(path)
        if start_year != 2020:
            # Filter OOS range 2014-2019
            candles = [c for c in candles if start_year <= c.timestamp.year <= end_year]
        raw_candles[sym] = candles
        indicators_by_sym[sym] = IndependentIndicatorEngine.calculate_indicators(candles)

    # 2. Synchronize timeline
    timeline_set = set()
    candles_map = defaultdict(dict)
    indicators_map = defaultdict(dict)

    for sym, candles in raw_candles.items():
        inds = indicators_by_sym[sym]
        for idx, c in enumerate(candles):
            timeline_set.add(c.timestamp)
            candles_map[c.timestamp][sym] = c
            indicators_map[c.timestamp][sym] = inds[idx]

    sorted_timeline = sorted(list(timeline_set))

    validator = IndependentV27Validator()

    # Track Unit NAV & Drawdown
    unit_nav = 100.00
    peak_nav = 100.00
    max_dd_pct = 0.0

    for ts in sorted_timeline:
        # Step 1: DCA Inflow
        validator.apply_monthly_dca(ts)
        eq_before = validator.equity_thb
        closed_before = len(validator.closed_trades)

        curr_candles = candles_map[ts]
        curr_inds = indicators_map[ts]

        # Step 2: Manage Open Positions (Intrabar SL & Pyramiding)
        for tid, trade in list(validator.active_trades.items()):
            sym = trade.symbol
            if sym not in curr_candles:
                continue
            candle = curr_candles[sym]

            # Stop Loss Check
            is_stopped = False
            sl_exit = trade.current_sl
            if trade.direction == "LONG":
                if candle.low <= trade.current_sl:
                    is_stopped = True
                    sl_exit = min(trade.current_sl, candle.open) if candle.open < trade.current_sl else trade.current_sl
            else:
                if candle.high >= trade.current_sl:
                    is_stopped = True
                    sl_exit = max(trade.current_sl, candle.open) if candle.open > trade.current_sl else trade.current_sl

            if is_stopped:
                validator.close_trade(trade, ts, sl_exit, "STOP_LOSS_TOUCH")
                continue

            # Pyramiding Check (+1.5R)
            if not trade.is_pyramid and trade.state == "BASE_ACTIVE":
                d_dist = abs(trade.entry_price - trade.initial_sl)
                target_15r = trade.entry_price + (1.5 * d_dist) if trade.direction == "LONG" else trade.entry_price - (1.5 * d_dist)
                is_hit = (candle.high >= target_15r) if trade.direction == "LONG" else (candle.low <= target_15r)
                if is_hit:
                    trade.current_sl = trade.entry_price
                    trade.state = "PYRAMID_QUALIFIED"
                    ok_size, pyr_vol, _ = validator.calculate_pyramid_sizing(sym, trade.volume)
                    if ok_size:
                        can_acc, _ = validator.can_accept_order(sym, trade.entry_price, target_15r, pyr_vol, is_pyramid=True)
                        if can_acc:
                            validator.trade_counter += 1
                            t2_id = f"{sym}_PYR_{validator.trade_counter}"
                            t2 = IndependentTradeRecord(
                                t2_id, sym, True, tid, trade.direction, ts,
                                target_15r, trade.entry_price, trade.entry_price, pyr_vol
                            )
                            t2.state = "PYRAMID_ACTIVE"
                            validator.active_trades[t2_id] = t2
                            trade.state = "PYRAMID_ACTIVE"

        # Step 3: Check Closed Bar Signals & Thesis Exits
        raw_signals = []
        for sym, c in curr_candles.items():
            ind = curr_inds[sym]
            rsi = ind.get("rsi")
            er = ind.get("er")
            atr = ind.get("atr")
            close_14 = ind.get("close_14_ago")

            if rsi is None or er is None or atr is None or close_14 is None:
                continue

            # Thesis Exit Check
            for tid, tr in list(validator.active_trades.items()):
                if tr.symbol == sym:
                    if (tr.direction == "LONG" and rsi < 40.0) or (tr.direction == "SHORT" and rsi > 60.0):
                        validator.close_trade(tr, ts, c.close, "THESIS_EXIT")

            # Entry Logic (State Machine)
            has_active = any(t.symbol == sym for t in validator.active_trades.values())
            
            # Economic Filter: ATR / Friction >= 5.0
            roundturn_friction = validator.meta[sym]["trade_tick_size"] * 25.0
            if (atr / roundturn_friction) < 5.0:
                continue

            # Long Pullback State Machine
            if er > 0.40 and c.close > close_14:
                curr_st = validator.pullback_state[sym]
                if rsi > 60.0:
                    validator.pullback_state[sym] = "LONG_STAGE_1_RSI_ABOVE_60"
                elif curr_st == "LONG_STAGE_1_RSI_ABOVE_60" and rsi < 50.0 and rsi > 40.0:
                    validator.pullback_state[sym] = "LONG_STAGE_2_PULLBACK_UNDER_50"
                elif curr_st == "LONG_STAGE_2_PULLBACK_UNDER_50" and rsi > 50.0:
                    validator.pullback_state[sym] = "IDLE"  # Reset
                    if not has_active:
                        sl_dist = 2.5 * atr
                        stop_p = c.close - sl_dist
                        ok_sz, vol, _ = validator.calculate_base_sizing(sym, sl_dist)
                        if ok_sz:
                            raw_signals.append({
                                "symbol": sym, "direction": "LONG", "entry_price": c.close,
                                "stop_price": stop_p, "volume": vol, "er_14": er,
                                "spread_atr_ratio": roundturn_friction / atr
                            })

            # Short Pullback State Machine
            elif er > 0.40 and c.close < close_14:
                curr_st = validator.pullback_state[sym]
                if rsi < 40.0:
                    validator.pullback_state[sym] = "SHORT_STAGE_1_RSI_BELOW_40"
                elif curr_st == "SHORT_STAGE_1_RSI_BELOW_40" and rsi > 50.0 and rsi < 60.0:
                    validator.pullback_state[sym] = "SHORT_STAGE_2_PULLBACK_OVER_50"
                elif curr_st == "SHORT_STAGE_2_PULLBACK_OVER_50" and rsi < 50.0:
                    validator.pullback_state[sym] = "IDLE"  # Reset
                    if not has_active:
                        sl_dist = 2.5 * atr
                        stop_p = c.close + sl_dist
                        ok_sz, vol, _ = validator.calculate_base_sizing(sym, sl_dist)
                        if ok_sz:
                            raw_signals.append({
                                "symbol": sym, "direction": "SHORT", "entry_price": c.close,
                                "stop_price": stop_p, "volume": vol, "er_14": er,
                                "spread_atr_ratio": roundturn_friction / atr
                            })

        # Step 4: Collision Resolution (Highest ER14 -> Lowest Spread/ATR -> Canonical Order)
        if raw_signals:
            # Canonical order: BTCUSD, GBPUSD, US500, USDJPY, XAUUSD
            canonical_rank = {"BTCUSD": 1, "GBPUSD": 2, "US500": 3, "USDJPY": 4, "XAUUSD": 5}
            raw_signals.sort(key=lambda s: (-round(s["er_14"], 4), round(s["spread_atr_ratio"], 4), canonical_rank.get(s["symbol"], 99)))

            for sig in raw_signals:
                can_acc, reason = validator.can_accept_order(
                    sig["symbol"], sig["stop_price"], sig["entry_price"], sig["volume"], is_pyramid=False
                )
                if can_acc:
                    validator.trade_counter += 1
                    t_id = f"{sig['symbol']}_BASE_{validator.trade_counter}"
                    t_rec = IndependentTradeRecord(
                        t_id, sig["symbol"], False, None, sig["direction"], ts,
                        sig["entry_price"], sig["stop_price"], sig["stop_price"], sig["volume"]
                    )
                    validator.active_trades[t_id] = t_rec

        # Step 5: Update NAV
        if len(validator.closed_trades) > closed_before:
            step_pnl = sum(t.realized_pnl_thb for t in validator.closed_trades[closed_before:])
            step_ret = step_pnl / eq_before if eq_before > 0 else 0.0
            unit_nav = unit_nav * (1.0 + step_ret)
            if unit_nav > peak_nav:
                peak_nav = unit_nav
            dd = (peak_nav - unit_nav) / peak_nav * 100.0
            if dd > max_dd_pct:
                max_dd_pct = dd

    # Summary Statistics
    closed = validator.closed_trades
    n_trades = len(closed)
    wins = [t for t in closed if t.realized_pnl_thb > 0]
    losses = [t for t in closed if t.realized_pnl_thb < 0]
    gross_win = sum(t.realized_pnl_thb for t in wins)
    gross_loss = abs(sum(t.realized_pnl_thb for t in losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
    net_pnl = sum(t.realized_pnl_thb for t in closed)
    win_rate = (len(wins) / n_trades * 100.0) if n_trades > 0 else 0.0
    expectancy = (net_pnl / n_trades) if n_trades > 0 else 0.0

    # Consecutive losses
    max_consec = 0
    curr_consec = 0
    for t in closed:
        if t.realized_pnl_thb < 0:
            curr_consec += 1
            if curr_consec > max_consec:
                max_consec = curr_consec
        else:
            curr_consec = 0

    # Base vs Pyramid
    base_trades = [t for t in closed if not t.is_pyramid]
    pyr_trades = [t for t in closed if t.is_pyramid]

    # Asset breakdown
    asset_breakdown = defaultdict(lambda: {"trades": 0, "wins": 0, "pnl": 0.0})
    for t in closed:
        asset_breakdown[t.symbol]["trades"] += 1
        if t.realized_pnl_thb > 0:
            asset_breakdown[t.symbol]["wins"] += 1
        asset_breakdown[t.symbol]["pnl"] += t.realized_pnl_thb

    # Yearly breakdown
    yearly_breakdown = defaultdict(lambda: {"trades": 0, "pnl": 0.0})
    for t in closed:
        yr = t.exit_time.year if t.exit_time else 2020
        yearly_breakdown[yr]["trades"] += 1
        yearly_breakdown[yr]["pnl"] += t.realized_pnl_thb

    return {
        "total_trades": n_trades,
        "win_rate_pct": round(win_rate, 2),
        "profit_factor": round(pf, 2),
        "net_trading_pnl_thb": round(net_pnl, 2),
        "ending_equity_thb": round(validator.equity_thb, 2),
        "total_deposited_capital_thb": round(validator.total_deposited_thb, 2),
        "profit_to_capital_ratio_pct": round((net_pnl / validator.total_deposited_thb) * 100.0, 2),
        "true_twr_max_dd_pct": round(max_dd_pct, 2),
        "max_consecutive_losses": max_consec,
        "expectancy_thb": round(expectancy, 2),
        "base_trades_count": len(base_trades),
        "pyr_trades_count": len(pyr_trades),
        "base_pnl_thb": round(sum(t.realized_pnl_thb for t in base_trades), 2),
        "pyr_pnl_thb": round(sum(t.realized_pnl_thb for t in pyr_trades), 2),
        "dca_events_count": len(validator.dca_events),
        "asset_breakdown": dict(asset_breakdown),
        "yearly_breakdown": dict(yearly_breakdown),
        "trades_list": closed
    }


def export_independent_validation_artifacts():
    res = run_independent_validation_backtest(2020, 2025)
    
    # 1. Export v27_independent_trades.csv
    trades_csv_path = "d:/Kaeha/v27_independent_trades.csv"
    with open(trades_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "trade_id", "symbol", "is_pyramid", "parent_id", "direction",
            "entry_time", "entry_price", "initial_sl", "current_sl",
            "volume", "exit_time", "exit_price", "exit_reason", "realized_pnl_thb"
        ])
        for t in res["trades_list"]:
            writer.writerow([
                t.trade_id, t.symbol, t.is_pyramid, t.parent_id, t.direction,
                t.entry_time.strftime("%Y-%m-%d %H:%M:%S") if t.entry_time else "",
                t.entry_price, t.initial_sl, t.current_sl, t.volume,
                t.exit_time.strftime("%Y-%m-%d %H:%M:%S") if t.exit_time else "",
                t.exit_price, t.exit_reason, round(t.realized_pnl_thb, 2)
            ])

    # 2. Export v27_independent_summary.json
    summary_json_path = "d:/Kaeha/v27_independent_summary.json"
    summary_data = {
        "engine": "Independent Reference Validator (V2.7)",
        "timestamp": datetime.now().isoformat(),
        "total_trades": res["total_trades"],
        "win_rate_pct": res["win_rate_pct"],
        "profit_factor": res["profit_factor"],
        "net_trading_pnl_thb": res["net_trading_pnl_thb"],
        "ending_equity_thb": res["ending_equity_thb"],
        "total_deposited_capital_thb": res["total_deposited_capital_thb"],
        "profit_to_capital_ratio_pct": res["profit_to_capital_ratio_pct"],
        "true_twr_max_dd_pct": res["true_twr_max_dd_pct"],
        "max_consecutive_losses": res["max_consecutive_losses"],
        "expectancy_thb": res["expectancy_thb"],
        "base_trades_count": res["base_trades_count"],
        "pyr_trades_count": res["pyr_trades_count"],
        "base_pnl_thb": res["base_pnl_thb"],
        "pyr_pnl_thb": res["pyr_pnl_thb"],
        "dca_events_count": res["dca_events_count"],
        "asset_breakdown": {k: {"trades": v["trades"], "wins": v["wins"], "pnl": round(v["pnl"], 2)} for k, v in res["asset_breakdown"].items()},
        "yearly_breakdown": {k: {"trades": v["trades"], "pnl": round(v["pnl"], 2)} for k, v in res["yearly_breakdown"].items()}
    }
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=4)

    return res


if __name__ == "__main__":
    res = export_independent_validation_artifacts()
    print("=" * 95)
    print("INDEPENDENT V2.7 REFERENCE VALIDATION RUN COMPLETED")
    print(f"Total Trades:       {res['total_trades']}")
    print(f"Win Rate:           {res['win_rate_pct']:.1f}%")
    print(f"Profit Factor:      {res['profit_factor']:.2f}")
    print(f"Net Trading P&L:    {res['net_trading_pnl_thb']:+,.2f} THB")
    print(f"Ending Equity:      {res['ending_equity_thb']:,.2f} THB (Total Deposited: {res['total_deposited_capital_thb']:,.0f} THB)")
    print(f"True TWR Max DD:    -{res['true_twr_max_dd_pct']:.2f}%")
    print(f"Base vs Pyramid:    Base = {res['base_pnl_thb']:+,.2f} THB | Pyramid = {res['pyr_pnl_thb']:+,.2f} THB")
    print(f"DCA Inflow Events:  {res['dca_events_count']} deposits")
    print("=" * 95)
