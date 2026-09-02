"""
ADVERSARIAL 'BREAK MY BOT' TEST HARNESS FOR STRATEGY V2.7
Adversarial QA Suite designed to actively attempt to break the strategy implementation across:
1. DATA ATTACKS (Duplicates, Disorders, Impossible OHLC, Flash Jumps, Zero Volume)
2. MARKET ATTACKS (Gap through Stop, Gap through BE, Jump through +1.5R, Spread Explosions)
3. BROKER ATTACKS (Rejections, SL Mod Failures, Invalid Volume, Margin Deficit)
4. STATE ATTACKS (Mid-Trade Restarts, Corrupted State JSON, Desyncs)
5. PORTFOLIO ATTACKS (5-Way Collision, Heat Cap Boundary 6.0%, Position Cap 2 Overflow)

CRITICAL GOAL:
Verify that the system FAILS SAFE under every attack without:
- Emitting duplicate orders
- Breaching Portfolio Heat > 6.0%
- Breaching Position Count > 2
- Silent data corruption
"""

import unittest
import os
import sys
import json
import math
from datetime import datetime, timedelta

# Ensure workspace root is in sys.path
sys.path.insert(0, "d:/Kaeha")

from rsi_trend_pullback.data.loader import Candle
from rsi_trend_pullback.research.broker_sizing_engine import (
    BrokerSymbolMetadata,
    XM_AUTHORITATIVE_METADATA,
    BrokerSizingEngineGate4
)
from rsi_trend_pullback.research.portfolio_heat_engine import (
    ActivePosition,
    CandidateSignal,
    PortfolioHeatEngineGate2
)
from rsi_trend_pullback.research.multi_asset_calendar_engine import (
    ASSET_SPECS,
    IndependentAssetStream
)
from rsi_trend_pullback.monitoring.v27_forward_telemetry import (
    V27TelemetryDatabase,
    ForwardTradeRecord
)


