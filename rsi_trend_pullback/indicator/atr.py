"""
Wilder's Average True Range (ATR) indicator calculation.
Measures true volatility in absolute price points.
"""

from typing import List, Optional
from ..data.loader import Candle


class WilderATR:
    """
    Wilder's Average True Range (ATR) with standard 14-period recursive smoothing.
    Matches MT4, MT5, TradingView `ta.atr` exact calculation.
    """

    def __init__(self, period: int = 14):
        if period < 1:
            raise ValueError(f"ATR period must be >= 1, got {period}")
        self.period: int = period
        self.reset()

    def reset(self) -> None:
        self._prev_close: Optional[float] = None
        self._tr_buffer: List[float] = []
        self._current_atr: Optional[float] = None
        self._history: List[Optional[float]] = []

    def update(self, candle: Candle) -> Optional[float]:
        """
        Updates with closed candle (High, Low, Close).
        """
        high = candle.high
        low = candle.low
        close = candle.close

        if self._prev_close is None:
            # First bar True Range is simply High - Low
            tr = high - low
        else:
            tr = max(
                high - low,
                abs(high - self._prev_close),
                abs(low - self._prev_close)
            )

        self._prev_close = close

        if self._current_atr is None:
            self._tr_buffer.append(tr)
            if len(self._tr_buffer) == self.period:
                self._current_atr = sum(self._tr_buffer) / self.period
                self._history.append(round(self._current_atr, 4))
                return round(self._current_atr, 4)
            else:
                self._history.append(None)
                return None
        else:
            # Wilder's Smoothing: (prev_atr * (period - 1) + tr) / period
            self._current_atr = (self._current_atr * (self.period - 1) + tr) / self.period
            self._history.append(round(self._current_atr, 4))
            return round(self._current_atr, 4)

    @classmethod
    def calculate_series(cls, candles: List[Candle], period: int = 14) -> List[Optional[float]]:
        indicator = cls(period=period)
        return [indicator.update(c) for c in candles]
