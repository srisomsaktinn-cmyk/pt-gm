"""
Runner for V2.7 Official Baseline Backtest.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.research.run_v27_official_baseline_backtest import (
    run_v27_official_baseline_backtest,
    print_official_baseline_report
)

if __name__ == "__main__":
    results = run_v27_official_baseline_backtest()
    print_official_baseline_report(results)