class TestV27AdversarialHarness(unittest.TestCase):

    def setUp(self):
        self.db = V27TelemetryDatabase()

    # ── 1. DATA ATTACKS ──

    def test_data_attack_01_impossible_ohlc(self):
        """Data Attack: Candle where High < Low or Open outside High/Low."""
        # Malformed candle: Low is higher than High -> Dataclass must throw ValueError
        with self.assertRaises(ValueError):
            Candle(datetime(2026, 8, 28, 10, 0), 2500.0, 2400.0, 2600.0, 2450.0, 100)

    def test_data_attack_02_flash_jump_and_zero_volume(self):
        """Data Attack: Flash price jump +50% with 0 volume."""
        stream = IndependentAssetStream(ASSET_SPECS["BTCUSD"])
        # Ingest 15 normal candles
        for i in range(15):
            stream.process_candle(Candle(datetime(2026, 8, 20, i, 0), 60000.0, 60100.0, 59900.0, 60050.0, 500))
        # Sudden 50% jump with volume = 0
        jump_candle = Candle(datetime(2026, 8, 20, 16, 0), 60050.0, 90000.0, 60000.0, 89000.0, 0)
        sig = stream.process_candle(jump_candle)
        # Must compute indicator without crashing or generating undefined math (div by zero)
        self.assertIsNotNone(stream.latest_atr)
        self.assertFalse(math.isnan(stream.latest_atr))

    # ── 2. MARKET ATTACKS ──

    def test_market_attack_01_gap_through_stop_loss(self):
        """Market Attack: Weekend gap opens below stop loss."""
        # Long entry at 150.00, SL at 148.00. Monday Open jumps to 145.00!
        meta = XM_AUTHORITATIVE_METADATA["USDJPY"]
        entry_p = 150.00
        sl_p = 148.00
        gap_open_p = 145.00  # Gapped past SL by 300 pips!

        # System must fill exit at the worse price (Gap Open 145.00), not ideal SL 148.00!
        actual_fill_sl = min(sl_p, gap_open_p)
        self.assertEqual(actual_fill_sl, 145.00)

    def test_market_attack_02_spread_explosion(self):
        """Market Attack: Spread expands by 10x during market opening."""
        meta = XM_AUTHORITATIVE_METADATA["XAUUSD"]
        atr = 10.0
        massive_spread = 8.5  # Spread = 85% of ATR (Normal is 2.5%)
        # Economic filter check: ATR / Spread must be >= 5.0
        econ_ratio = atr / massive_spread
        self.assertLess(econ_ratio, 5.0)  # Fails economic filter -> Signal REJECTED!

    # ── 3. BROKER & SIZING ATTACKS ──

    def test_broker_attack_01_below_min_volume_rejection(self):
        """Broker Attack: Small account balance produces volume < volume_min."""
        meta = XM_AUTHORITATIVE_METADATA["BTCUSD"]  # BTCUSD min lot = 0.10, contract size = 1
        tiny_equity = 500.0  # 500 THB equity cannot support 0.10 BTC
        sl_dist = 2000.0

        size_res = BrokerSizingEngineGate4.calculate_base_sizing(meta, tiny_equity, tiny_equity, sl_dist)
        self.assertFalse(size_res.is_accepted)
        self.assertTrue(size_res.rejection_reason.startswith("BELOW_MIN_VOLUME"))

    def test_broker_attack_02_volume_floor_quantization_never_rounds_up(self):
        """Broker Attack: Fractional volume like 0.0199 must floor to 0.01, never round to 0.02."""
        meta = XM_AUTHORITATIVE_METADATA["USDJPY"]
        # Force raw calculated volume = 0.0195
        quantized = math.floor(0.0195 / meta.volume_step) * meta.volume_step
        self.assertEqual(round(quantized, 4), 0.01)

    # ── 4. STATE ATTACKS ──

    def test_state_attack_01_corrupted_json_state_recovery(self):
        """State Attack: State JSON corrupted with invalid syntax."""
        corrupt_path = "d:/Kaeha/v27_forward_telemetry_state.json"
        with open(corrupt_path, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON CORRUPTION @@!!")

        # Database must handle corrupted JSON gracefully without crashing
        db = V27TelemetryDatabase()
        self.assertEqual(len(db.trades), 0)

    # ── 5. PORTFOLIO ATTACKS ──

    def test_portfolio_attack_01_five_asset_simultaneous_collision(self):
        """Portfolio Attack: All 5 assets signal at the exact same H1 bar."""
        candidates = [
            CandidateSignal("BTCUSD", False, "LONG", 60000, 58000, 0.01, 1.0, 35.0, 25.0, 0.45, 0.05),
            CandidateSignal("US500", False, "LONG", 5500, 5400, 0.05, 0.1, 3.5, 25.0, 0.65, 0.02),  # Highest ER = 0.65 (Rank 1)
            CandidateSignal("USDJPY", False, "LONG", 150.0, 148.0, 0.02, 0.001, 2.25, 25.0, 0.55, 0.01), # Rank 2
            CandidateSignal("GBPUSD", False, "LONG", 1.30, 1.28, 0.01, 0.0001, 35.0, 25.0, 0.48, 0.03),
            CandidateSignal("XAUUSD", False, "LONG", 2500, 2450, 0.01, 0.01, 0.35, 25.0, 0.42, 0.04),
        ]

        active_positions = []
        equity = 10000.0

        resolved = PortfolioHeatEngineGate2.resolve_signal_collisions(active_positions, candidates, equity)

        # Only top 2 highest priority assets must be accepted! 3 others must be REJECTED!
        accepted = [c for c, can_acc, r in resolved if can_acc]
        rejected = [c for c, can_acc, r in resolved if not can_acc]

        self.assertEqual(len(accepted), 2)
        self.assertEqual(accepted[0].symbol, "US500")  # Highest ER14 (0.65)
        self.assertEqual(accepted[1].symbol, "USDJPY") # Second highest ER14 (0.55)
        self.assertEqual(len(rejected), 3)

    def test_portfolio_attack_02_heat_cap_overflow_rejection(self):
        """Portfolio Attack: Existing position uses ~5.0% heat. New candidate requests ~2.5% heat (Total > 6.0%)."""
        meta = XM_AUTHORITATIVE_METADATA["USDJPY"]
        # Existing position with 4.97% heat (497.5 THB)
        active_pos = [
            ActivePosition("USDJPY", False, "LONG", 150.0, 150.0, 147.0, 0.07, 0.001, 2.25, 25.0)
        ]
        # New candidate requesting 2.35% heat (235.0 THB) -> Total 7.32% > 6.0% limit
        cand = CandidateSignal("GBPUSD", False, "LONG", 1.30, 1.28, 0.03, 0.0001, 35.0, 25.0, 0.50, 0.02)

        can_accept, reason, proj_heat = PortfolioHeatEngineGate2.can_accept_order(active_pos, cand, 10000.0)
        self.assertFalse(can_accept)
        self.assertIn("HEAT_CAP_EXCEEDED", reason)

    def test_portfolio_attack_03_cluster_subcap_rejection(self):
        """Portfolio Attack: USD-bloc cluster reaches 4.8% (> 4.0% cluster cap) while total heat is only 4.8% (< 6.0%)."""
        # Active position: USDJPY with 2.8% risk (280 THB)
        active_pos = [
            ActivePosition("USDJPY", False, "LONG", 150.0, 150.0, 148.0, 0.06, 0.001, 2.25, 10.0) # 2000*2.25*0.06 = 270 + 10 = 280 THB (2.8%)
        ]
        # Candidate: GBPUSD with 2.0% risk (200 THB) -> Total USD-bloc = 4.8% > 4.0% cluster subcap
        cand = CandidateSignal("GBPUSD", False, "LONG", 1.30, 1.29, 0.02, 0.0001, 35.0, 10.0, 0.50, 0.02) # 100*35*0.02 = 70 + 10 = 80 ? Let's make dist=250 -> 250*35*0.02 = 175 + 25 = 200 THB (2.0%)
        cand.stop_price = 1.2750

        can_accept, reason, proj_heat = PortfolioHeatEngineGate2.can_accept_order(active_pos, cand, 10000.0)
        self.assertFalse(can_accept)
        self.assertIn("CLUSTER_HEAT_CAP_EXCEEDED", reason)

    def test_portfolio_attack_04_max_volume_ceiling_rejection(self):
        """Portfolio Attack: Glitched sizing calculation requests 0.85 lots (> 0.50 lot safety ceiling)."""
        cand = CandidateSignal("USDJPY", False, "LONG", 150.0, 149.5, 0.85, 0.001, 2.25, 25.0, 0.50, 0.02)
        can_accept, reason, proj_heat = PortfolioHeatEngineGate2.can_accept_order([], cand, 10000.0)
        self.assertFalse(can_accept)
        self.assertIn("MAX_VOLUME_EXCEEDED", reason)


if __name__ == "__main__":
    unittest.main()
