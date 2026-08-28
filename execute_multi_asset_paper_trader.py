"""
Runner script for Multi-Asset MT5 Paper Trading Bot.
"""

from rsi_trend_pullback.mt5_multi_asset_paper_trader import MT5MultiAssetPaperTrader

if __name__ == "__main__":
    runner = MT5MultiAssetPaperTrader()
    if runner.initialize_mt5():
        if runner.warm_up_all_assets(num_bars=150):
            runner.run_live_loop()
    else:
        print("[EXIT] Could not connect to MetaTrader 5.")
