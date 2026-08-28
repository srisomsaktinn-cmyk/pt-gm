"""
Execution script to generate XAUUSD CSVs, trade logs, and export all results.
"""

from rsi_trend_pullback.run_xauusd_phase9 import run_phase9_xauusd

if __name__ == "__main__":
    results = run_phase9_xauusd()
    print("XAUUSD Phase 9 Execution Complete.")
