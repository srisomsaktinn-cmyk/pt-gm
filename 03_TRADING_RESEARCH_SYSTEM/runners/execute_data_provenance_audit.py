"""
Standalone runner for Data Provenance Audit.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.research.audit_data_provenance import run_full_provenance_audit

if __name__ == "__main__":
    run_full_provenance_audit()
