"""
Standalone runner for V2.7 Accounting & Attribution Audit.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.research.audit_v27_baseline_accounting import (
    perform_full_accounting_audit,
    print_accounting_audit_report
)

if __name__ == "__main__":
    audit_data = perform_full_accounting_audit()
    print_accounting_audit_report(audit_data)
