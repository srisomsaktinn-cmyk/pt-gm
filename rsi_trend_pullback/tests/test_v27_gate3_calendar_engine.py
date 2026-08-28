"""
Unit Test Suite for Strategy V2.7 Research Candidate - Gate 3 (Multi-Asset Independent Calendar Engine).
Tests all 14 required edge cases:
1. Asset A has a bar while Asset B is closed.
2. Asset A has a session break (US500).
3. BTC trades 24/7 during FX weekend closure.
4. Weekend transition gap recognition.
5. Missing candle detection (flagged without synthetic repair).
6. Duplicate timestamp rejection.
7. Two assets signal simultaneously.
8. Three assets signal simultaneously (deterministic selection).
9. Four assets signal simultaneously.
10. Five assets signal simultaneously.
11. Heat cap rejects valid signal.
12. Position cap rejects valid signal.
13. Same ER -> compare Spread/ATR ratio.
14. Same ER and same Spread/ATR -> Canonical Alphabetical Symbol tie-break.
"""

import unittest
from datetime import datetime, timedelta
from rsi_trend_pullback.data.loader import Candle
from rsi_trend_pullback.research.portfolio_heat_engine import ActivePosition, CandidateSignal
from rsi_trend_pullback.research.multi_asset_calendar_engine import (
    ASSET_SPECS,
    SessionType,
    IndependentAssetStream,
    MultiAssetCalendarCoordinator
)


