"""
CLI Runner for Strategy V2.7 Research & Forward Analytics Center.
"""

import sys
import os

sys.path.insert(0, "d:/Kaeha")

from rsi_trend_pullback.analytics.v27_analytics_engine import V27AnalyticsCenter

if __name__ == "__main__":
    center = V27AnalyticsCenter()
    summary = center.generate_master_reports()

    base = summary["historical_baseline"]
    pyr = summary["pyramid_forensics"]
    drought = summary["trade_drought"]

    print("=" * 95)
    print("  STRATEGY V2.7: RESEARCH & FORWARD ANALYTICS CENTER (OBSERVABILITY ONLY)")
    print("=" * 95)

    print("\n--- 1. BENCHMARK PERFORMANCE (2020-2025: 6 YEARS) ---")
    print(f"  • Total Trades:              {base['total_trades']} trades")
    print(f"  • Win Rate:                  {base['win_rate_pct']:.1f}% (95% CI: {base['win_rate_ci_95'][0]}% - {base['win_rate_ci_95'][1]}%)")
    print(f"  • Profit Factor:             {base['profit_factor']:.2f}")
    print(f"  • Payoff Ratio:              {base['payoff_ratio']:.2f}x")
    print(f"  • Expectancy per Trade:      {base['expectancy_thb']:+,.2f} THB (95% CI: {base['expectancy_ci_95'][0]} to {base['expectancy_ci_95'][1]} THB)")
    print(f"  • Net Trading Profit:        {base['net_pnl_thb']:+,.2f} THB")
    print(f"  • True Unit-NAV Max DD:      -{base['max_drawdown_pct']:.2f}% [Personal Limit: 25.0%]")

    print("\n--- 2. PYRAMIDING (+1.5R) SCALE-IN FORENSICS ---")
    print(f"  • Scale-In Activations:      {pyr['total_pyramid_events']} times")
    print(f"  • Macro Runner Conversion:   {pyr['successful_runners']} trades ({pyr['runner_conversion_rate_pct']:.1f}%)")
    print(f"  • Breakeven Reversals:       {pyr['be_reversals']} trades ({100 - pyr['runner_conversion_rate_pct']:.1f}%)")
    print(f"  • Pyramiding Contribution:   {pyr['pyramid_pnl_thb']:+,.2f} THB ({pyr['pyramid_share_pct']:.1f}% of total profit)")

    print("\n--- 3. MULTI-ASSET ATTRIBUTION ---")
    print(f"  {'Symbol':<10} | {'Trades':<8} | {'Win Rate':<10} | {'PF':<6} | {'Expectancy':<14} | {'Net P&L (THB)':<18}")
    print("  " + "-" * 80)
    for sym, s in summary["asset_analysis"].items():
        print(f"  {sym:<10} | {s['trades']:<8} | {s['win_rate_pct']:<9.1f}% | {s['profit_factor']:<6.2f} | {s['expectancy_thb']:<+14,.2f} | {s['net_pnl_thb']:<+18,.2f}")

    print("\n--- 4. TRADE DROUGHT & INTER-SIGNAL FREQUENCY ---")
    print(f"  • Average Gap Between Trades: {drought['avg_days_between_trades']:.1f} days")
    print(f"  • Median Gap Between Trades:  {drought['median_days_between_trades']:.1f} days")
    print(f"  • Maximum Gap (Trade Drought):{drought['max_gap_days']:.1f} days")

    print("\n" + "=" * 95)
    print("  Reports Created: v27_daily_analytics.md | v27_asset_analysis.md | v27_pyramid_analysis.md")
    print("  Interactive HTML Dashboard: d:/Kaeha/v27_analytics_dashboard.html")
    print("=" * 95)
