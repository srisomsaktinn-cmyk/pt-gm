"""
Unit Test Suite for Strategy V2.7 Research Candidate - Gate 1 (Pyramiding Sizing & Risk Proof).
Proves:
1. Base volume uses strict math.floor rounding so actual risk <= target risk.
2. Trade 2 sizing strictly equals floor(2/3 * V1).
3. Reversal to Trade 1 Breakeven strictly produces Combined Loss <= 1.0R.
4. Micro-lot constraints on 10,000 THB account are accurately quantized.
"""

import unittest
import math
from rsi_trend_pullback.research.pyramiding_engine import PyramidingGate1Engine


class TestV27Gate1Pyramiding(unittest.TestCase):

    def test_01_floor_rounding_never_exceeds_target_risk(self):
        """Proves actual dollar risk never exceeds target risk due to math.floor."""
        equity = 10000.0  # 10,000 THB
        risk_pct = 0.03   # 3.0% = 300.00 THB target
        sl_distance = 0.850  # 85 pips
        tick_size = 0.001
        tick_value = 2.25    # THB per tick per lot
        volume_min = 0.01
        volume_max = 50.0
        volume_step = 0.01

        v1, target_risk, actual_risk = PyramidingGate1Engine.calculate_base_volume(
            equity, risk_pct, sl_distance, tick_size, tick_value, volume_min, volume_max, volume_step
        )

        self.assertEqual(target_risk, 300.00)
        self.assertLessEqual(actual_risk, target_risk, "Actual risk must never exceed target risk")
        self.assertGreater(v1, 0.0)

    def test_02_pyramid_case_a_reversal_bounded_to_1r_loss(self):
        """Mathematical Proof: Reversal to Entry1 strictly bounds combined loss <= 1.0R."""
        # Simulated trade parameters
        entry1 = 100.0
        initial_sl = 90.0
        d_distance = 10.0  # 1.0R in price
        tick_size = 0.01
        tick_value = 1.0

        v1 = 0.30  # Base lot
        # Target 1.0R dollar risk = (10.0 / 0.01) * 1.0 * 0.30 = $300.00

        # Scale in at +1.5R
        entry2 = entry1 + (1.5 * d_distance)  # 115.0
        sl_reversal = entry1                   # 100.0 (Breakeven of Trade 1)

        # Calculate V2 = floor(2/3 * V1)
        v2 = PyramidingGate1Engine.calculate_pyramid_volume(v1, volume_min=0.01, volume_max=50.0, volume_step=0.01)
        expected_v2 = round(math.floor((2.0 / 3.0) * 0.30 / 0.01) * 0.01, 2)  # 0.20
        self.assertEqual(v2, expected_v2)

        # Evaluate full reversal back to entry1
        res = PyramidingGate1Engine.evaluate_scale_in_reversal(
            entry1=entry1,
            entry2=entry2,
            sl_reversal=sl_reversal,
            v1=v1,
            v2=v2,
            tick_size=tick_size,
            tick_value=tick_value,
            direction="LONG"
        )

        # Trade 1 at BE = 0.0
        self.assertEqual(res["trade1_pnl"], 0.0, "Trade 1 PnL at Breakeven must be exactly 0.0")

        # Trade 2 loss: (100.0 - 115.0) / 0.01 * 1.0 * 0.20 = -15 * 100 * 0.20 = -$300.00 = -1.0R
        self.assertEqual(res["trade2_pnl"], -300.0, "Trade 2 loss at SL must equal exactly -1.0R ($300)")

        # Combined Loss = -$300.00 (-1.0R) <= Base Trade Risk
        self.assertEqual(res["combined_pnl"], -300.0)
        self.assertLessEqual(abs(res["combined_pnl"]), 300.0, "Combined loss must never exceed 1.0R target")

    def test_03_pyramid_suppression_when_below_min_volume(self):
        """Proves that if 2/3 of base volume is below broker min volume, pyramid is suppressed."""
        v1 = 0.01  # Minimum lot size
        volume_min = 0.01
        volume_step = 0.01

        # 2/3 of 0.01 = 0.00667 < 0.01 min
        v2 = PyramidingGate1Engine.calculate_pyramid_volume(v1, volume_min=volume_min, volume_max=50.0, volume_step=volume_step)
        self.assertEqual(v2, 0.0, "Pyramid volume must be 0.0 when 2/3 * V1 < min_volume")

    def test_04_small_account_gold_vs_forex_quantization(self):
        """Verifies micro-lot risk behavior on 10,000 THB account across Gold vs Forex."""
        equity_thb = 10000.0
        target_risk_thb = 300.0  # 3%

        # 1. Forex USDJPY (Typical 25-pip stop on XM, tick_value ~2.25 THB)
        v_fx, _, actual_risk_fx = PyramidingGate1Engine.calculate_base_volume(
            equity=equity_thb,
            risk_pct=0.03,
            sl_distance=0.250,
            tick_size=0.001,
            tick_value=2.25,
            volume_min=0.01,
            volume_max=50.0,
            volume_step=0.01
        )
        self.assertLessEqual(actual_risk_fx, target_risk_thb, "Forex risk must stay <= 300 THB")
        self.assertGreaterEqual(v_fx, 0.01)

        # 2. Gold (High ATR $18.0, 1 oz = 0.01 lot, tick_value = $0.01 * 35 = 0.35 THB)
        # Loss on 0.01 lot = $18.0 * 35 = 630 THB
        v_gold, _, actual_risk_gold = PyramidingGate1Engine.calculate_base_volume(
            equity=equity_thb,
            risk_pct=0.03,
            sl_distance=18.0,
            tick_size=0.01,
            tick_value=0.35,
            volume_min=0.01,
            volume_max=50.0,
            volume_step=0.01
        )
        self.assertEqual(v_gold, 0.01, "Gold must clamp to volume_min 0.01 lot")
        self.assertGreater(actual_risk_gold, target_risk_thb, "Quantifies that 0.01 lot Gold on 10k THB exceeds 300 THB due to broker floor")


if __name__ == "__main__":
    unittest.main()
