"""
Complete analysis script for V1 vs V2 Controlled Experiment.
Calculates all side-by-side tables, duration buckets, regime analytics,
and exports the comprehensive report.
"""

from rsi_trend_pullback.run_v1_vs_v2_comparison import run_v1_vs_v2_experiment

if __name__ == "__main__":
    print("Running V1 vs V2 Controlled Experiment...")
    res = run_v1_vs_v2_experiment()
    print("V1 vs V2 Experiment Complete.")
