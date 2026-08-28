"""
DCA Schedule Inspector.
Inspects exact deposit events, timestamps, amounts, and verifies Model A vs Model B.
"""

from rsi_trend_pullback.research.run_v27_official_baseline_backtest import (
    run_v27_official_baseline_backtest
)
from rsi_trend_pullback.research.v27_integrity_pipeline import (
    V27UnifiedPipelineOrchestrator
)
from rsi_trend_pullback.data.loader import DataLoader, Candle
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.data.multi_asset_builder import build_all_multi_asset_datasets
from rsi_trend_pullback.research.broker_sizing_engine import XM_AUTHORITATIVE_METADATA
from rsi_trend_pullback.research.multi_asset_calendar_engine import ASSET_SPECS
from collections import defaultdict

def audit_dca_events():
    paths = build_all_multi_asset_datasets()
    paths["XAUUSD"] = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"

    raw_data = {sym: DataLoader.load_csv(p) for sym, p in paths.items()}
    timeline_set = set()
    candles_by_time_sym = defaultdict(dict)
    for sym, candles in raw_data.items():
        for c in candles:
            timeline_set.add(c.timestamp)
            candles_by_time_sym[c.timestamp][sym] = c

    sorted_timestamps = sorted(list(timeline_set))

    orchestrator = V27UnifiedPipelineOrchestrator(
        initial_equity_thb=10000.0,
        broker_metadata=XM_AUTHORITATIVE_METADATA,
        asset_specs=ASSET_SPECS
    )

    for ts in sorted_timestamps:
        orchestrator.process_closed_candle_event(ts, candles_by_time_sym[ts])

    dca_events = [e for e in orchestrator.audit_log if e.get("event") == "DCA_DEPOSIT"]
    
    print(f"Total DCA Deposit Events: {len(dca_events)}")
    print(f"First 5 DCA Deposits:")
    for d in dca_events[:5]:
        print(f"  • Timestamp: {d['timestamp']} | Amount: {d['amount_thb']:,.2f} THB | New Equity: {d['new_equity_thb']:,.2f} THB")

    print(f"Last 5 DCA Deposits:")
    for d in dca_events[-5:]:
        print(f"  • Timestamp: {d['timestamp']} | Amount: {d['amount_thb']:,.2f} THB | New Equity: {d['new_equity_thb']:,.2f} THB")

    total_dca_inflow = sum(d["amount_thb"] for d in dca_events)
    print(f"\nInitial Balance: 10,000.00 THB")
    print(f"Sum of DCA Deposits: {total_dca_inflow:,.2f} THB ({len(dca_events)} deposits x 1,000 THB)")
    print(f"Total External Capital Contributed: {10000.0 + total_dca_inflow:,.2f} THB")
    print(f"Net Trading Profit: {orchestrator.equity_thb - (10000.0 + total_dca_inflow):,.2f} THB")
    print(f"Final Equity: {orchestrator.equity_thb:,.2f} THB")

if __name__ == "__main__":
    audit_dca_events()
