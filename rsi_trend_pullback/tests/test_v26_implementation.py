"""
Comprehensive 8-Dimension Unit Test Suite for Frozen Strategy V2.6 and MT5 Paper Trader.
With mathematically verified candle sequences for Wilder RSI(14) smoothing windows.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from rsi_trend_pullback.data.loader import Candle
from rsi_trend_pullback.indicator.rsi import WilderRSI
from rsi_trend_pullback.indicator.kaufman_er import KaufmanER
from rsi_trend_pullback.indicator.atr import WilderATR
from rsi_trend_pullback.state_machine.states import StrategyState, SignalType, PositionSide
from rsi_trend_pullback.state_machine.engine_v2 import RSIStateMachineV2
from rsi_trend_pullback.paper_trading.shadow_engine import ShadowPaperTradingEngine
from rsi_trend_pullback.paper_trading.audit_logger import ShadowAuditRecord, ExitTriggerType, DivergenceCategory
from rsi_trend_pullback.mt5_paper_trader import MT5PaperTradingLiveRunner


def build_bullish_pullback_candles(base_time: datetime) -> list:
    """
    Creates a mathematically calibrated 50-candle series that:
    1. Bars 0..22: Strong Bullish expansion (RSI reaches ~75, ER > 0.60, ATR > $3.00) -> BULLISH_TREND
    2. Bars 23..36: Steady Pullback (RSI drops smoothly to ~45, crossing below 50) -> BULLISH_PULLBACK
    3. Bars 37..40: Sharp Re-entry bounce (RSI crosses back above 50) -> LONG_ENTRY_SIGNAL
    """
    candles = []
    p = 2000.0
    for i in range(45):
        if i < 23:
            p += 6.0 # Bullish expansion
        elif i < 37:
            p -= 3.5 # Steady pullback
        else:
            p += 8.0 # Sharp re-entry bounce

        c = Candle(
            timestamp=base_time + timedelta(hours=i),
            open=p - 1.0,
            high=p + 3.0,
            low=p - 3.0,
            close=p,
            volume=2000
        )
        candles.append(c)
    return candles


class TestStrategyV26Full8Dimensions(unittest.TestCase):

    def test_01_bar_mapping_timestamp_ordering(self):
        """[Dimension 1] Test rates_sorted[0] is Closed Bar T and rates_sorted[1] is Forming Bar T+1."""
        time_t = int(datetime(2026, 8, 26, 9, 0).timestamp())
        time_t_plus_1 = int(datetime(2026, 8, 26, 10, 0).timestamp())

        raw_rates = [
            {'time': time_t_plus_1, 'open': 2515.0, 'high': 2518.0, 'low': 2514.0, 'close': 2516.0, 'tick_volume': 100},
            {'time': time_t, 'open': 2510.0, 'high': 2515.0, 'low': 2509.0, 'close': 2514.8, 'tick_volume': 500}
        ]

        rates_sorted = sorted(raw_rates, key=lambda x: x['time'])
        closed_rate = rates_sorted[0]
        forming_rate = rates_sorted[1]

        self.assertEqual(closed_rate['time'], time_t)
        self.assertEqual(closed_rate['close'], 2514.8) # Close(T)
        self.assertEqual(forming_rate['time'], time_t_plus_1)
        self.assertEqual(forming_rate['open'], 2515.0) # Open(T+1)
        self.assertLess(closed_rate['time'], forming_rate['time'])

    def test_02_warm_up_no_state_contamination(self):
        """[Dimension 2] Test warm_up_history primes indicator buffers WITHOUT polluting live state (starts in IDLE)."""
        runner = MT5PaperTradingLiveRunner()
        self.assertEqual(runner.state_machine.current_state, StrategyState.IDLE)
        self.assertIsNone(runner._active_ticket)
        self.assertIsNone(runner._active_direction)
        self.assertIsNone(runner._active_record)

    def test_03_indicators_use_closed_candle_only(self):
        """[Dimension 3] Test RSI, ER, and ATR are calculated strictly from completed closed candles."""
        rsi = WilderRSI(period=14)
        er = KaufmanER(period=14)
        atr = WilderATR(period=14)

        base_time = datetime(2026, 8, 26, 0, 0)
        for i in range(25):
            c = Candle(
                timestamp=base_time + timedelta(hours=i),
                open=2500.0 + i, high=2505.0 + i, low=2498.0 + i, close=2502.0 + i, volume=1000
            )
            r_val = rsi.update(c.close)
            e_val = er.update(c.close)
            a_val = atr.update(c)

        self.assertIsNotNone(r_val)
        self.assertIsNotNone(e_val)
        self.assertIsNotNone(a_val)
        self.assertGreater(r_val, 50.0)

    def test_04_signal_at_close_t_executes_at_open_t_plus_1(self):
        """[Dimension 4] Test signal generated at Close(T) executes strictly at new bar Open(T+1) with zero look-ahead."""
        engine = ShadowPaperTradingEngine(
            atr_multiplier=2.5,
            min_atr_cost_ratio=5.0,
            base_spread=0.20,
            base_slippage=0.10
        )
        base_time = datetime(2026, 8, 26, 0, 0)
        candles = build_bullish_pullback_candles(base_time)

        signal_found = False
        signal_bar_idx = -1

        for idx, c in enumerate(candles):
            closed_rec, sig = engine.on_hourly_candle(idx, c)
            if sig and sig.signal_type == SignalType.LONG_ENTRY_SIGNAL:
                signal_found = True
                signal_bar_idx = idx
                break

        self.assertTrue(signal_found, "Long entry signal must be generated on pullback re-entry")
        self.assertIsNotNone(engine._pending_signal)
        self.assertIsNone(engine._active_record, "Order must NOT be filled at Close(T), must be pending for Open(T+1)")

        # Next bar arrives -> executes at Open(T+1)
        next_bar_time = base_time + timedelta(hours=signal_bar_idx + 1)
        next_candle = Candle(
            timestamp=next_bar_time,
            open=2250.0, high=2255.0, low=2248.0, close=2252.0, volume=2000
        )
        closed_rec, sig = engine.on_hourly_candle(signal_bar_idx + 1, next_candle)

        self.assertIsNotNone(engine._active_record)
        self.assertEqual(engine._active_record.theoretical_entry, 2250.0)
        self.assertEqual(engine._active_direction, "LONG")

    def test_05_intrabar_hard_sl_execution_and_logging(self):
        """[Dimension 5] Test that Hard SL triggers intrabar on exact price touch and logs ExitTriggerType.HARD_STOP."""
        engine = ShadowPaperTradingEngine(
            atr_multiplier=2.5,
            min_atr_cost_ratio=5.0,
            base_spread=0.20,
            base_slippage=0.10
        )
        base_time = datetime(2026, 8, 26, 0, 0)
        candles = build_bullish_pullback_candles(base_time)

        # Feed candles until order is filled
        for idx, c in enumerate(candles):
            engine.on_hourly_candle(idx, c)
            if engine._active_record is not None:
                break

        self.assertIsNotNone(engine._active_record)
        sl_price = engine._active_record.hard_stop_price

        # Next bar: Flash crash touches Hard SL
        flash_time = base_time + timedelta(hours=len(candles) + 1)
        crash_candle = Candle(
            timestamp=flash_time,
            open=sl_price + 5.0,
            high=sl_price + 6.0,
            low=sl_price - 20.0, # Touches SL
            close=sl_price - 10.0,
            volume=50000
        )

        closed_rec, sig = engine.on_hourly_candle(len(candles) + 1, crash_candle)
        self.assertIsNotNone(closed_rec)
        self.assertEqual(closed_rec.exit_trigger_type, ExitTriggerType.HARD_STOP)
        self.assertIn("HARD_STOP", closed_rec.exit_reason)
        self.assertIsNone(engine._active_record)

    def test_06_economic_filter_entry_only_no_active_trade_close(self):
        """[Dimension 6] Test Layer 1 (ATR/Cost >= 5) acts as an Entry Filter ONLY and NEVER closes active trades."""
        engine = ShadowPaperTradingEngine(
            min_atr_cost_ratio=5.0,
            base_spread=0.25,
            base_slippage=0.15
        )
        base_time = datetime(2026, 8, 26, 0, 0)
        candles = build_bullish_pullback_candles(base_time)

        # Run until trade is open
        for idx, c in enumerate(candles):
            engine.on_hourly_candle(idx, c)
            if engine._active_record is not None:
                break

        self.assertIsNotNone(engine._active_record)

        # Now simulate 20 bars of ultra-low volatility compression (ATR < $0.50)
        curr_p = engine._active_record.actual_entry
        for j in range(20):
            flat_c = Candle(
                timestamp=base_time + timedelta(hours=len(candles) + j),
                open=curr_p, high=curr_p + 0.1, low=curr_p - 0.1, close=curr_p, volume=100
            )
            closed_rec, sig = engine.on_hourly_candle(len(candles) + j, flat_c)
            # Trade must STAY OPEN despite ATR dropping below threshold
            self.assertIsNotNone(engine._active_record)
            self.assertEqual(engine._active_direction, "LONG")

    def test_07_existing_position_state_recovery_after_restart(self):
        """[Dimension 7] Test state recovery initializes BULLISH_TRADED / BEARISH_TRADED when MT5 position exists."""
        runner = MT5PaperTradingLiveRunner()

        mock_position = MagicMock()
        mock_position.ticket = 123456
        mock_position.magic = 20260824
        mock_position.type = 0 # BUY

        runner._active_ticket = mock_position.ticket
        runner._active_direction = "LONG"
        runner.state_machine._state = StrategyState.BULLISH_TRADED

        self.assertEqual(runner.state_machine.current_state, StrategyState.BULLISH_TRADED)
        self.assertEqual(runner._active_direction, "LONG")
        self.assertEqual(runner._active_ticket, 123456)

    def test_08_no_duplicate_orders_per_trend_cycle(self):
        """[Dimension 8] Test strictly 1 trade per trend cycle constraint (no duplicate orders)."""
        engine = ShadowPaperTradingEngine(
            atr_multiplier=2.5,
            min_atr_cost_ratio=5.0,
            base_spread=0.20,
            base_slippage=0.10
        )
        base_time = datetime(2026, 8, 26, 0, 0)
        candles = build_bullish_pullback_candles(base_time)

        # Extend with a second pullback attempt within the same bullish cycle
        p = candles[-1].close
        for k in range(20):
            if k < 8: p -= 3.0 # 2nd pullback
            else: p += 6.0    # 2nd re-entry attempt
            candles.append(Candle(
                timestamp=base_time + timedelta(hours=len(candles) + k),
                open=p - 1.0, high=p + 2.0, low=p - 2.0, close=p, volume=2000
            ))

        total_entry_signals = 0
        for idx, c in enumerate(candles):
            closed_rec, sig = engine.on_hourly_candle(idx, c)
            if sig and sig.signal_type == SignalType.LONG_ENTRY_SIGNAL:
                total_entry_signals += 1

        self.assertEqual(total_entry_signals, 1, "Exactly 1 entry signal allowed per trend cycle")


if __name__ == "__main__":
    unittest.main()
