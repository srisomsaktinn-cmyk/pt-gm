"""
Execution script to run V2.6 experiment and generate artifact report.
"""

from rsi_trend_pullback.run_v26_volatility_experiment import run_volatility_experiment

if __name__ == "__main__":
    print("Executing V2.6 Volatility Filter Experiment...")
    res = run_volatility_experiment()
    print("Execution complete.")
