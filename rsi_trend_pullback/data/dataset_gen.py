"""
Market data generators for testing and validation.
Generates deterministic synthetic datasets (trending, ranging, choppy, gaps)
and structured Dataset A (In-sample / Dev) & Dataset B (Out-of-sample).
"""

from datetime import datetime, timedelta
from typing import List
import math
import random
from .loader import Candle


class DatasetGenerator:
    """
    Generates deterministic synthetic market price series for reproducible testing.
    """

    @staticmethod
    def generate_sine_trend(
        start_date: datetime = datetime(2023, 1, 1, 0, 0),
        bars: int = 1000,
        base_price: float = 100.0,
        trend_slope: float = 0.05,
        cycle_period: int = 50,
        cycle_amp: float = 5.0,
        noise_level: float = 0.5,
        seed: int = 42
    ) -> List[Candle]:
        """
        Generates a synthetic price series with trend + periodic pullbacks + noise.
        """
        rng = random.Random(seed)
        candles: List[Candle] = []
        current_time = start_date
        price = base_price

        for i in range(bars):
            cycle = cycle_amp * math.sin(2 * math.pi * i / cycle_period)
            trend = trend_slope * i
            noise = rng.gauss(0, noise_level)
            
            target_close = base_price + trend + cycle + noise
            # Create plausible OHLC around target_close
            open_price = price
            close_price = max(1.0, target_close)
            
            # Intrabar range
            high_price = max(open_price, close_price) + abs(rng.gauss(0, 0.4))
            low_price = min(open_price, close_price) - abs(rng.gauss(0, 0.4))
            low_price = max(0.5, low_price)
            high_price = max(high_price, max(open_price, close_price))
            
            c = Candle(
                timestamp=current_time,
                open=round(open_price, 4),
                high=round(high_price, 4),
                low=round(low_price, 4),
                close=round(close_price, 4),
                volume=1000.0
            )
            candles.append(c)
            price = close_price
            current_time += timedelta(hours=1)

        return candles

    @staticmethod
    def generate_deterministic_dataset_a(bars: int = 2000) -> List[Candle]:
        """
        Dataset A: Development & Sanity testing (2020-2022 regime)
        Contains:
        1. Warmup period (bars 0-50)
        2. Bullish trend with pullbacks (bars 51-500)
        3. Choppy sideways regime (bars 501-1000)
        4. Bearish trend with pullbacks (bars 1001-1500)
        5. Strong trending with shallow pullbacks (bars 1501-2000)
        """
        rng = random.Random(101)
        start_date = datetime(2020, 1, 1, 0, 0)
        candles: List[Candle] = []
        current_time = start_date
        price = 100.0

        for i in range(bars):
            if i < 500:
                # Bullish regime
                drift = 0.08
                cycle = 3.5 * math.sin(2 * math.pi * i / 40)
            elif i < 1000:
                # Sideways choppy regime
                drift = 0.0
                cycle = 2.0 * math.sin(2 * math.pi * i / 15)
            elif i < 1500:
                # Bearish regime
                drift = -0.09
                cycle = 3.5 * math.sin(2 * math.pi * i / 45)
            else:
                # High volatility transition
                drift = 0.04
                cycle = 6.0 * math.sin(2 * math.pi * i / 60)

            noise = rng.gauss(0, 0.4)
            delta = drift + (cycle - (3.5 * math.sin(2 * math.pi * (i-1) / 40) if i > 0 and i < 500 else 0)) * 0.2 + noise
            open_price = price
            close_price = max(5.0, price + delta)
            high_price = max(open_price, close_price) + abs(rng.gauss(0, 0.3))
            low_price = min(open_price, close_price) - abs(rng.gauss(0, 0.3))
            low_price = max(1.0, low_price)

            candles.append(Candle(
                timestamp=current_time,
                open=round(open_price, 4),
                high=round(high_price, 4),
                low=round(low_price, 4),
                close=round(close_price, 4),
                volume=5000.0
            ))
            price = close_price
            current_time += timedelta(hours=1)

        return candles

    @staticmethod
    def generate_deterministic_dataset_b(bars: int = 2000) -> List[Candle]:
        """
        Dataset B: Out-of-Sample validation dataset (2023-2025 regime)
        Different random seed, structural shifts, regime transitions.
        """
        rng = random.Random(999)
        start_date = datetime(2023, 1, 1, 0, 0)
        candles: List[Candle] = []
        current_time = start_date
        price = 150.0

        for i in range(bars):
            if i < 400:
                # Prolonged choppy / low volatility
                drift = 0.005
                cycle = 1.8 * math.sin(2 * math.pi * i / 20)
            elif i < 1100:
                # Strong macro bull trend
                drift = 0.12
                cycle = 4.0 * math.sin(2 * math.pi * i / 50)
            elif i < 1600:
                # Sudden deep correction / bear crash
                drift = -0.15
                cycle = 5.0 * math.sin(2 * math.pi * i / 35)
            else:
                # High volatility ranging
                drift = 0.02
                cycle = 4.5 * math.sin(2 * math.pi * i / 25)

            noise = rng.gauss(0, 0.5)
            delta = drift + noise
            open_price = price
            close_price = max(5.0, price + delta)
            high_price = max(open_price, close_price) + abs(rng.gauss(0, 0.4))
            low_price = min(open_price, close_price) - abs(rng.gauss(0, 0.4))
            low_price = max(1.0, low_price)

            candles.append(Candle(
                timestamp=current_time,
                open=round(open_price, 4),
                high=round(high_price, 4),
                low=round(low_price, 4),
                close=round(close_price, 4),
                volume=8000.0
            ))
            price = close_price
            current_time += timedelta(hours=1)

        return candles
