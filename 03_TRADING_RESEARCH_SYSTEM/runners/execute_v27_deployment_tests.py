"""
Standalone runner for V2.7 Deployment Safety Tests.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.tests.test_v27_demo_deployment_safety import TestV27DemoDeploymentSafety

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestV27DemoDeploymentSafety)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
