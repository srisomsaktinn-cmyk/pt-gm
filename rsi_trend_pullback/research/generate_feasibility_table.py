"""
Feasibility Generator across 4 Account Sizes on XM Ultra Low.
"""

from rsi_trend_pullback.research.broker_sizing_engine import (
    BrokerSizingEngineGate4,
    XM_AUTHORITATIVE_METADATA
)

TYPICAL_SL_PRICES = {
    "XAUUSD": 18.0,      # $18.00/oz
    "USDJPY": 0.350,     # 35 pips
    "GBPUSD": 0.00350,   # 35 pips
    "US500":  35.0,      # 35 index points
    "BTCUSD": 1500.0     # $1,500
}

def generate_table():
    account_sizes = [5000.0, 10000.0, 20000.0, 50000.0]
    
    print("=" * 105)
    print("SMALL ACCOUNT FEASIBILITY TABLE (TARGET RISK = 3.0% OF EQUITY / STRICT FLOOR ROUNDING)")
    print("=" * 105)
    
    for eq in account_sizes:
        print(f"\n--- [ ACCOUNT EQUITY: {eq:,.0f} THB (TARGET RISK 3.0% = {eq*0.03:,.0f} THB) ] ---")
        print(f"{'Symbol':<8} | {'Raw Volume':<12} | {'Rounded Vol':<12} | {'Actual Risk (THB)':<18} | {'Risk %':<8} | {'Rounding Diff':<14} | {'Status':<16}")
        print("-" * 105)
        for sym, sl in TYPICAL_SL_PRICES.items():
            meta = XM_AUTHORITATIVE_METADATA[sym]
            res = BrokerSizingEngineGate4.calculate_base_sizing(
                meta=meta,
                equity_thb=eq,
                free_margin_thb=eq,
                sl_distance_price=sl
            )
            status = "🟢 ACCEPTED" if res.is_accepted else "❌ REJECTED"
            print(f"{sym:<8} | {res.raw_volume:<12.4f} | {res.quantized_volume:<12.2f} | {res.actual_risk_thb:<18,.2f} | {res.actual_risk_pct:<7.2f}% | -{res.rounding_error_thb:<13.2f} | {status:<16}")

if __name__ == "__main__":
    generate_table()
