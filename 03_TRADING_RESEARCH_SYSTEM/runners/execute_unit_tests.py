"""
Runner script to execute Strategy V2.6 Full 8-Dimension Implementation Unit Tests.
"""

import unittest
from rsi_trend_pullback.tests.test_v26_implementation import TestStrategyV26Full8Dimensions

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStrategyV26Full8Dimensions)
    runner = unittest.TextTestRunner(verbosity=2)
    print("=" * 80)
    print("RUNNING STRATEGY V2.6 FULL 8-DIMENSION UNIT TEST SUITE")
    print("=" * 80)
    res = runner.run(suite)
    print("=" * 80)
    if res.wasSuccessful():
        print(f"[RESULT] ALL {res.testsRun} TESTS PASSED SUCCESSFULLY (0 Errors, 0 Failures)")
    else:
        print(f"[RESULT] FAILED ({len(res.failures)} Failures, {len(res.errors)} Errors)")
    print("=" * 80)
