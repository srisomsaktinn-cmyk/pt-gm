"""
Strategy V2.7 Rejected Signal Telemetry & Governance Logger.
Explicitly records every candidate trading signal rejected by risk boundaries:
- Aggregate Heat Cap Exceeded (> 6.0%)
- Cluster Heat Cap Exceeded (> 4.0%)
- Position Count Cap Exceeded (> 2 active positions)
- Below Minimum Volume Sizing
- Economic Friction Filter (ATR/Spread < 5.0)
- Hard Volume Ceiling Exceeded (> 0.50 lots)
"""

import os
import csv
from datetime import datetime
from typing import Dict, Any, Optional

REJECTED_SIGNALS_CSV = "d:/Kaeha/03_TRADING_RESEARCH_SYSTEM/data_telemetry/v27_rejected_signals.csv"


class V27RejectedSignalsLogger:
    """
    Appends structured rejected signal events to audit CSV.
    """
    CSV_HEADERS = [
        "timestamp",
        "symbol",
        "direction",
        "entry_price",
        "stop_price",
        "requested_volume",
        "potential_risk_thb",
        "rejection_reason",
        "category",
        "cluster",
        "current_equity",
        "aggregate_heat_pct",
        "cluster_heat_pct"
    ]

    @classmethod
    def log_rejection(
        cls,
        timestamp: datetime,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_price: float,
        requested_volume: float,
        potential_risk_thb: float,
        rejection_reason: str,
        cluster: str = "GENERAL",
        current_equity: float = 10000.0,
        aggregate_heat_pct: float = 0.0,
        cluster_heat_pct: float = 0.0
    ):
        os.makedirs(os.path.dirname(REJECTED_SIGNALS_CSV), exist_ok=True)
        file_exists = os.path.exists(REJECTED_SIGNALS_CSV)

        category = "UNKNOWN"
        if "CLUSTER_HEAT" in rejection_reason:
            category = "CLUSTER_HEAT_CAP"
        elif "HEAT_CAP" in rejection_reason:
            category = "PORTFOLIO_HEAT_CAP"
        elif "POSITION_CAP" in rejection_reason:
            category = "MAX_POSITIONS_CAP"
        elif "BELOW_MIN_VOLUME" in rejection_reason:
            category = "UNDER_MIN_VOLUME"
        elif "MAX_VOLUME" in rejection_reason:
            category = "OVER_MAX_VOLUME"
        elif "ECONOMIC_FILTER" in rejection_reason or "FRICTION" in rejection_reason:
            category = "ECONOMIC_FRICTION_FILTER"

        row = [
            timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            direction,
            round(entry_price, 5),
            round(stop_price, 5),
            round(requested_volume, 4),
            round(potential_risk_thb, 2),
            rejection_reason,
            category,
            cluster,
            round(current_equity, 2),
            f"{aggregate_heat_pct*100:.2f}%",
            f"{cluster_heat_pct*100:.2f}%"
        ]

        with open(REJECTED_SIGNALS_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(cls.CSV_HEADERS)
            writer.writerow(row)
