"""
Kaufman Efficiency Ratio (ER) indicator implementation.
Measures price directional speed vs noise volatility over N bars.
Bounded strictly in [0.0, 1.0].
"""

from typing import List, Optional
import math


class KaufmanER:
    """
    Kaufman Efficiency Ratio (ER) Calculator.
    
    Formula:
      Change = |Close_t - Close_{t - period}|
      Volatility = sum_{i=0}^{period-1} |Close_{t-i} - Close_{t-i-1}|
      ER = Change / Volatility
    """

    def __init__(self, period: int = 14):
        if period < 1:
            raise ValueError(f"ER period must be >= 1, got {period}")
        self.period: int = period
        self.reset()

    def reset(self) -> None:
        self._price_history: List[float] = []

    def update(self, close_price: float) -> Optional[float]:
        """
        Updates with closed candle close price.
        Returns ER in [0.0, 1.0] if history >= period + 1, else None.
        """
        self._price_history.append(close_price)
        if len(self._price_history) <= self.period:
            return None

        # Net directional price change over `period` bars
        net_change = abs(close_price - self._price_history[-1 - self.period])

        # Sum of absolute 1-bar price changes over `period` bars
        total_volatility = 0.0
        for i in range(len(self._price_history) - self.period, len(self._price_history)):
            total_volatility += abs(self._price_history[i] - self._price_history[i - 1])

        if total_volatility == 0.0:
            return 0.0

        er = net_change / total_volatility
        return round(er, 6)

    @classmethod
    def calculate_series(cls, close_prices: List[float], period: int = 14) -> List[Optional[float]]:
        indicator = cls(period=period)
        return [indicator.update(p) for p in close_prices]
