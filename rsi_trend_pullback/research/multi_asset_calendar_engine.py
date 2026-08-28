"""
Strategy V2.7 Research Candidate - Gate 3: Multi-Asset Independent Calendar & Event Engine.
Strictly implements:
1. Independent time series and market-session models for each asset (BTC 24/7 vs FX/Gold 24/5 vs US500 breaks).
2. No cross-asset bar synthesis or timestamp forward-filling.
3. Explicit Data Integrity auditing: flags missing bars, rejects duplicate timestamps.
4. Independent indicator calculation per asset (RSI, ER, ATR).
5. Deterministic multi-asset event coordinator with 3-tier collision resolution.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional, Set
from enum import Enum

from rsi_trend_pullback.data.loader import Candle
from rsi_trend_pullback.indicator.rsi import WilderRSI
from rsi_trend_pullback.indicator.kaufman_er import KaufmanER
from rsi_trend_pullback.indicator.atr import WilderATR
from rsi_trend_pullback.state_machine.states import StrategyState, SignalType, TradingSignal
from rsi_trend_pullback.state_machine.engine_v2 import RSIStateMachineV2
from rsi_trend_pullback.research.portfolio_heat_engine import (
    ActivePosition,
    CandidateSignal,
    PortfolioHeatEngineGate2
)


class SessionType(Enum):
    CONTINUOUS_24_7 = "24/7"  # BTCUSD
    STANDARD_24_5 = "24/5"    # Forex (USDJPY, GBPUSD) and Gold (XAUUSD)
    EQUITY_INDEX_24_5_WITH_BREAKS = "24/5_BREAKS"  # US500


@dataclass
class AssetMarketSpec:
    symbol: str
    session_type: SessionType
    tick_size: float
    tick_value: float
    volume_min: float
    volume_max: float
    volume_step: float
    typical_spread: float
    friction_ref: float
    digits: int


ASSET_SPECS: Dict[str, AssetMarketSpec] = {
    "BTCUSD": AssetMarketSpec("BTCUSD", SessionType.CONTINUOUS_24_7, 0.01, 0.35, 0.01, 50.0, 0.01, 50.0, 35.0, 2),
    "GBPUSD": AssetMarketSpec("GBPUSD", SessionType.STANDARD_24_5, 0.00001, 35.0, 0.01, 50.0, 0.01, 0.00010, 0.00020, 5),
    "US500":  AssetMarketSpec("US500",  SessionType.EQUITY_INDEX_24_5_WITH_BREAKS, 0.01, 0.35, 0.10, 50.0, 0.01, 0.70, 0.80, 2),
    "USDJPY": AssetMarketSpec("USDJPY", SessionType.STANDARD_24_5, 0.001, 2.25, 0.01, 50.0, 0.01, 0.010, 0.018, 3),
    "XAUUSD": AssetMarketSpec("XAUUSD", SessionType.STANDARD_24_5, 0.01, 0.35, 0.01, 50.0, 0.01, 0.25, 0.46, 2),
}


@dataclass
class DataIntegrityReport:
    symbol: str
    total_bars_processed: int = 0
    duplicate_timestamps_rejected: int = 0
    missing_bars_flagged: int = 0
    weekend_gaps_detected: int = 0
    session_breaks_detected: int = 0
    anomalies: List[str] = field(default_factory=list)


class IndependentAssetStream:
    """
    Encapsulates independent market clock, indicators, and state machine for a single asset.
    Strictly isolated from other assets.
    """

    def __init__(self, spec: AssetMarketSpec):
        self.spec = spec
        self.symbol = spec.symbol
        self.session_type = spec.session_type

        self.indicator_rsi = WilderRSI(period=14)
        self.indicator_er = KaufmanER(period=14)
        self.indicator_atr = WilderATR(period=14)
        self.state_machine = RSIStateMachineV2(upper_level=60.0, pullback_level=50.0, lower_level=40.0, er_threshold=0.40)

        self.price_history: List[float] = []
        self.processed_timestamps: Set[datetime] = set()
        self.last_candle_timestamp: Optional[datetime] = None
        self.integrity_report = DataIntegrityReport(symbol=self.symbol)

        self.latest_rsi: Optional[float] = None
        self.latest_er: Optional[float] = None
        self.latest_atr: Optional[float] = None

    def is_market_open(self, dt: datetime) -> bool:
        """
        Determines whether the market is open for this specific asset at timestamp dt.
        """
        if self.session_type == SessionType.CONTINUOUS_24_7:
            return True  # BTC trades 24/7

        weekday = dt.weekday()  # Monday=0, Sunday=6
        hour = dt.hour

        # Weekend closure for 24/5 (Friday 22:00 UTC to Sunday 21:00 UTC)
        if weekday == 5:  # Saturday
            return False
        if weekday == 6 and hour < 21:  # Sunday before 21:00 UTC
            return False
        if weekday == 4 and hour >= 22:  # Friday after 22:00 UTC
            return False

        # US500 daily session break check (21:15 UTC to 22:15 UTC daily maintenance break)
        if self.session_type == SessionType.EQUITY_INDEX_24_5_WITH_BREAKS:
            if (hour == 21 and dt.minute >= 15) or (hour == 22 and dt.minute < 15):
                return False

        return True

    def process_candle(self, candle: Candle) -> Optional[TradingSignal]:
        """
        Ingests a valid closed H1 candle strictly for this asset.
        Audits data integrity and evaluates strategy rules.
        """
        # 1. Duplicate Timestamp Check
        if candle.timestamp in self.processed_timestamps:
            self.integrity_report.duplicate_timestamps_rejected += 1
            self.integrity_report.anomalies.append(f"DUPLICATE_TIMESTAMP: {candle.timestamp} rejected")
            return None

        # 2. Gap & Missing Bar Check
        if self.last_candle_timestamp is not None:
            gap_seconds = (candle.timestamp - self.last_candle_timestamp).total_seconds()
            expected_seconds = 3600  # 1 hour for H1

            if gap_seconds > expected_seconds:
                # Differentiate between normal weekend closure vs unexpected missing bar
                if self.last_candle_timestamp.weekday() == 4 and candle.timestamp.weekday() in (6, 0):
                    self.integrity_report.weekend_gaps_detected += 1
                elif self.session_type == SessionType.EQUITY_INDEX_24_5_WITH_BREAKS and gap_seconds <= 7200:
                    self.integrity_report.session_breaks_detected += 1
                else:
                    missing_count = int(gap_seconds // expected_seconds) - 1
                    self.integrity_report.missing_bars_flagged += missing_count
                    self.integrity_report.anomalies.append(
                        f"MISSING_BARS: {missing_count} bars between {self.last_candle_timestamp} and {candle.timestamp}"
                    )

        # 3. Update Isolated State & Indicators
        self.processed_timestamps.add(candle.timestamp)
        self.last_candle_timestamp = candle.timestamp
        self.integrity_report.total_bars_processed += 1
        self.price_history.append(candle.close)

        rsi_val = self.indicator_rsi.update(candle.close)
        er_val = self.indicator_er.update(candle.close)
        atr_val = self.indicator_atr.update(candle)

        self.latest_rsi = rsi_val
        self.latest_er = er_val
        self.latest_atr = atr_val

        # 4. Economic Viability Filter & State Machine Evaluation
        chg14 = candle.close - self.price_history[-1 - 14] if len(self.price_history) > 14 else None
        vol_sufficient = (atr_val / self.spec.friction_ref) >= 5.0 if (atr_val and self.spec.friction_ref > 0) else False
        effective_er = er_val if vol_sufficient else 0.0

        signal = self.state_machine.evaluate_bar(
            bar_index=len(self.price_history),
            timestamp=candle.timestamp,
            current_rsi=rsi_val,
            current_er=effective_er,
            close_change_14=chg14
        )

        return signal


class MultiAssetCalendarCoordinator:
    """
    Global event dispatcher managing independent time series across 5 assets.
    """

    def __init__(self, asset_specs: Dict[str, AssetMarketSpec] = ASSET_SPECS):
        self.streams: Dict[str, IndependentAssetStream] = {
            sym: IndependentAssetStream(spec) for sym, spec in asset_specs.items()
        }

    def process_event_step(
        self,
        event_timestamp: datetime,
        active_candles: Dict[str, Candle],
        active_positions: List[ActivePosition],
        equity: float
    ) -> Dict[str, Any]:
        """
        Processes an event step where one or more assets closed an H1 candle at event_timestamp.
        Handles independent bar ingestion and resolves any signal collisions deterministically.
        """
        raw_signals: List[Tuple[str, TradingSignal]] = []

        # 1. Ingest candles independently into respective asset streams
        for sym, stream in self.streams.items():
            if sym in active_candles:
                c = active_candles[sym]
                sig = stream.process_candle(c)
                if sig and sig.signal_type in (SignalType.LONG_ENTRY_SIGNAL, SignalType.SHORT_ENTRY_SIGNAL):
                    raw_signals.append((sym, sig))

        # 2. Build Candidate Signals
        candidates: List[CandidateSignal] = []
        for sym, sig in raw_signals:
            stream = self.streams[sym]
            spec = stream.spec
            direction = "LONG" if sig.signal_type == SignalType.LONG_ENTRY_SIGNAL else "SHORT"
            entry_price = active_candles[sym].close  # Signal at Close(T), filled at Open(T+1)
            atr_val = stream.latest_atr or (entry_price * 0.01)
            sl_dist = 2.5 * atr_val
            stop_price = entry_price - sl_dist if direction == "LONG" else entry_price + sl_dist

            # Calculate base volume using math.floor
            target_dollar_risk = equity * 0.03
            loss_per_1_lot = (sl_dist / spec.tick_size) * spec.tick_value
            raw_v = target_dollar_risk / loss_per_1_lot if loss_per_1_lot > 0 else spec.volume_min
            v1 = max(spec.volume_min, min(spec.volume_max, math.floor(raw_v / spec.volume_step) * spec.volume_step))

            spread_atr_ratio = spec.typical_spread / atr_val if atr_val > 0 else 1.0

            candidates.append(CandidateSignal(
                symbol=sym,
                is_pyramid=False,
                direction=direction,
                entry_price=entry_price,
                stop_price=stop_price,
                volume=round(v1, 6),
                tick_size=spec.tick_size,
                tick_value=spec.tick_value,
                friction_buffer_cur=25.0,  # 25 THB standard buffer
                er_14=stream.latest_er or 0.0,
                spread_atr_ratio=spread_atr_ratio
            ))

        # 3. Resolve Collisions via 3-Tier Rule (ER14 -> Spread/ATR -> Canonical Alphabetical Symbol)
        collision_results = []
        if candidates:
            collision_results = PortfolioHeatEngineGate2.resolve_signal_collisions(
                active_positions=active_positions,
                candidates=candidates,
                equity=equity
            )

        return {
            "event_timestamp": event_timestamp,
            "candles_processed_count": len(active_candles),
            "signals_generated_count": len(raw_signals),
            "candidates_count": len(candidates),
            "collision_results": collision_results
        }
