"""
Execution script to run the V2 ATR experiment and generate complete artifact.
"""

from rsi_trend_pullback.run_v2_atr_experiment import run_atr_stop_experiment

if __name__ == "__main__":
    print("Running V2 ATR Stop Loss Experiment...")
    res = run_atr_stop_experiment()
    print("V2 ATR Experiment Complete.")
