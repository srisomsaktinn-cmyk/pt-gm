"""
Execution script to run Multi-Asset Portfolio Experiment.
"""

from rsi_trend_pullback.run_multi_asset_experiment import run_full_multi_asset_portfolio

if __name__ == "__main__":
    print("Executing Multi-Asset Portfolio Experiment (6 Assets: 2020-2025)...")
    res, port, trades = run_full_multi_asset_portfolio()
    print("=" * 80)
    print("INDIVIDUAL ASSET BREAKDOWN (Strategy V2.6 on H1 2020-2025)")
    print("=" * 80)
    print(f"{'Symbol':<10} | {'Trades':<8} | {'Tr/Mo':<6} | {'WinRate':<8} | {'PF (ECN)':<8} | {'Net P&L ($)':<12} | {'Max DD':<8}")
    print("-" * 80)
    for sym, r in res.items():
        print(f"{sym:<10} | {r['total_trades']:<8} | {r['trades_per_month']:<6} | {r['win_rate']:<7.1f}% | {r['profit_factor']:<8.2f} | ${r['net_pnl']:<+11,.2f} | -{r['max_drawdown_pct']:.2f}%")
    print("=" * 80)
    print("COMBINED MULTI-ASSET PORTFOLIO RESULTS")
    print("=" * 80)
    print(f"  * Total Portfolio Trades : {port['total_trades']} trades ({port['trades_per_year']} trades/year)")
    print(f"  * Trading Frequency      : {port['trades_per_month']} trades/month (~{port['trades_per_week']} trades/week)")
    print(f"  * Portfolio Win Rate     : {port['win_rate']:.2f}%")
    print(f"  * Portfolio Profit Factor: {port['profit_factor']:.2f}")
    print(f"  * Combined Net P&L (ECN) : ${port['net_pnl']:+,.2f}")
    print(f"  * Portfolio Max Drawdown : -{port['max_drawdown_pct']:.2f}%")
    print("=" * 80)
