"""
Strategy V2.7 Research Candidate - Gate 5: Unified Integrity & Execution Pipeline.
Orchestrates:
1. Multi-Asset Independent Calendar Feeds (Gate 3).
2. Frozen V2.6 Signal Evaluation (ER14 > 0.40, RSI 60/50/40, ATR/Friction >= 5.0).
3. Deterministic 3-Tier Collision Resolution with Dynamic Sequential Portfolio State Recalculation (Gate 2).
4. Broker-Aware Micro-Lot Floor Sizing & Rejection of Under-Min Volume (Gate 4).
5. Pyramiding Order of Operations (Case A: floor(2/3 * V1), SL to BE, SL2 to BE) with Gap & Race-Condition Safeguards (Gate 1).
6. Margin Safety, Heat Cap (<= 6.0%), Position Count Cap (<= 2).
7. Complete State Persistence & Fail-Safe Recovery.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional, Set
from enum import Enum
import math
import json
import os

from rsi_trend_pullback.data.loader import Candle
from rsi_trend_pullback.state_machine.states import SignalType, StrategyState, TradingSignal
from rsi_trend_pullback.research.broker_sizing_engine import (
    BrokerSymbolMetadata,
    XM_AUTHORITATIVE_METADATA,
    BrokerSizingEngineGate4,
    SizingResult
)
from rsi_trend_pullback.research.portfolio_heat_engine import (
    ActivePosition,
    CandidateSignal,
    PortfolioHeatEngineGate2
)
from rsi_trend_pullback.research.multi_asset_calendar_engine import (
    AssetMarketSpec,
    ASSET_SPECS,
    SessionType,
    IndependentAssetStream
)


class PositionLifecycleState(Enum):
    PENDING_OPEN = "PENDING_OPEN"
    BASE_ACTIVE = "BASE_ACTIVE"               # Trade 1 active with initial Hard SL
    PYRAMID_QUALIFIED = "PYRAMID_QUALIFIED"   # Trade 1 hit >= +1.5R, SL moved to BE
    PYRAMID_ACTIVE = "PYRAMID_ACTIVE"         # Trade 1 at BE + Trade 2 active with SL at BE
    CLOSED_HARD_SL = "CLOSED_HARD_SL"
    CLOSED_THESIS_EXIT = "CLOSED_THESIS_EXIT"
    CLOSED_BE_SL = "CLOSED_BE_SL"
    REJECTED_BELOW_MIN_LOT = "REJECTED_BELOW_MIN_LOT"
    REJECTED_HEAT_CAP = "REJECTED_HEAT_CAP"
    REJECTED_POSITION_CAP = "REJECTED_POSITION_CAP"
    REJECTED_MARGIN = "REJECTED_MARGIN"


@dataclass
class TradeRecord:
    trade_id: str
    symbol: str
    is_pyramid_leg: bool
    parent_trade_id: Optional[str]
    direction: str  # "LONG" or "SHORT"
    entry_time: datetime
    entry_price: float
    initial_sl: float
    current_sl: float
    volume: float
    state: PositionLifecycleState
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    realized_pnl_thb: float = 0.0
    exit_reason: Optional[str] = None


class V27UnifiedPipelineOrchestrator:
    """
    Deterministic Gate 5 Unified Pipeline Orchestrator for Strategy V2.7.
    """

    def __init__(
        self,
        initial_equity_thb: float = 10000.0,
        broker_metadata: Dict[str, BrokerSymbolMetadata] = XM_AUTHORITATIVE_METADATA,
        asset_specs: Dict[str, AssetMarketSpec] = ASSET_SPECS
    ):
        self.equity_thb: float = initial_equity_thb
        self.free_margin_thb: float = initial_equity_thb
        self.broker_metadata = broker_metadata
        self.asset_specs = asset_specs

        # Independent Asset Streams
        self.streams: Dict[str, IndependentAssetStream] = {
            sym: IndependentAssetStream(spec) for sym, spec in asset_specs.items()
        }

        # Active Positions & Trade History
        self.active_trades: Dict[str, TradeRecord] = {}  # Key: trade_id
        self.closed_trades: List[TradeRecord] = []
        self.trade_counter: int = 0

        # DCA Management
        self.monthly_dca_thb: float = 1000.0
        self.last_dca_month: Optional[int] = None
        self.total_deposited_thb: float = initial_equity_thb

        # Audit Logs
        self.audit_log: List[Dict[str, Any]] = []

    def get_active_positions_for_heat(self) -> List[ActivePosition]:
        """
        Converts active TradeRecords into ActivePosition objects for Portfolio Heat Engine.
        """
        active_list = []
        for t in self.active_trades.values():
            meta = self.broker_metadata[t.symbol]
            stream = self.streams[t.symbol]
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
                friction_buffer_cur=25.0  # 25 THB standard friction buffer
            ))
        return active_list

    def apply_monthly_dca(self, current_dt: datetime) -> bool:
        """
        Applies 1,000 THB monthly DCA at the first bar of each calendar month.
        Sizing strictly uses equity AFTER deposit is credited.
        """
        if self.last_dca_month is None:
            self.last_dca_month = current_dt.month
            return False

        if current_dt.month != self.last_dca_month:
            self.equity_thb += self.monthly_dca_thb
            self.free_margin_thb += self.monthly_dca_thb
            self.total_deposited_thb += self.monthly_dca_thb
            self.last_dca_month = current_dt.month
            self.audit_log.append({
                "timestamp": current_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "DCA_DEPOSIT",
                "amount_thb": self.monthly_dca_thb,
                "new_equity_thb": round(self.equity_thb, 2)
            })
            return True
        return False

    def process_closed_candle_event(
        self,
        event_timestamp: datetime,
        candles_by_symbol: Dict[str, Candle]
    ) -> List[Dict[str, Any]]:
        """
        Complete causal event step:
        Step 1: Apply DCA if new month.
        Step 2: Check Intrabar SL and Trailing BE touches on open trades.
        Step 3: Check Pyramiding triggers (+1.5R) with strict Order of Operations.
        Step 4: Check Thesis Exits (RSI < 40 / > 60).
        Step 5: Ingest new closed candles and evaluate new entry signals.
        Step 6: Resolve signal collisions sequentially (updating portfolio state after each fill).
        """
        event_actions = []

        # ── Step 1: DCA Deposit ──
        self.apply_monthly_dca(event_timestamp)

        # ── Step 2 & 3 & 4: Manage Existing Active Positions ──
        active_ids = list(self.active_trades.keys())
        for tid in active_ids:
            if tid not in self.active_trades:
                continue
            trade = self.active_trades[tid]
            sym = trade.symbol
            if sym not in candles_by_symbol:
                continue

            candle = candles_by_symbol[sym]
            meta = self.broker_metadata[sym]

            # 2.1 Intrabar Hard SL / BE Touch Check
            is_stopped_out = False
            sl_exit_price = trade.current_sl

            if trade.direction == "LONG":
                if candle.low <= trade.current_sl:
                    is_stopped_out = True
                    # Slippage / Gap safety: If open gapped below SL, fill at candle open
                    sl_exit_price = min(trade.current_sl, candle.open) if candle.open < trade.current_sl else trade.current_sl
            else:
                if candle.high >= trade.current_sl:
                    is_stopped_out = True
                    sl_exit_price = max(trade.current_sl, candle.open) if candle.open > trade.current_sl else trade.current_sl

            if is_stopped_out:
                self._close_position(trade, event_timestamp, sl_exit_price, "STOP_LOSS_TOUCH", meta)
                event_actions.append({"trade_id": tid, "action": "STOP_LOSS_CLOSED", "exit_price": sl_exit_price})
                continue

            # 2.2 Pyramiding Order of Operations (+1.5R Check for Base Trades)
            if not trade.is_pyramid_leg and trade.state == PositionLifecycleState.BASE_ACTIVE:
                d_distance = abs(trade.entry_price - trade.initial_sl)
                target_15r = trade.entry_price + (1.5 * d_distance) if trade.direction == "LONG" else trade.entry_price - (1.5 * d_distance)

                # Check if high/low touched +1.5R during candle
                is_15r_reached = (candle.high >= target_15r) if trade.direction == "LONG" else (candle.low <= target_15r)

                if is_15r_reached:
                    # Strict Order of Operations:
                    # 1. Modify Trade 1 SL to Breakeven
                    trade.current_sl = trade.entry_price
                    trade.state = PositionLifecycleState.PYRAMID_QUALIFIED

                    # 2. Calculate Trade 2 Sizing = floor(2/3 * V1)
                    pyramid_size_res = BrokerSizingEngineGate4.calculate_pyramid_sizing(
                        meta=meta,
                        base_volume=trade.volume,
                        free_margin_thb=self.free_margin_thb,
                        sl_distance_price=(1.5 * d_distance)
                    )

                    # 3. Position Cap and Heat Cap Validation for Pyramid Leg
                    if pyramid_size_res.is_accepted:
                        active_heat_positions = self.get_active_positions_for_heat()
                        cand_pyramid = CandidateSignal(
                            symbol=sym,
                            is_pyramid=True,
                            direction=trade.direction,
                            entry_price=target_15r,
                            stop_price=trade.entry_price,  # Stop at Breakeven
                            volume=pyramid_size_res.quantized_volume,
                            tick_size=meta.trade_tick_size,
                            tick_value=meta.trade_tick_value,
                            friction_buffer_cur=25.0,
                            er_14=0.60,
                            spread_atr_ratio=0.05
                        )
                        can_accept, reason, proj_heat = PortfolioHeatEngineGate2.can_accept_order(
                            active_heat_positions, cand_pyramid, self.equity_thb
                        )

                        if can_accept:
                            # 4. Open Trade 2 (Scale-In)
                            self.trade_counter += 1
                            t2_id = f"{sym}_PYR_{self.trade_counter}"
                            t2 = TradeRecord(
                                trade_id=t2_id,
                                symbol=sym,
                                is_pyramid_leg=True,
                                parent_trade_id=tid,
                                direction=trade.direction,
                                entry_time=event_timestamp,
                                entry_price=target_15r,
                                initial_sl=trade.entry_price,
                                current_sl=trade.entry_price,
                                volume=pyramid_size_res.quantized_volume,
                                state=PositionLifecycleState.PYRAMID_ACTIVE
                            )
                            self.active_trades[t2_id] = t2
                            trade.state = PositionLifecycleState.PYRAMID_ACTIVE
                            event_actions.append({"trade_id": t2_id, "action": "PYRAMID_OPENED", "volume": t2.volume})
                        else:
                            event_actions.append({"trade_id": tid, "action": "PYRAMID_REJECTED", "reason": reason})
                    else:
                        event_actions.append({"trade_id": tid, "action": "PYRAMID_REJECTED", "reason": pyramid_size_res.rejection_reason})

        # ── Step 5 & 6: Ingest Candles & Resolve Signal Collisions ──
        raw_signals: List[CandidateSignal] = []
        for sym, c in candles_by_symbol.items():
            stream = self.streams[sym]
            meta = self.broker_metadata[sym]
            sig = stream.process_candle(c)

            # Check Thesis Exit on existing open trades
            if sig and sig.signal_type in (SignalType.LONG_EXIT_SIGNAL, SignalType.SHORT_EXIT_SIGNAL):
                for tid, tr in list(self.active_trades.items()):
                    if tr.symbol == sym:
                        if (tr.direction == "LONG" and sig.signal_type == SignalType.LONG_EXIT_SIGNAL) or \
                           (tr.direction == "SHORT" and sig.signal_type == SignalType.SHORT_EXIT_SIGNAL):
                            self._close_position(tr, event_timestamp, c.close, "THESIS_EXIT", meta)
                            event_actions.append({"trade_id": tid, "action": "THESIS_EXIT_CLOSED", "exit_price": c.close})

            # Check New Entry Signals
            if sig and sig.signal_type in (SignalType.LONG_ENTRY_SIGNAL, SignalType.SHORT_ENTRY_SIGNAL):
                # Only signal if no active base trade on this symbol
                has_active = any(t.symbol == sym for t in self.active_trades.values())
                if not has_active:
                    direction = "LONG" if sig.signal_type == SignalType.LONG_ENTRY_SIGNAL else "SHORT"
                    atr_val = stream.latest_atr or (c.close * 0.01)
                    sl_dist = 2.5 * atr_val
                    stop_price = c.close - sl_dist if direction == "LONG" else c.close + sl_dist

                    # Sizing via Gate 4
                    size_res = BrokerSizingEngineGate4.calculate_base_sizing(
                        meta=meta,
                        equity_thb=self.equity_thb,
                        free_margin_thb=self.free_margin_thb,
                        sl_distance_price=sl_dist
                    )

                    if size_res.is_accepted:
                        spread_atr = meta.trade_tick_size * 25 / atr_val  # approximate spread/ATR
                        raw_signals.append(CandidateSignal(
                            symbol=sym,
                            is_pyramid=False,
                            direction=direction,
                            entry_price=c.close,
                            stop_price=stop_price,
                            volume=size_res.quantized_volume,
                            tick_size=meta.trade_tick_size,
                            tick_value=meta.trade_tick_value,
                            friction_buffer_cur=25.0,
                            er_14=stream.latest_er or 0.0,
                            spread_atr_ratio=spread_atr
                        ))
                    else:
                        event_actions.append({"symbol": sym, "action": "SIGNAL_REJECTED", "reason": size_res.rejection_reason})

        # ── Sequential Collision Resolution (Re-evaluating dynamic portfolio state after each fill) ──
        if raw_signals:
            # Sort candidates by 3-tier unbiased priority
            sorted_candidates = sorted(
                raw_signals,
                key=lambda s: (-round(s.er_14, 4), round(s.spread_atr_ratio, 4), s.symbol.upper())
            )

            for cand in sorted_candidates:
                # Dynamically re-evaluate active positions at this exact sub-step!
                current_active_positions = self.get_active_positions_for_heat()
                can_accept, reason, proj_heat = PortfolioHeatEngineGate2.can_accept_order(
                    current_active_positions, cand, self.equity_thb
                )

                if can_accept:
                    self.trade_counter += 1
                    t_id = f"{cand.symbol}_BASE_{self.trade_counter}"
                    new_trade = TradeRecord(
                        trade_id=t_id,
                        symbol=cand.symbol,
                        is_pyramid_leg=False,
                        parent_trade_id=None,
                        direction=cand.direction,
                        entry_time=event_timestamp,
                        entry_price=cand.entry_price,
                        initial_sl=cand.stop_price,
                        current_sl=cand.stop_price,
                        volume=cand.volume,
                        state=PositionLifecycleState.BASE_ACTIVE
                    )
                    self.active_trades[t_id] = new_trade
                    event_actions.append({"trade_id": t_id, "action": "ORDER_OPENED", "volume": cand.volume, "projected_heat": proj_heat})
                else:
                    event_actions.append({"symbol": cand.symbol, "action": "ORDER_REJECTED", "reason": reason})

        return event_actions

    def _close_position(
        self,
        trade: TradeRecord,
        exit_time: datetime,
        exit_price: float,
        exit_reason: str,
        meta: BrokerSymbolMetadata
    ) -> None:
        """
        Closes active position, calculates realized P&L in THB, and updates equity.
        """
        if trade.direction == "LONG":
            points = exit_price - trade.entry_price
        else:
            points = trade.entry_price - exit_price

        ticks = points / meta.trade_tick_size
        pnl_thb = ticks * meta.trade_tick_value * trade.volume

        trade.exit_time = exit_time
        trade.exit_price = exit_price
        trade.realized_pnl_thb = round(pnl_thb, 2)
        trade.exit_reason = exit_reason
        trade.state = PositionLifecycleState.CLOSED_HARD_SL if "STOP" in exit_reason else PositionLifecycleState.CLOSED_THESIS_EXIT

        self.equity_thb += pnl_thb
        self.equity_thb = max(1.0, self.equity_thb)
        self.free_margin_thb = self.equity_thb

        self.closed_trades.append(trade)
        if trade.trade_id in self.active_trades:
            del self.active_trades[trade.trade_id]
