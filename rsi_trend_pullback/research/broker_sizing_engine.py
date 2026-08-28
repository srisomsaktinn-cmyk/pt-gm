"""
Strategy V2.7 Research Candidate - Gate 4: Broker Metadata & Micro-Lot Quantization Engine.
Strictly implements:
1. Dynamic broker metadata ingestion (volume_min, volume_step, volume_max, contract_size, tick_size, tick_value).
2. Strict Floor Quantization: Quantized_Volume = floor(Raw_Volume / Volume_Step) * Volume_Step.
3. Strict Rule: Actual Risk <= Target Risk. If Quantized_Volume < Volume_Min -> REJECT TRADE.
4. Pyramid Sizing: V2 = floor((2/3) * V1 / Volume_Step) * Volume_Step. If V2 < Volume_Min -> REJECT PYRAMID.
5. Margin Safety & Free Margin Checks.
6. Export timestamped broker_metadata_snapshot.json.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
import math
import json
import os


@dataclass
class BrokerSymbolMetadata:
    canonical_name: str
    broker_symbol: str
    volume_min: float
    volume_max: float
    volume_step: float
    trade_contract_size: float
    trade_tick_size: float
    trade_tick_value: float  # Denominated in Account Currency (THB)
    currency_base: str
    currency_profit: str
    currency_margin: str
    leverage: float
    margin_initial: float  # Margin required for 1.0 lot in Account Currency
    digits: int
    is_swap_free: bool


# Authoritative XM Ultra Low Metadata Snapshot for 10,000 THB Base Account (Leverage 1:1000)
XM_AUTHORITATIVE_METADATA: Dict[str, BrokerSymbolMetadata] = {
    "XAUUSD": BrokerSymbolMetadata(
        canonical_name="XAUUSD",
        broker_symbol="GOLD#",
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01,
        trade_contract_size=100.0,  # 100 oz per 1.0 lot (0.01 lot = 1 oz)
        trade_tick_size=0.01,
        trade_tick_value=0.35,      # 0.01 USD tick * 35 THB/USD = 0.35 THB
        currency_base="XAU",
        currency_profit="USD",
        currency_margin="USD",
        leverage=1000.0,
        margin_initial=87.50,       # 1.0 lot margin ~2.5 USD * 35 = 87.50 THB
        digits=2,
        is_swap_free=True
    ),
    "USDJPY": BrokerSymbolMetadata(
        canonical_name="USDJPY",
        broker_symbol="USDJPY",
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01,
        trade_contract_size=100000.0,  # 100k units (0.01 lot = 1,000 units)
        trade_tick_size=0.001,
        trade_tick_value=2.25,         # 100 JPY tick in THB ~2.25 THB per 1.0 lot
        currency_base="USD",
        currency_profit="JPY",
        currency_margin="USD",
        leverage=1000.0,
        margin_initial=35.0,           # ~1.0 USD * 35 = 35 THB
        digits=3,
        is_swap_free=True
    ),
    "GBPUSD": BrokerSymbolMetadata(
        canonical_name="GBPUSD",
        broker_symbol="GBPUSD",
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01,
        trade_contract_size=100000.0,
        trade_tick_size=0.00001,
        trade_tick_value=35.0,         # 1 USD tick = 35 THB per 1.0 lot
        currency_base="GBP",
        currency_profit="USD",
        currency_margin="GBP",
        leverage=1000.0,
        margin_initial=45.50,
        digits=5,
        is_swap_free=True
    ),
    "US500": BrokerSymbolMetadata(
        canonical_name="US500",
        broker_symbol="US500Cash#",
        volume_min=0.10,               # Minimum 0.10 lot on XM US500
        volume_max=50.0,
        volume_step=0.01,
        trade_contract_size=1.0,       # 1 contract
        trade_tick_size=0.01,
        trade_tick_value=0.35,         # 0.01 index pt = 0.35 THB
        currency_base="USD",
        currency_profit="USD",
        currency_margin="USD",
        leverage=1000.0,
        margin_initial=19.25,
        digits=2,
        is_swap_free=False
    ),
    "BTCUSD": BrokerSymbolMetadata(
        canonical_name="BTCUSD",
        broker_symbol="BTCUSD#",
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01,
        trade_contract_size=1.0,       # 1 BTC per 1.0 lot (0.01 lot = 0.01 BTC)
        trade_tick_size=0.01,
        trade_tick_value=0.35,
        currency_base="BTC",
        currency_profit="USD",
        currency_margin="USD",
        leverage=1000.0,
        margin_initial=35.0,
        digits=2,
        is_swap_free=True
    )
}


@dataclass
class SizingResult:
    symbol: str
    is_accepted: bool
    rejection_reason: Optional[str]
    target_risk_thb: float
    raw_volume: float
    quantized_volume: float
    actual_risk_thb: float
    actual_risk_pct: float
    rounding_error_thb: float
    required_margin_thb: float
    free_margin_thb: float
    is_pyramid: bool


class BrokerSizingEngineGate4:
    """
    Deterministic Broker-Aware Sizing & Quantization Engine for Strategy V2.7.
    """

    TARGET_BASE_RISK_PCT: float = 0.03  # 3.0% of Account Equity
    MARGIN_SAFETY_BUFFER: float = 1.25  # Free margin must exceed 1.25x required margin

    @classmethod
    def calculate_base_sizing(
        cls,
        meta: BrokerSymbolMetadata,
        equity_thb: float,
        free_margin_thb: float,
        sl_distance_price: float
    ) -> SizingResult:
        """
        Calculates Trade 1 sizing enforcing strict floor rounding.
        Rejects trade if quantized volume < volume_min.
        """
        target_risk_thb = equity_thb * cls.TARGET_BASE_RISK_PCT

        if sl_distance_price <= 0 or meta.trade_tick_size <= 0 or meta.trade_tick_value <= 0:
            return SizingResult(meta.canonical_name, False, "INVALID_PRICE_PARAMETERS", target_risk_thb, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, free_margin_thb, False)

        # Monetary loss per 1.0 lot at stop distance in THB
        loss_per_1_lot_thb = (sl_distance_price / meta.trade_tick_size) * meta.trade_tick_value

        if loss_per_1_lot_thb <= 0:
            return SizingResult(meta.canonical_name, False, "INVALID_LOSS_PER_LOT", target_risk_thb, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, free_margin_thb, False)

        raw_volume = target_risk_thb / loss_per_1_lot_thb

        # Strict Floor Quantization
        stepped_volume = math.floor(raw_volume / meta.volume_step) * meta.volume_step
        quantized_volume = round(stepped_volume, 6)

        # Check Under Minimum Volume Floor -> REJECT (Rule: Never round up!)
        if quantized_volume < meta.volume_min:
            actual_risk_if_min = round(meta.volume_min * loss_per_1_lot_thb, 2)
            actual_risk_pct_if_min = (actual_risk_if_min / equity_thb) * 100.0
            return SizingResult(
                symbol=meta.canonical_name,
                is_accepted=False,
                rejection_reason=f"BELOW_MIN_VOLUME: Raw {raw_volume:.4f} lots < Min {meta.volume_min:.2f} lots (Min lot risk {actual_risk_if_min:.1f} THB [{actual_risk_pct_if_min:.1f}%] exceeds 3% target {target_risk_thb:.1f} THB)",
                target_risk_thb=round(target_risk_thb, 2),
                raw_volume=round(raw_volume, 4),
                quantized_volume=0.0,
                actual_risk_thb=0.0,
                actual_risk_pct=0.0,
                rounding_error_thb=0.0,
                required_margin_thb=0.0,
                free_margin_thb=free_margin_thb,
                is_pyramid=False
            )

        # Clamp to Volume Max
        quantized_volume = min(meta.volume_max, quantized_volume)

        # Recalculate Actual Risk
        actual_risk_thb = round(quantized_volume * loss_per_1_lot_thb, 2)
        actual_risk_pct = (actual_risk_thb / equity_thb) * 100.0
        rounding_error_thb = round(target_risk_thb - actual_risk_thb, 2)

        # Margin Safety Check
        required_margin_thb = round(quantized_volume * meta.margin_initial, 2)
        if free_margin_thb < (required_margin_thb * cls.MARGIN_SAFETY_BUFFER):
            return SizingResult(
                symbol=meta.canonical_name,
                is_accepted=False,
                rejection_reason=f"INSUFFICIENT_FREE_MARGIN: Free margin {free_margin_thb:.2f} THB < Required {required_margin_thb * cls.MARGIN_SAFETY_BUFFER:.2f} THB",
                target_risk_thb=round(target_risk_thb, 2),
                raw_volume=round(raw_volume, 4),
                quantized_volume=quantized_volume,
                actual_risk_thb=actual_risk_thb,
                actual_risk_pct=round(actual_risk_pct, 2),
                rounding_error_thb=rounding_error_thb,
                required_margin_thb=required_margin_thb,
                free_margin_thb=free_margin_thb,
                is_pyramid=False
            )

        return SizingResult(
            symbol=meta.canonical_name,
            is_accepted=True,
            rejection_reason=None,
            target_risk_thb=round(target_risk_thb, 2),
            raw_volume=round(raw_volume, 4),
            quantized_volume=quantized_volume,
            actual_risk_thb=actual_risk_thb,
            actual_risk_pct=round(actual_risk_pct, 2),
            rounding_error_thb=rounding_error_thb,
            required_margin_thb=required_margin_thb,
            free_margin_thb=free_margin_thb,
            is_pyramid=False
        )

    @classmethod
    def calculate_pyramid_sizing(
        cls,
        meta: BrokerSymbolMetadata,
        base_volume: float,
        free_margin_thb: float,
        sl_distance_price: float
    ) -> SizingResult:
        """
        Calculates Trade 2 (Pyramid) sizing strictly using Case A: V2 = floor((2/3) * V1).
        Rejects pyramid if V2 < volume_min.
        """
        raw_v2 = (2.0 / 3.0) * base_volume
        stepped_v2 = math.floor(raw_v2 / meta.volume_step) * meta.volume_step
        quantized_v2 = round(stepped_v2, 6)

        loss_per_1_lot_thb = (sl_distance_price / meta.trade_tick_size) * meta.trade_tick_value

        if quantized_v2 < meta.volume_min:
            return SizingResult(
                symbol=meta.canonical_name,
                is_accepted=False,
                rejection_reason=f"PYRAMID_BELOW_MIN_VOLUME: Scaled volume {raw_v2:.4f} < Min {meta.volume_min:.2f}",
                target_risk_thb=0.0,
                raw_volume=round(raw_v2, 4),
                quantized_volume=0.0,
                actual_risk_thb=0.0,
                actual_risk_pct=0.0,
                rounding_error_thb=0.0,
                required_margin_thb=0.0,
                free_margin_thb=free_margin_thb,
                is_pyramid=True
            )

        quantized_v2 = min(meta.volume_max, quantized_v2)
        actual_risk_thb = round(quantized_v2 * loss_per_1_lot_thb, 2)
        required_margin_thb = round(quantized_v2 * meta.margin_initial, 2)

        if free_margin_thb < (required_margin_thb * cls.MARGIN_SAFETY_BUFFER):
            return SizingResult(
                symbol=meta.canonical_name,
                is_accepted=False,
                rejection_reason=f"PYRAMID_INSUFFICIENT_MARGIN: Free margin {free_margin_thb:.2f} < Required {required_margin_thb * cls.MARGIN_SAFETY_BUFFER:.2f}",
                target_risk_thb=0.0,
                raw_volume=round(raw_v2, 4),
                quantized_volume=quantized_v2,
                actual_risk_thb=actual_risk_thb,
                actual_risk_pct=0.0,
                rounding_error_thb=0.0,
                required_margin_thb=required_margin_thb,
                free_margin_thb=free_margin_thb,
                is_pyramid=True
            )

        return SizingResult(
            symbol=meta.canonical_name,
            is_accepted=True,
            rejection_reason=None,
            target_risk_thb=0.0,
            raw_volume=round(raw_v2, 4),
            quantized_volume=quantized_v2,
            actual_risk_thb=actual_risk_thb,
            actual_risk_pct=0.0,
            rounding_error_thb=0.0,
            required_margin_thb=required_margin_thb,
            free_margin_thb=free_margin_thb,
            is_pyramid=True
        )

    @classmethod
    def export_broker_metadata_snapshot(cls, output_path: str = "d:/Kaeha/broker_metadata_snapshot.json") -> None:
        """
        Exports machine-readable snapshot containing all broker metadata values.
        """
        snapshot = {
            "snapshot_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+7"),
            "broker": "XM Global Limited (XM Ultra Low Account)",
            "account_currency": "THB",
            "leverage": "1:1000",
            "symbols": {k: asdict(v) for k, v in XM_AUTHORITATIVE_METADATA.items()}
        }
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=4, ensure_ascii=False)
        print(f"[METADATA EXPORT] Exported broker snapshot to {output_path}")
