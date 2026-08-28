"""
Standalone runner for Strategy V2.7 Master Robustness Suite.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.research.v27_robustness_stress_oos_suite import execute_master_robustness_suite

if __name__ == "__main__":
    execute_master_robustness_suite()
