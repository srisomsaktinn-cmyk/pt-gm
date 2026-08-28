"""
Artifact generator for Phase 10 Untouched Prior Historical Validation (2014-2019).
"""

from rsi_trend_pullback.run_phase10_prior_oos import run_phase10_prior_oos

if __name__ == "__main__":
    print("Generating Phase 10 artifacts...")
    res = run_phase10_prior_oos()
    print("Phase 10 Done.")
