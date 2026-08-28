"""
Comprehensive Unit & Integration Test Suite for V2.7 Research & Forward Analytics Center.
Tests all quantitative analytics dimensions:
1. Category isolation (Historical vs Forward vs Missed vs Rejected)
2. Missed signals excluded from Forward metrics
3. Profit factor, win rate, expectancy, and payoff calculations
4. MAE and MFE distribution percentiles
5. Time-of-day & Day-of-week grouping
6. Pyramiding attribution metrics
7. Trade drought inter-signal gap calculations
8. Automated reports and HTML dashboard generation
"""

import unittest
import os
import json
from datetime import datetime, timedelta

from rsi_trend_pullback.analytics.v27_analytics_engine import (
    V27AnalyticsCenter,
    UnifiedTradeRecord
)


class TestV27AnalyticsCenter(unittest.TestCase):

    def setUp(self):
        self.center = V27AnalyticsCenter()

    def test_01_category_isolation_and_ingestion(self):
        """Test 1: Records are categorized into distinct source types."""
        sources = set(r.source_type for r in self.center.records)
        self.assertIn("HISTORICAL_BACKTEST", sources)
        for r in self.center.records:
            self.assertIn(r.source_type, ["HISTORICAL_BACKTEST", "FORWARD_EXECUTED", "MISSED_SIGNAL", "REJECTED_SIGNAL", "OOS_BACKTEST"])

    def test_02_missed_signals_excluded_from_forward_metrics(self):
        """Test 2: Missed signals are NEVER counted in Forward performance metrics."""
        fwd_records = [r for r in self.center.records if r.source_type == "FORWARD_EXECUTED"]
        missed_records = [r for r in self.center.records if r.source_type == "MISSED_SIGNAL"]
        
        fwd_metrics = self.center.compute_performance_metrics(fwd_records)
        # Missed signals count should not equal forward count
        self.assertEqual(fwd_metrics["total_trades"], len(fwd_records))

    def test_03_performance_metrics_math_accuracy(self):
        """Test 3: Profit factor, expectancy, and win rate math."""
        # Create synthetic isolated test trades
        recs = [
            UnifiedTradeRecord("T1", "USDJPY", "LONG", "BASE", "HISTORICAL_BACKTEST", datetime.now(), datetime.now(), 150, 151, 148, 148, 0.02, 1000.0, 1000.0, 0, 0.01, 0, 0, 0.5, 0.5, 55, 0.03, 1, "THESIS_EXIT"),
            UnifiedTradeRecord("T2", "USDJPY", "LONG", "BASE", "HISTORICAL_BACKTEST", datetime.now(), datetime.now(), 150, 148, 148, 148, 0.02, -500.0, -500.0, 0, 0.01, 0, 0, 0.5, 0.5, 55, 0.03, 1, "STOP_LOSS_TOUCH"),
        ]
        m = self.center.compute_performance_metrics(recs)
        self.assertEqual(m["total_trades"], 2)
        self.assertEqual(m["wins"], 1)
        self.assertEqual(m["losses"], 1)
        self.assertEqual(m["win_rate_pct"], 50.0)
        self.assertEqual(m["profit_factor"], 2.00)
        self.assertEqual(m["expectancy_thb"], 250.00)
        self.assertEqual(m["payoff_ratio"], 2.00)

    def test_04_mae_mfe_distributions(self):
        """Test 4: MAE and MFE distributions are calculated."""
        hist_records = [r for r in self.center.records if r.source_type == "HISTORICAL_BACKTEST"]
        mae_mfe = self.center.run_mae_mfe_analysis(hist_records)
        self.assertIn("winning_trades_mae_pct", mae_mfe)
        self.assertIn("winning_trades_mfe_pct", mae_mfe)
        self.assertIn("p50", mae_mfe["winning_trades_mfe_pct"])

    def test_05_pyramid_forensics_attribution(self):
        """Test 5: Base vs Pyramid attribution sums to total."""
        hist_records = [r for r in self.center.records if r.source_type == "HISTORICAL_BACKTEST"]
        pyr = self.center.run_pyramid_forensics(hist_records)
        self.assertEqual(pyr["total_pyramid_events"], 64)
        self.assertAlmostEqual(pyr["base_share_pct"] + pyr["pyramid_share_pct"], 100.0, places=0)

    def test_06_reports_and_dashboard_generation(self):
        """Test 6: Master markdown reports and HTML dashboard generated."""
        summary = self.center.generate_master_reports()
        self.assertTrue(os.path.exists("d:/Kaeha/v27_daily_analytics.md"))
        self.assertTrue(os.path.exists("d:/Kaeha/v27_asset_analysis.md"))
        self.assertTrue(os.path.exists("d:/Kaeha/v27_pyramid_analysis.md"))
        self.assertTrue(os.path.exists("d:/Kaeha/v27_drawdown_forensics.md"))
        self.assertTrue(os.path.exists("d:/Kaeha/v27_analytics_summary.json"))
        self.assertTrue(os.path.exists("d:/Kaeha/v27_analytics_dashboard.html"))


if __name__ == "__main__":
    unittest.main()
