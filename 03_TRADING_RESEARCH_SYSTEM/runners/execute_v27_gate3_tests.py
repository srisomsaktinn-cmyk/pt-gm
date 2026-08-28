"""
Standalone runner for V2.7 Gate 3 Unit Tests.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.tests.test_v27_gate3_calendar_engine import TestV27Gate3CalendarEngine

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestV27Gate3CalendarEngine)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
