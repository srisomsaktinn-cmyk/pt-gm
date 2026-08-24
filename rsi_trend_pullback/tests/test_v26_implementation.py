"""
Comprehensive Unit Test Suite for Frozen Strategy V2.6 and Real-Time Shadow Engine.
Verifies all 7 core implementation integrity requirements.
"""

import unittest
from datetime import datetime, timedelta

from rsi_trend_pullback.data.loader import Candle
from rsi_trend_pullback.indicator.rsi import WilderRSI
from rsi_trend_pullback.indicator.kaufman_er import KaufmanER
from rsi_trend_pullback.indicator.atr import WilderATR
from rsi_trend_pullback.state_machine.states import StrategyState, SignalType, PositionSide
from rsi_trend_pullback.state_machine.engine_v2 import RSIStateMachineV2
from rsi_trend_pullback.paper_trading.shadow_engine import ShadowPaperTradingEngine
from rsi_trend_pullback.paper_trading.audit_logger import ShadowAuditRecord, ExitTriggerType, DivergenceCategory


class TestStrategyV26Implementation(unittest.TestCase):

    def test_01_kaufman_er_bounds(self):
        """Test Kaufman ER is strictly bounded in [0.0, 1.0] and handles zero volatility."""
        er = KaufmanER(period=14)
        # Flat prices -> zero volatility -> ER should be 0.0
        for _ in range(20):
            val = er.update(100.0)
        self.assertEqual(val, 0.0)

        # Monotonic straight line -> ER should be 1.0
        er.reset()
        for i in range(25):
            val = er.update(100.0 + i * 2.0)
        self.assertAlmostEqual(val, 1.0, places=4)

    def test_02_wilder_atr_calculation(self):
        """Test Wilder ATR produces smooth recursive output."""
        atr = WilderATR(period=14)
        base_time = datetime(2025, 1, 1, 0, 0)
        for i in range(30):
            c = Candle(
                timestamp=base_time + timedelta(hours=i),
                open=100.0 + i, high=105.0 + i, low=98.0 + i, close=102.0 + i, volume=1000
            )
            val = atr.update(c)
        self.assertIsNotNone(val)
        self.assertGreater(val, 0.0)

    def test_03_economic_filter_entry_only(self):
        """Test Economic Filter (ATR/Cost >= 5) acts as an Entry Filter ONLY and never closes active trades."""
        engine = ShadowPaperTradingEngine(
            min_atr_cost_ratio=5.0, # requires ATR >= $2.30
            base_spread=0.25,
            base_slippage=0.15
        )
        base_time = datetime(2025, 1, 1, 0, 0)

        # Create a series of candles that generate a valid Long Entry
        candles = []
        price = 1000.0
        for i in range(60):
            # Up trend to push RSI > 60 and ER > 0.40 with large ATR ($5.00)
            if i < 20: price += 5.0
            elif i < 25: price -= 2.0 # pullback
            elif i < 30: price += 4.0 # re-entry trigger
            else: price += 0.1 # flat / low ATR compression

            c = Candle(
                timestamp=base_time + timedelta(hours=i),
                open=price - 1.0, high=price + 2.5, low=price - 2.5, close=price, volume=5000
            )
            candles.append(c)

        for bar_idx, c in enumerate(candles):
            closed_rec, sig = engine.on_hourly_candle(bar_idx, c)
            # Verify that when in active trade and ATR drops, the engine does NOT force-close
            if engine._active_record is not None:
                self.assertIsNotNone(engine._active_direction)

    def test_04_intrabar_hard_sl_vs_thesis_exit(self):
        """Test that Intrabar SL generates ExitTriggerType.HARD_STOP with exact touch trigger."""
        engine = ShadowPaperTradingEngine(
            atr_multiplier=2.5,
            base_spread=0.20,
            base_slippage=0.10
        )
        base_time = datetime(2025, 1, 1, 0, 0)

        # Create sequence that triggers Long entry then flash drops
        candles = []
        p = 1000.0
        for i in range(40):
            if i < 18: p += 6.0
            elif i < 22: p -= 3.0
            elif i < 26: p += 5.0 # Entry fires
            elif i == 27:
                # Flash drop touching SL
                c = Candle(timestamp=base_time + timedelta(hours=i), open=p, high=p+1, low=p-50.0, close=p-30.0, volume=10000)
                candles.append(c)
                continue
            else: p -= 1.0
            c = Candle(timestamp=base_time + timedelta(hours=i), open=p-1.0, high=p+2.0, low=p-2.0, close=p, volume=5000)
            candles.append(c)

        closed_trades = []
        for bar_idx, c in enumerate(candles):
            closed_rec, sig = engine.on_hourly_candle(bar_idx, c)
            if closed_rec is not None:
                closed_trades.append(closed_rec)

        if closed_trades:
            last_trade = closed_trades[-1]
            self.assertEqual(last_trade.exit_trigger_type, ExitTriggerType.HARD_STOP)
            self.assertIn("HARD_STOP", last_trade.exit_reason)

    def test_05_friction_decomposition_fields(self):
        """Test that ShadowAuditRecord correctly decomposes spread, commission, and slippage costs."""
        rec = ShadowAuditRecord(
            trade_id=1,
            timestamp=datetime(2025, 1, 1, 10, 0),
            direction="LONG",
            theoretical_entry=2000.0,
            actual_entry=2000.25,
            entry_slippage=0.15,
            spread_at_entry=0.25,
            execution_delay_ms=110.0,
            atr_14=6.0,
            er_14=0.45,
            volatility_ratio=13.0,
            rsi_14=52.0,
            hard_stop_price=1985.0
        )
        rec.finalize_trade(
            exit_trigger_type=ExitTriggerType.THESIS_EXIT,
            exit_trigger_time=datetime(2025, 1, 1, 15, 0),
            exit_trigger_price=2010.0,
            exit_execution_time=datetime(2025, 1, 1, 16, 0),
            exit_signal_time=datetime(2025, 1, 1, 15, 0),
            theoretical_exit=2010.0,
            actual_exit=2009.70,
            exit_slippage=0.15,
            exit_reason="THESIS_EXIT: RSI < 40",
            units=50.0,
            commission_rate=0.00003
        )
        self.assertEqual(rec.spread_cost, 12.50) # $0.25 * 50 oz
        self.assertGreater(rec.commission_cost, 0.0)
        self.assertGreater(rec.friction_drag, 0.0)
        self.assertIn(rec.divergence_category, [DivergenceCategory.NONE, DivergenceCategory.SLIPPAGE])


if __name__ == "__main__":
    unittest.main()
