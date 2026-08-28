"""
Standalone runner for V2.7 Personal Schedule Coverage Analysis.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.analytics.v27_personal_coverage_analyzer import run_personal_coverage_analysis

if __name__ == "__main__":
    run_personal_coverage_analysis()
