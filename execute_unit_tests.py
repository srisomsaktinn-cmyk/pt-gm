"""
Runner script to execute Strategy V2.6 Implementation Unit Tests.
"""

import unittest
from rsi_trend_pullback.tests.test_v26_implementation import TestStrategyV26Implementation

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStrategyV26Implementation)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    print("\nUnit Test Execution Finished.")
