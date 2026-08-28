"""
Runner for 203,650 THB Exact Reconciliation.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.research.reconcile_203650_attribution import run_exact_reconciliation

if __name__ == "__main__":
    run_exact_reconciliation()
