"""
Standalone runner for V2.7 Missed Signal Auditor.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.monitoring.v27_missed_signal_auditor import V27MissedSignalAuditor

if __name__ == "__main__":
    auditor = V27MissedSignalAuditor()
    
    # Example Default: Audit offline intervals (e.g. daily outside 09:00-22:00 or past offline tests)
    # The auditor is configurable with any start/end datetime
    print("=" * 85)
    print("RUNNING STRATEGY V2.7 MISSED SIGNAL AUDITOR")
    print("=" * 85)
    
    res = auditor.audit_offline_period(2020, 2025)
    print(f"Total Offline Missed Signals: {res['total_missed_signals']}")
    print(f"Artifacts Generated: missed_signals.csv | missed_signal_summary.json | missed_signal_report.md")
    print("=" * 85)
