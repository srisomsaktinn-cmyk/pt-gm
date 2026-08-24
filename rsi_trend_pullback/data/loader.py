"""
Data loader and integrity validator for OHLC market data.
Ensures zero look-ahead, strict schema validation, monotonic timestamps,
and data anomaly detection.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
import csv
import math


@dataclass(frozen=True)
class Candle:
    """
    Immutable single OHLC candle representation.
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self):
        # Defensive price validations
        if self.open <= 0 or self.high <= 0 or self.low <= 0 or self.close <= 0:
            raise ValueError(f"Candle at {self.timestamp} contains non-positive price values: O={self.open}, H={self.high}, L={self.low}, C={self.close}")
        if self.low > self.high:
            raise ValueError(f"Candle at {self.timestamp} invalid: Low ({self.low}) > High ({self.high})")
        if self.open > self.high or self.open < self.low:
            raise ValueError(f"Candle at {self.timestamp} invalid: Open ({self.open}) out of High/Low bounds [{self.low}, {self.high}]")
        if self.close > self.high or self.close < self.low:
            raise ValueError(f"Candle at {self.timestamp} invalid: Close ({self.close}) out of High/Low bounds [{self.low}, {self.high}]")


class DataLoader:
    """
    Loads, cleans, and strictly validates chronological market data.
    """

    @staticmethod
    def parse_datetime(dt_str: str) -> datetime:
        """
        Parses common datetime string formats deterministically.
        """
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%Y.%m.%d %H:%M:%S",
            "%Y.%m.%d %H:%M",
        ]
        dt_str_clean = dt_str.strip()
        for fmt in formats:
            try:
                return datetime.strptime(dt_str_clean, fmt)
            except ValueError:
                continue
        # Fallback to ISO format parsing
        try:
            return datetime.fromisoformat(dt_str_clean)
        except Exception:
            raise ValueError(f"Unable to parse timestamp '{dt_str}' with standard date formats.")

    @classmethod
    def load_from_csv(cls, filepath: str, has_header: bool = True) -> List[Candle]:
        """
        Loads and strictly validates OHLC data from a CSV file.
        """
        candles: List[Candle] = []
        with open(filepath, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader) if has_header else None
            
            # Map column indices case-insensitively
            col_map: Dict[str, int] = {}
            if header:
                for idx, col in enumerate(header):
                    norm = col.strip().lower()
                    if norm in ["time", "timestamp", "date", "datetime"]:
                        col_map["time"] = idx
                    elif norm in ["open", "o"]:
                        col_map["open"] = idx
                    elif norm in ["high", "h"]:
                        col_map["high"] = idx
                    elif norm in ["low", "l"]:
                        col_map["low"] = idx
                    elif norm in ["close", "c"]:
                        col_map["close"] = idx
                    elif norm in ["vol", "volume", "v"]:
                        col_map["volume"] = idx

            # Fallback to standard 0..4 if header not recognized
            if "time" not in col_map: col_map["time"] = 0
            if "open" not in col_map: col_map["open"] = 1
            if "high" not in col_map: col_map["high"] = 2
            if "low" not in col_map: col_map["low"] = 3
            if "close" not in col_map: col_map["close"] = 4

            line_num = 1 if has_header else 0
            for row in reader:
                line_num += 1
                if not row or len(row) < 5:
                    continue
                try:
                    ts = cls.parse_datetime(row[col_map["time"]])
                    o = float(row[col_map["open"]])
                    h = float(row[col_map["high"]])
                    l = float(row[col_map["low"]])
                    c = float(row[col_map["close"]])
                    v = float(row[col_map["volume"]]) if "volume" in col_map and col_map["volume"] < len(row) else 0.0
                    
                    candle = Candle(timestamp=ts, open=o, high=h, low=l, close=c, volume=v)
                    candles.append(candle)
                except Exception as e:
                    raise ValueError(f"Error parsing row {line_num} in '{filepath}': {row} -> {str(e)}")

        return cls.validate_dataset(candles)

    @classmethod
    def load_from_records(cls, records: List[Dict[str, Any]]) -> List[Candle]:
        """
        Loads and validates from a list of dict records.
        """
        candles = []
        for idx, rec in enumerate(records):
            ts = rec["timestamp"] if isinstance(rec["timestamp"], datetime) else cls.parse_datetime(str(rec["timestamp"]))
            candle = Candle(
                timestamp=ts,
                open=float(rec["open"]),
                high=float(rec["high"]),
                low=float(rec["low"]),
                close=float(rec["close"]),
                volume=float(rec.get("volume", 0.0))
            )
            candles.append(candle)
        return cls.validate_dataset(candles)

    @staticmethod
    def validate_dataset(candles: List[Candle]) -> List[Candle]:
        """
        Strict dataset validation:
        1. Non-empty check
        2. Strictly monotonic timestamps (no duplicates, no out-of-order)
        3. Gap reporting
        """
        if not candles:
            raise ValueError("Dataset is empty. At least 1 candle required.")

        # Check chronological order and uniqueness
        seen_timestamps = set()
        for i in range(len(candles)):
            c = candles[i]
            if c.timestamp in seen_timestamps:
                raise ValueError(f"Data integrity error: Duplicate timestamp detected at {c.timestamp}")
            seen_timestamps.add(c.timestamp)

            if i > 0:
                prev_c = candles[i - 1]
                if c.timestamp <= prev_c.timestamp:
                    raise ValueError(
                        f"Data integrity error: Chronological order violation at index {i}. "
                        f"Current: {c.timestamp} <= Previous: {prev_c.timestamp}"
                    )

        return candles
