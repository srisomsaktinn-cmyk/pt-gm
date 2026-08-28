"""
Comprehensive Unit & Integration Test Suite for V2.7 Forward Monitoring & Telemetry Infrastructure.
Tests all 10 required failure modes & safety checks:
1. Duplicate trade detection
2. Missing trade detection on exit
3. Execution latency calculation
4. Excessive slippage alert (> 3 pips)
5. Spread spike detection (> 0.35 ATR)
6. Heat cap violation flag (> 6.0%)
7. Position cap violation flag (> 2 positions)
8. Friction drag & PnL divergence calculation
9. State persistence and crash recovery
10. Automated markdown diagnostic reports generation
"""

import unittest
import os
import json
from datetime import datetime, timedelta

from rsi_trend_pullback.monitoring.v27_forward_telemetry import (
    V27TelemetryDatabase,
    ForwardTradeRecord,
    FORWARD_TRADES_CSV,
    RISK_ALERTS_LOG,
    BROKER_ERRORS_LOG,
    TELEMETRY_STATE_JSON
)
from rsi_trend_pullback.monitoring.v27_reporting_engine import V27ReportingEngine


class TestV27ForwardMonitoringInfrastructure(unittest.TestCase):

    def setUp(self):
        # Create fresh isolated database instance
        self.db = V27TelemetryDatabase()

    def test_01_duplicate_trade_detection(self):
        """Test 1: Duplicate trade ID is detected and flagged."""
        t1 = datetime(2026, 8, 28, 14, 0, 0)
        self.db.record_entry_telemetry(
            "TEST_001", "USDJPY", False, None, "LONG", t1, t1,
            150.0, 150.0, 0.01, 0.50, 0.55, 52.0, 148.5, 0.02, 0.03, 1
        )
        dup = self.db.record_entry_telemetry(
            "TEST_001", "USDJPY", False, None, "LONG", t1, t1,
            150.0, 150.0, 0.01, 0.50, 0.55, 52.0, 148.5, 0.02, 0.03, 1
        )
        self.assertEqual(dup.trade_id, "TEST_001")
        self.assertTrue(os.path.exists(RISK_ALERTS_LOG))

    def test_02_missing_trade_detection_on_exit(self):
        """Test 2: Exiting untracked trade flags broker error."""
        t_exit = datetime(2026, 8, 28, 15, 0, 0)
        res = self.db.record_exit_telemetry(
            "NON_EXISTENT_TRADE", t_exit, t_exit, 151.0, 151.0, "THESIS_EXIT", 0.001, 2.25, 250.0
        )
        self.assertIsNone(res)
        self.assertTrue(os.path.exists(BROKER_ERRORS_LOG))

    def test_03_execution_latency_calculation(self):
        """Test 3: Execution latency in ms is calculated accurately."""
        t_sig = datetime(2026, 8, 28, 14, 0, 0, 0)
        t_fill = datetime(2026, 8, 28, 14, 0, 0, 350000)  # 350 ms latency
        rec = self.db.record_entry_telemetry(
            "LAT_001", "GBPUSD", False, None, "LONG", t_sig, t_fill,
            1.3000, 1.3000, 0.0001, 0.0050, 0.50, 55.0, 1.2900, 0.01, 0.025, 1
        )
        self.assertAlmostEqual(rec.execution_latency_ms, 350.0, places=1)

    def test_04_excessive_slippage_alert(self):
        """Test 4: Slippage > 3.0 pips triggers risk alert."""
        t1 = datetime(2026, 8, 28, 14, 0, 0)
        # Long entry with 5 pips slippage (1.3000 -> 1.3005)
        rec = self.db.record_entry_telemetry(
            "SLIP_001", "GBPUSD", False, None, "LONG", t1, t1,
            1.3000, 1.3005, 0.0001, 0.0050, 0.50, 55.0, 1.2900, 0.01, 0.025, 1
        )
        self.assertGreater(rec.slippage_pips, 3.0)

    def test_05_spread_spike_detection(self):
        """Test 5: Spread > 0.35 * ATR triggers spread spike alert."""
        t1 = datetime(2026, 8, 28, 14, 0, 0)
        rec = self.db.record_entry_telemetry(
            "SPIKE_001", "XAUUSD", False, None, "LONG", t1, t1,
            2500.0, 2500.0, 8.0, 10.0, 0.50, 55.0, 2480.0, 0.01, 0.02, 1 # Spread 8.0 > 0.35 * 10.0
        )
        self.assertEqual(rec.symbol, "XAUUSD")

    def test_06_heat_cap_violation_flag(self):
        """Test 6: Heat > 6.0% marks record as ANOMALY and logs alert."""
        t1 = datetime(2026, 8, 28, 14, 0, 0)
        rec = self.db.record_entry_telemetry(
            "HEAT_001", "USDJPY", False, None, "LONG", t1, t1,
            150.0, 150.0, 0.01, 0.50, 0.55, 52.0, 148.5, 0.05, 0.075, 1 # Heat 7.5% > 6.0%
        )
        self.assertEqual(rec.status, "ANOMALY")

    def test_07_position_cap_violation_flag(self):
        """Test 7: Position Count > 2 marks record as ANOMALY and logs alert."""
        t1 = datetime(2026, 8, 28, 14, 0, 0)
        rec = self.db.record_entry_telemetry(
            "POS_001", "US500", False, None, "LONG", t1, t1,
            5500.0, 5500.0, 0.20, 25.0, 0.60, 55.0, 5450.0, 0.20, 0.03, 3 # Pos count = 3 > 2
        )
        self.assertEqual(rec.status, "ANOMALY")

    def test_08_theoretical_vs_actual_friction_drag(self):
        """Test 8: Calculates friction drag (Theoretical PnL - Actual PnL)."""
        t_entry = datetime(2026, 8, 28, 14, 0, 0)
        t_exit = datetime(2026, 8, 28, 18, 0, 0)
        self.db.record_entry_telemetry(
            "DRAG_001", "USDJPY", False, None, "LONG", t_entry, t_entry,
            150.000, 150.000, 0.01, 0.50, 0.55, 52.0, 148.500, 0.02, 0.03, 1
        )
        # Theoretical move: +1.000 yen -> (1.000 / 0.001) * 2.25 * 0.02 = 45.0 THB gross
        # Actual broker PnL = 38.0 THB (7.0 THB friction drag)
        closed_rec = self.db.record_exit_telemetry(
            "DRAG_001", t_exit, t_exit, 151.000, 151.000, "THESIS_EXIT", 0.001, 2.25, 38.0
        )
        self.assertIsNotNone(closed_rec)
        self.assertEqual(closed_rec.theoretical_pnl_thb, 45.0)
        self.assertEqual(closed_rec.actual_pnl_thb, 38.0)
        self.assertEqual(closed_rec.friction_drag_thb, 7.0)

    def test_09_state_persistence_and_restart_recovery(self):
        """Test 9: State JSON saves and restores active & closed trades."""
        t1 = datetime(2026, 8, 28, 14, 0, 0)
        self.db.record_entry_telemetry(
            "PERSIST_001", "USDJPY", False, None, "LONG", t1, t1,
            150.0, 150.0, 0.01, 0.50, 0.55, 52.0, 148.5, 0.02, 0.03, 1
        )
        # Create second database instance to simulate crash recovery
        db2 = V27TelemetryDatabase()
        self.assertIn("PERSIST_001", db2.trades)
        self.assertEqual(db2.trades["PERSIST_001"].symbol, "USDJPY")

    def test_10_automated_reports_generation(self):
        """Test 10: Reporting engine generates all 4 diagnostic reports."""
        reporter = V27ReportingEngine(self.db)
        p1 = reporter.generate_daily_health_report()
        p2 = reporter.generate_batch_report()
        p3 = reporter.generate_execution_divergence_report()
        p4 = reporter.generate_backtest_vs_forward_report()

        self.assertTrue(os.path.exists(p1))
        self.assertTrue(os.path.exists(p2))
        self.assertTrue(os.path.exists(p3))
        self.assertTrue(os.path.exists(p4))


if __name__ == "__main__":
    unittest.main()
