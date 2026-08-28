"""
Standalone runner for V2.7 Forward Monitoring & Telemetry Test Suite.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.tests.test_v27_forward_monitoring import TestV27ForwardMonitoringInfrastructure

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestV27ForwardMonitoringInfrastructure)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
