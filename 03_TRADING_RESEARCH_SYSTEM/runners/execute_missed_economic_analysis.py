"""
Standalone runner for V2.7 Missed Signal Economic Value Analysis.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.analytics.v27_missed_economic_analyzer import run_economic_value_analysis

if __name__ == "__main__":
    run_economic_value_analysis()
