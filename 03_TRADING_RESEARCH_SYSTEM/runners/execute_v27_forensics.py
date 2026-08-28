"""
Runner for V2.7 Performance Forensics.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.research.v27_performance_forensics import (
    run_performance_forensics,
    print_forensics_report
)

if __name__ == "__main__":
    res = run_performance_forensics()
    print_forensics_report(res)
