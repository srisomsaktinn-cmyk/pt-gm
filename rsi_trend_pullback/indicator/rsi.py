"""
Relative Strength Index (RSI) calculation using J. Welles Wilder's exact smoothing method.
Supports both batch calculation and bar-by-bar streaming calculation to prevent look-ahead bias.
"""

from typing import List, Optional, Tuple
import math


class WilderRSI:
    """
    Implements standard Wilder's RSI with Period = 14 (or configurable).

    Platform / Library Convention Documentation:
    -------------------------------------------
    - MT4 / MT5: Uses Wilder's Exponential Smoothing (MMA, alpha = 1/period).
    - TradingView (`ta.rsi`): Uses Wilder's Smoothing (RMA, alpha = 1/period).
    - TA-Lib (`RSI`): Uses Wilder's Smoothing.
    - Cutler's RSI (SMA-based) or Standard EMA (alpha = 2/(period+1)): NOT used here.
    
    This implementation matches Wilder's original formula and standard trading platforms.
    """

    def __init__(self, period: int = 14):
        if period < 1:
            raise ValueError(f"RSI period must be >= 1, got {period}")
        self.period: int = period
        self.reset()

    def reset(self) -> None:
        """
        Resets internal state for streaming calculations.
        """
        self._prev_close: Optional[float] = None
        self._gains_buffer: List[float] = []
        self._losses_buffer: List[float] = []
        self._avg_gain: Optional[float] = None
        self._avg_loss: Optional[float] = None
        self._bar_count: int = 0
        self._history_rsi: List[Optional[float]] = []

    def update(self, close_price: float) -> Optional[float]:
        """
        Updates the indicator with a new CLOSED candle close price.
        Returns the RSI value if warm-up is complete, else None.
        """
        self._bar_count += 1

        if self._prev_close is None:
            self._prev_close = close_price
            self._history_rsi.append(None)
            return None

        change = close_price - self._prev_close
        self._prev_close = close_price

        gain = max(change, 0.0)
        loss = max(-change, 0.0)

        # Initial warm-up: collect first `period` price changes
        if self._avg_gain is None:
            self._gains_buffer.append(gain)
            self._losses_buffer.append(loss)

            if len(self._gains_buffer) == self.period:
                # First average is simple arithmetic mean
                self._avg_gain = sum(self._gains_buffer) / self.period
                self._avg_loss = sum(self._losses_buffer) / self.period
                rsi = self._calculate_rsi_value(self._avg_gain, self._avg_loss)
                self._history_rsi.append(rsi)
                return rsi
            else:
                self._history_rsi.append(None)
                return None
        else:
            # Subsequent values use Wilder's recursive smoothing
            self._avg_gain = (self._avg_gain * (self.period - 1) + gain) / self.period
            self._avg_loss = (self._avg_loss * (self.period - 1) + loss) / self.period
            rsi = self._calculate_rsi_value(self._avg_gain, self._avg_loss)
            self._history_rsi.append(rsi)
            return rsi

    @staticmethod
    def _calculate_rsi_value(avg_gain: float, avg_loss: float) -> float:
        """
        Calculates RSI bounded [0.0, 100.0] handling zero division safely.
        """
        if avg_loss == 0.0:
            if avg_gain == 0.0:
                return 50.0  # No movement
            return 100.0
        if avg_gain == 0.0:
            return 0.0

        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return round(rsi, 6)

    @classmethod
    def calculate_series(cls, close_prices: List[float], period: int = 14) -> List[Optional[float]]:
        """
        Calculates RSI series over a list of close prices deterministically.
        Ensures exact identical output to streaming updates.
        """
        indicator = cls(period=period)
        results: List[Optional[float]] = []
        for price in close_prices:
            rsi_val = indicator.update(price)
            results.append(rsi_val)
        return results