class TestV27Gate3CalendarEngine(unittest.TestCase):

    def setUp(self):
        self.coordinator = MultiAssetCalendarCoordinator()
        self.equity = 10000.0  # 10,000 THB

    def test_01_asset_a_has_bar_while_asset_b_closed(self):
        """Verifies BTC processes Saturday bar while Forex markets are closed."""
        saturday_dt = datetime(2026, 8, 22, 12, 0, 0)  # Saturday 12:00 UTC

        btc_open = self.coordinator.streams["BTCUSD"].is_market_open(saturday_dt)
        fx_open = self.coordinator.streams["USDJPY"].is_market_open(saturday_dt)

        self.assertTrue(btc_open, "BTC must be open 24/7 on Saturday")
        self.assertFalse(fx_open, "Forex must be closed on Saturday")

    def test_02_asset_a_has_session_break(self):
        """Verifies US500 daily session break is recognized."""
        break_dt = datetime(2026, 8, 20, 21, 30, 0)  # Thursday 21:30 UTC
        us500_open = self.coordinator.streams["US500"].is_market_open(break_dt)
        self.assertFalse(us500_open, "US500 must recognize daily session break at 21:30 UTC")

    def test_03_btc_trades_24_7_during_fx_weekend_closure(self):
        """Verifies BTC stream ingests Saturday candles without disturbing Forex streams."""
        saturday_c = Candle(
            timestamp=datetime(2026, 8, 22, 10, 0, 0),
            open=60000.0, high=60500.0, low=59800.0, close=60200.0, volume=150.0
        )

        res = self.coordinator.process_event_step(
            event_timestamp=saturday_c.timestamp,
            active_candles={"BTCUSD": saturday_c},
            active_positions=[],
            equity=self.equity
        )

        self.assertEqual(res["candles_processed_count"], 1)
        self.assertEqual(self.coordinator.streams["BTCUSD"].integrity_report.total_bars_processed, 1)
        self.assertEqual(self.coordinator.streams["USDJPY"].integrity_report.total_bars_processed, 0)

    def test_04_weekend_transition_gap(self):
        """Verifies Friday 21:00 to Sunday 22:00 gap is recorded as weekend gap, not missing bars."""
        stream = self.coordinator.streams["USDJPY"]
        fri_c = Candle(datetime(2026, 8, 21, 21, 0, 0), 150.0, 150.5, 149.8, 150.2, 100.0)  # Fri
        sun_c = Candle(datetime(2026, 8, 23, 22, 0, 0), 150.3, 150.8, 150.1, 150.6, 100.0)  # Sun

        stream.process_candle(fri_c)
        stream.process_candle(sun_c)

        self.assertEqual(stream.integrity_report.weekend_gaps_detected, 1)
        self.assertEqual(stream.integrity_report.missing_bars_flagged, 0, "Weekend jump must not count as missing bars")

    def test_05_missing_candle_detection(self):
        """Verifies Tuesday 4-hour gap is explicitly flagged as 3 missing bars without synthetic repair."""
        stream = self.coordinator.streams["XAUUSD"]
        c1 = Candle(datetime(2026, 8, 18, 10, 0, 0), 2500.0, 2505.0, 2498.0, 2502.0, 100.0)
        c2 = Candle(datetime(2026, 8, 18, 14, 0, 0), 2504.0, 2510.0, 2502.0, 2508.0, 100.0)

        stream.process_candle(c1)
        stream.process_candle(c2)

        self.assertEqual(stream.integrity_report.missing_bars_flagged, 3)
        self.assertIn("MISSING_BARS: 3 bars", stream.integrity_report.anomalies[0])

    def test_06_duplicate_timestamp_rejection(self):
        """Verifies duplicate timestamp is rejected and incremented in report."""
        stream = self.coordinator.streams["GBPUSD"]
        c = Candle(datetime(2026, 8, 19, 12, 0, 0), 1.30, 1.31, 1.29, 1.305, 100.0)

        sig1 = stream.process_candle(c)
        sig2 = stream.process_candle(c)  # Duplicate

        self.assertEqual(stream.integrity_report.duplicate_timestamps_rejected, 1)
        self.assertEqual(stream.integrity_report.total_bars_processed, 1)

    def test_07_two_assets_signal_simultaneously(self):
        """Verifies 2 simultaneous signals are both accepted when positions are empty."""
        cand_jpy = CandidateSignal("USDJPY", False, "LONG", 150.0, 149.0, 0.01, 0.001, 2.25, 10.0, er_14=0.55, spread_atr_ratio=0.08)
        cand_xau = CandidateSignal("XAUUSD", False, "LONG", 2500.0, 2480.0, 0.01, 0.01, 0.35, 10.0, er_14=0.48, spread_atr_ratio=0.05)

        results = self.coordinator.streams["USDJPY"].state_machine  # checking coordinator helper
        res = self.coordinator.process_event_step(
            event_timestamp=datetime(2026, 8, 19, 15, 0, 0),
            active_candles={},
            active_positions=[],
            equity=self.equity
        )
        # Directly test collision resolution via engine
        from rsi_trend_pullback.research.portfolio_heat_engine import PortfolioHeatEngineGate2
        coll_res = PortfolioHeatEngineGate2.resolve_signal_collisions([], [cand_jpy, cand_xau], self.equity)

        self.assertTrue(coll_res[0][1], "1st signal must be accepted")
        self.assertTrue(coll_res[1][1], "2nd signal must be accepted")

    def test_08_three_assets_signal_simultaneously(self):
        """Verifies 3 simultaneous signals accept top 2 by ER and reject 3rd."""
        cands = [
            CandidateSignal("XAUUSD", False, "LONG", 2500.0, 2480.0, 0.01, 0.01, 0.35, 10.0, er_14=0.42, spread_atr_ratio=0.05),
            CandidateSignal("USDJPY", False, "LONG", 150.0, 149.0, 0.01, 0.001, 2.25, 10.0, er_14=0.60, spread_atr_ratio=0.08),
            CandidateSignal("US500",  False, "LONG", 5500.0, 5450.0, 0.20, 0.01, 0.35, 10.0, er_14=0.51, spread_atr_ratio=0.06),
        ]
        from rsi_trend_pullback.research.portfolio_heat_engine import PortfolioHeatEngineGate2
        res = PortfolioHeatEngineGate2.resolve_signal_collisions([], cands, self.equity)

        self.assertEqual(res[0][0].symbol, "USDJPY")
        self.assertTrue(res[0][1], "USDJPY (ER 0.60) Accepted")

        self.assertEqual(res[1][0].symbol, "US500")
        self.assertTrue(res[1][1], "US500 (ER 0.51) Accepted")

        self.assertEqual(res[2][0].symbol, "XAUUSD")
        self.assertFalse(res[2][1], "XAUUSD (ER 0.42) Rejected by position count cap")

    def test_09_four_assets_signal_simultaneously(self):
        """Verifies 4 simultaneous signals accept top 2 and reject bottom 2."""
        cands = [
            CandidateSignal("GBPUSD", False, "LONG", 1.30, 1.29, 0.01, 0.0001, 2.25, 10.0, er_14=0.41, spread_atr_ratio=0.09),
            CandidateSignal("XAUUSD", False, "LONG", 2500.0, 2480.0, 0.01, 0.01, 0.35, 10.0, er_14=0.44, spread_atr_ratio=0.05),
            CandidateSignal("BTCUSD", False, "LONG", 60000.0, 59000.0, 0.01, 0.01, 0.35, 10.0, er_14=0.55, spread_atr_ratio=0.12),
            CandidateSignal("USDJPY", False, "LONG", 150.0, 149.0, 0.01, 0.001, 2.25, 10.0, er_14=0.62, spread_atr_ratio=0.08),
        ]
        from rsi_trend_pullback.research.portfolio_heat_engine import PortfolioHeatEngineGate2
        res = PortfolioHeatEngineGate2.resolve_signal_collisions([], cands, self.equity)

        self.assertEqual([r[0].symbol for r in res if r[1]], ["USDJPY", "BTCUSD"])
        self.assertEqual([r[0].symbol for r in res if not r[1]], ["XAUUSD", "GBPUSD"])

    def test_10_five_assets_signal_simultaneously(self):
        """Verifies 5 simultaneous signals accept top 2 and reject bottom 3 deterministically."""
        cands = [
            CandidateSignal("GBPUSD", False, "LONG", 1.30, 1.29, 0.01, 0.0001, 2.25, 10.0, er_14=0.41, spread_atr_ratio=0.09),
            CandidateSignal("XAUUSD", False, "LONG", 2500.0, 2480.0, 0.01, 0.01, 0.35, 10.0, er_14=0.44, spread_atr_ratio=0.05),
            CandidateSignal("US500",  False, "LONG", 5500.0, 5450.0, 0.20, 0.01, 0.35, 10.0, er_14=0.49, spread_atr_ratio=0.06),
            CandidateSignal("BTCUSD", False, "LONG", 60000.0, 59000.0, 0.01, 0.01, 0.35, 10.0, er_14=0.55, spread_atr_ratio=0.12),
            CandidateSignal("USDJPY", False, "LONG", 150.0, 149.0, 0.01, 0.001, 2.25, 10.0, er_14=0.62, spread_atr_ratio=0.08),
        ]
        from rsi_trend_pullback.research.portfolio_heat_engine import PortfolioHeatEngineGate2
        res = PortfolioHeatEngineGate2.resolve_signal_collisions([], cands, self.equity)

        self.assertEqual([r[0].symbol for r in res if r[1]], ["USDJPY", "BTCUSD"])
        self.assertEqual(len([r for r in res if not r[1]]), 3)

    def test_11_heat_cap_rejects_valid_signal(self):
        """Verifies heat cap rejects order if projected heat > 6.0%."""
        active = [ActivePosition("USDJPY", False, "LONG", 150.0, 150.0, 148.5, 0.01, 0.001, 2.25, 0.0)]  # 337.5 THB
        cand = CandidateSignal("XAUUSD", False, "LONG", 2500.0, 2460.0, 0.01, 0.01, 0.35, 0.0, er_14=0.50, spread_atr_ratio=0.05)  # 1400 ticks * 0.35 * 0.01 = 490 THB
        # Total = 337.5 + 490 = 827.5 THB = 8.27% > 6.0%
        from rsi_trend_pullback.research.portfolio_heat_engine import PortfolioHeatEngineGate2
        accepted, reason, proj_heat = PortfolioHeatEngineGate2.can_accept_order(active, cand, self.equity)
        self.assertFalse(accepted)
        self.assertIn("HEAT_CAP_EXCEEDED", reason)

    def test_12_position_cap_rejects_valid_signal(self):
        """Verifies position cap rejects 3rd signal even when heat is very low."""
        active = [
            ActivePosition("USDJPY", False, "LONG", 150.0, 151.0, 150.0, 0.01, 0.001, 2.25, 10.0),
            ActivePosition("GBPUSD", False, "LONG", 1.30, 1.31, 1.30, 0.01, 0.0001, 2.25, 10.0)
        ]
        cand = CandidateSignal("XAUUSD", False, "LONG", 2500.0, 2490.0, 0.01, 0.01, 0.35, 10.0, er_14=0.60, spread_atr_ratio=0.05)
        from rsi_trend_pullback.research.portfolio_heat_engine import PortfolioHeatEngineGate2
        accepted, reason, _ = PortfolioHeatEngineGate2.can_accept_order(active, cand, self.equity)
        self.assertFalse(accepted)
        self.assertIn("POSITION_CAP_EXCEEDED", reason)

    def test_13_same_er_compares_spread_atr_ratio(self):
        """Clean 3-Tier Tiebreaker: When ER14 is identical, lower Spread/ATR wins priority."""
        # Active slot 1 taken
        active = [ActivePosition("BTCUSD", False, "LONG", 60000.0, 61000.0, 60000.0, 0.01, 0.01, 0.35, 10.0)]

        # Two signals with IDENTICAL ER = 0.5000
        # XAUUSD: Spread/ATR = 0.25 / 15.0 = 0.0167 (Cheaper friction)
        # USDJPY: Spread/ATR = 0.010 / 0.20 = 0.0500 (Higher friction)
        cand_jpy = CandidateSignal("USDJPY", False, "LONG", 150.0, 149.0, 0.01, 0.001, 2.25, 10.0, er_14=0.5000, spread_atr_ratio=0.0500)
        cand_xau = CandidateSignal("XAUUSD", False, "LONG", 2500.0, 2480.0, 0.01, 0.01, 0.35, 10.0, er_14=0.5000, spread_atr_ratio=0.0167)

        from rsi_trend_pullback.research.portfolio_heat_engine import PortfolioHeatEngineGate2
        res = PortfolioHeatEngineGate2.resolve_signal_collisions(active, [cand_jpy, cand_xau], self.equity)

        # XAUUSD has lower spread/ATR ratio (0.0167 < 0.0500) -> XAUUSD must win priority
        self.assertEqual(res[0][0].symbol, "XAUUSD")
        self.assertTrue(res[0][1], "XAUUSD must be accepted due to lower Spread/ATR ratio")

        self.assertEqual(res[1][0].symbol, "USDJPY")
        self.assertFalse(res[1][1], "USDJPY must be rejected due to Position Cap = 2")

    def test_14_same_er_and_same_spread_atr_canonical_alphabetical_tiebreak(self):
        """Clean 3-Tier Tiebreaker: When ER and Spread/ATR are identical, Alphabetical symbol order breaks tie."""
        active = [ActivePosition("BTCUSD", False, "LONG", 60000.0, 61000.0, 60000.0, 0.01, 0.01, 0.35, 10.0)]

        # Two signals with IDENTICAL ER = 0.4500 and IDENTICAL Spread/ATR = 0.0500
        cand_us500 = CandidateSignal("US500", False, "LONG", 5500.0, 5450.0, 0.20, 0.01, 0.35, 10.0, er_14=0.4500, spread_atr_ratio=0.0500)
        cand_gbpusd = CandidateSignal("GBPUSD", False, "SHORT", 1.30, 1.31, 0.01, 0.0001, 2.25, 10.0, er_14=0.4500, spread_atr_ratio=0.0500)

        from rsi_trend_pullback.research.portfolio_heat_engine import PortfolioHeatEngineGate2
        res = PortfolioHeatEngineGate2.resolve_signal_collisions(active, [cand_us500, cand_gbpusd], self.equity)

        # Alphabetical: "GBPUSD" comes before "US500" -> GBPUSD wins tiebreaker
        self.assertEqual(res[0][0].symbol, "GBPUSD")
        self.assertTrue(res[0][1], "GBPUSD must win alphabetical tiebreaker over US500")

        self.assertEqual(res[1][0].symbol, "US500")
        self.assertFalse(res[1][1], "US500 must be rejected due to Position Cap = 2")


if __name__ == "__main__":
    unittest.main()
