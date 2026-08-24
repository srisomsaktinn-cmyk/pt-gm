"""
Execution script to generate Paper Trading shadow audit logs and report.
"""

from rsi_trend_pullback.run_paper_trading_simulator import run_paper_trading_simulation

if __name__ == "__main__":
    print("Executing Paper Trading Simulation & Shadow Audit...")
    res = run_paper_trading_simulation(max_trades=50)
    print("Execution complete.")
