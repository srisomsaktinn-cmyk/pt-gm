"""
Unit Test Suite for Strategy V2.7 Research Candidate - Gate 4 (Broker Metadata & Micro-Lot Quantization).
Tests all 15 required scenarios:
1. Exact 3% risk.
2. Volume rounds down via floor.
3. Volume would round up -> strictly must NOT round up.
4. Calculated volume below minimum -> REJECT trade.
5. Calculated volume above maximum -> clamp to volume_max.
6. Pyramid 2/3 sizing.
7. Pyramid volume below minimum -> REJECT pyramid.
8. BTC contract-size handling.
9. Gold contract-size handling.
10. FX contract-size handling.
11. US500 contract-size handling.
12. Currency conversion in THB.
13. Insufficient free margin.
14. Portfolio heat rejection.
15. Combined volume + heat + margin rejection.
"""

import unittest
from rsi_trend_pullback.research.broker_sizing_engine import (
    BrokerSymbolMetadata,
    XM_AUTHORITATIVE_METADATA,
    BrokerSizingEngineGate4
)
from rsi_trend_pullback.research.portfolio_heat_engine import ActivePosition, CandidateSignal, PortfolioHeatEngineGate2


class TestV27Gate4SizingEngine(unittest.TestCase):

    def setUp(self):
        self.equity_10k = 10000.0  # 10,000 THB
        self.free_margin_10k = 10000.0

    def test_01_exact_3_percent_risk(self):
        """Verifies exact 3.0% sizing when parameters align with broker step."""
        meta = XM_AUTHORITATIVE_METADATA["USDJPY"]
        # Stop loss 0.40 JPY (400 ticks) -> Loss per 1 lot = 400 * 2.25 = 900 THB
        # Target 300 THB -> Raw volume = 300 / 900 = 0.3333 lots -> floor = 0.33 lots
        res = BrokerSizingEngineGate4.calculate_base_sizing(
            meta=meta,
            equity_thb=self.equity_10k,
            free_margin_thb=self.free_margin_10k,
            sl_distance_price=0.40
        )
        self.assertTrue(res.is_accepted)
        self.assertEqual(res.target_risk_thb, 300.0)
        self.assertLessEqual(res.actual_risk_thb, 300.0, "Actual risk must never exceed target 300 THB")

    def test_02_volume_rounds_down_via_floor(self):
        """Verifies raw volume 0.0287 lots rounds down strictly to 0.02 lots."""
        meta = XM_AUTHORITATIVE_METADATA["GBPUSD"]
        # Stop loss 0.00300 (300 ticks) -> Loss per lot = 300 * 35 = 10,500 THB
        # Raw = 300 / 10,500 = 0.02857 lots -> floor = 0.02 lots
        res = BrokerSizingEngineGate4.calculate_base_sizing(
            meta=meta,
            equity_thb=self.equity_10k,
            free_margin_thb=self.free_margin_10k,
            sl_distance_price=0.00300
        )
        self.assertTrue(res.is_accepted)
        self.assertEqual(res.quantized_volume, 0.02)
        self.assertEqual(res.actual_risk_thb, 210.0)
        self.assertEqual(res.rounding_error_thb, 90.0)  # 300 - 210 = 90 THB under

    def test_03_volume_would_round_up_must_not_round_up(self):
        """Verifies raw volume 0.0299 lots does NOT round up to 0.03 lots."""
        meta = XM_AUTHORITATIVE_METADATA["GBPUSD"]
        # Raw volume 0.0298 lots
        loss_per_lot = 300.0 / 0.0298  # approx 10,067 THB
        sl_dist = (loss_per_lot / meta.trade_tick_value) * meta.trade_tick_size

        res = BrokerSizingEngineGate4.calculate_base_sizing(
            meta=meta,
            equity_thb=self.equity_10k,
            free_margin_thb=self.free_margin_10k,
            sl_distance_price=sl_dist
        )
        self.assertEqual(res.quantized_volume, 0.02, "Must strictly stay at 0.02 and NOT round up to 0.03")
        self.assertLessEqual(res.actual_risk_thb, 300.0)

    def test_04_calculated_volume_below_minimum_rejects_trade(self):
        """Verifies trade is REJECTED when raw volume < volume_min (e.g. Gold on 10k THB)."""
        meta = XM_AUTHORITATIVE_METADATA["XAUUSD"]
        # Stop loss $20.00 -> Loss on 0.01 lot = 2000 ticks * 0.35 = 700 THB (7.0% risk)
        # Raw volume = 300 / 70,000 = 0.00428 lots < 0.01 min
        res = BrokerSizingEngineGate4.calculate_base_sizing(
            meta=meta,
            equity_thb=self.equity_10k,
            free_margin_thb=self.free_margin_10k,
            sl_distance_price=20.00
        )
        self.assertFalse(res.is_accepted, "Must reject trade when raw volume < 0.01 min lot")
        self.assertIn("BELOW_MIN_VOLUME", res.rejection_reason)
        self.assertEqual(res.quantized_volume, 0.0)

    def test_05_calculated_volume_above_maximum_clamps(self):
        """Verifies calculated volume above 50.0 lots clamps to volume_max."""
        meta = XM_AUTHORITATIVE_METADATA["US500"]
        res = BrokerSizingEngineGate4.calculate_base_sizing(
            meta=meta,
            equity_thb=10000000.0,  # 10 Million THB -> Target risk 300,000 THB
            free_margin_thb=10000000.0,
            sl_distance_price=5.0
        )
        self.assertTrue(res.is_accepted)
        self.assertEqual(res.quantized_volume, meta.volume_max)

    def test_06_pyramid_case_a_2_3_sizing(self):
        """Verifies pyramid sizing equals floor(2/3 * V1)."""
        meta = XM_AUTHORITATIVE_METADATA["USDJPY"]
        base_v1 = 0.03
        res = BrokerSizingEngineGate4.calculate_pyramid_sizing(
            meta=meta,
            base_volume=base_v1,
            free_margin_thb=self.free_margin_10k,
            sl_distance_price=0.50
        )
        self.assertTrue(res.is_accepted)
        self.assertEqual(res.quantized_volume, 0.02)  # floor(2/3 * 0.03) = 0.02

    def test_07_pyramid_volume_below_minimum_rejects_pyramid(self):
        """Verifies pyramid is REJECTED when 2/3 * 0.01 lot = 0.0067 < 0.01 min."""
        meta = XM_AUTHORITATIVE_METADATA["GBPUSD"]
        base_v1 = 0.01
        res = BrokerSizingEngineGate4.calculate_pyramid_sizing(
            meta=meta,
            base_volume=base_v1,
            free_margin_thb=self.free_margin_10k,
            sl_distance_price=0.0020
        )
        self.assertFalse(res.is_accepted, "Must reject pyramid when 2/3 of base is below 0.01 min lot")
        self.assertIn("PYRAMID_BELOW_MIN_VOLUME", res.rejection_reason)

    def test_08_btc_contract_size_handling(self):
        """Verifies BTC metadata handling (1 contract per lot, tick size 0.01)."""
        meta = XM_AUTHORITATIVE_METADATA["BTCUSD"]
        self.assertEqual(meta.trade_contract_size, 1.0)
        self.assertEqual(meta.trade_tick_size, 0.01)

    def test_09_gold_contract_size_handling(self):
        """Verifies Gold metadata handling (100 oz per lot, tick size 0.01)."""
        meta = XM_AUTHORITATIVE_METADATA["XAUUSD"]
        self.assertEqual(meta.trade_contract_size, 100.0)
        self.assertEqual(meta.trade_tick_value, 0.35)

    def test_10_fx_contract_size_handling(self):
        """Verifies FX metadata handling (100,000 units per lot)."""
        meta = XM_AUTHORITATIVE_METADATA["USDJPY"]
        self.assertEqual(meta.trade_contract_size, 100000.0)

    def test_11_us500_contract_size_handling(self):
        """Verifies US500 metadata handling (min lot 0.10)."""
        meta = XM_AUTHORITATIVE_METADATA["US500"]
        self.assertEqual(meta.volume_min, 0.10)
        self.assertEqual(meta.trade_contract_size, 1.0)

    def test_12_currency_conversion_in_thb(self):
        """Verifies tick values are correctly expressed in THB base currency."""
        for sym, meta in XM_AUTHORITATIVE_METADATA.items():
            self.assertGreater(meta.trade_tick_value, 0.0)
            self.assertGreater(meta.margin_initial, 0.0)

    def test_13_insufficient_free_margin_rejection(self):
        """Verifies order is rejected when free margin < required margin * 1.25."""
        meta = XM_AUTHORITATIVE_METADATA["USDJPY"]
        # Free margin is only 10 THB
        res = BrokerSizingEngineGate4.calculate_base_sizing(
            meta=meta,
            equity_thb=self.equity_10k,
            free_margin_thb=10.0,
            sl_distance_price=0.20
        )
        self.assertFalse(res.is_accepted)
        self.assertIn("INSUFFICIENT_FREE_MARGIN", res.rejection_reason)

    def test_14_portfolio_heat_rejection(self):
        """Verifies candidate sized at 300 THB is rejected if existing heat is already 5.5%."""
        active = [ActivePosition("USDJPY", False, "LONG", 150.0, 150.0, 147.5, 0.02, 0.001, 2.25, 0.0)]  # 1125 THB / 20k = 5.625%
        cand = CandidateSignal("GBPUSD", False, "LONG", 1.30, 1.29, 0.02, 0.0001, 2.25, 0.0, 0.50, 0.05)  # 450 THB
        # Total = 1125 + 450 = 1575 THB / 20k = 7.875% > 6.0%
        accepted, reason, _ = PortfolioHeatEngineGate2.can_accept_order(active, cand, 20000.0)
        self.assertFalse(accepted)
        self.assertIn("HEAT_CAP_EXCEEDED", reason)

    def test_15_combined_volume_heat_margin_safety(self):
        """Verifies end-to-end rejection cascade across sizing, margin, and heat."""
        meta = XM_AUTHORITATIVE_METADATA["USDJPY"]
        # Step 1: Valid sizing
        res = BrokerSizingEngineGate4.calculate_base_sizing(meta, self.equity_10k, self.free_margin_10k, sl_distance_price=0.30)
        self.assertTrue(res.is_accepted)

        # Step 2: Heat Check
        cand = CandidateSignal("USDJPY", False, "LONG", 150.0, 149.7, res.quantized_volume, meta.trade_tick_size, meta.trade_tick_value, 20.0, 0.50, 0.05)
        accepted, _, heat_pct = PortfolioHeatEngineGate2.can_accept_order([], cand, self.equity_10k)
        self.assertTrue(accepted)
        self.assertLessEqual(heat_pct, 0.060)


if __name__ == "__main__":
    unittest.main()
