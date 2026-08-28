"""
Execution script to run the Controlled Timeframe Experiment (H1 vs M15) and generate artifact.
"""

from rsi_trend_pullback.run_timeframe_experiment import run_timeframe_experiment

if __name__ == "__main__":
    print("Executing Controlled Timeframe Experiment (H1 vs M15)...")
    res = run_timeframe_experiment()
    print("Timeframe Experiment Execution Finished.")
