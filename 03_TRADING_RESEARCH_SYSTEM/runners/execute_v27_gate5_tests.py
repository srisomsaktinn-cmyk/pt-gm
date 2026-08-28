"""
Standalone runner for V2.7 Gate 5 Final Integrity Audit Tests.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.tests.test_v27_gate5_integrity_suite import TestV27Gate5IntegritySuite

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestV27Gate5IntegritySuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
