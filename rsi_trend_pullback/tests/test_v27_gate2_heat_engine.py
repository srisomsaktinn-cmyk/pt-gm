"""
Unit Test Suite for Strategy V2.7 Research Candidate - Gate 2 (Portfolio Heat Engine & Signal Collision).
Verifies:
1. Dynamic Portfolio Heat equation with friction buffer.
2. Heat cap boundary conditions (<= 6.0% accepted, > 6.0% rejected).
3. Position count cap strictly separates from heat cap (Max 2 positions).
4. Deterministic Signal Collision resolution (ER14 sort + canonical rank tiebreaker).
"""

import unittest
from rsi_trend_pullback.research.portfolio_heat_engine import (
    ActivePosition,
    CandidateSignal,
    PortfolioHeatEngineGate2
)


class TestV27Gate2HeatEngine(unittest.TestCase):

    def setUp(self):
        self.equity = 10000.0  # 10,000 THB

    def test_01_zero_risk_be_position_preserves_friction_buffer(self):
        """Proves position at BE has zero price loss but preserves explicit friction buffer."""
        pos = ActivePosition(
            symbol="XAUUSD",
            is_pyramid=False,
            direction="LONG",
            entry_price=2500.0,
            current_price=2530.0,
            current_stop_price=2500.0,  # At Breakeven
            volume=0.01,
            tick_size=0.01,
            tick_value=0.35,  # 0.35 THB per tick (approx $0.01 * 35 THB)
            friction_buffer_cur=30.0  # 30 THB friction buffer
        )

        loss = pos.calculate_potential_loss()
        self.assertEqual(loss, 30.0, "Price loss must be 0, total loss equals friction buffer 30 THB")

        total_loss, heat_pct = PortfolioHeatEngineGate2.calculate_current_heat([pos], self.equity)
        self.assertEqual(total_loss, 30.0)
        self.assertEqual(heat_pct, 0.0030)  # 0.3% heat

    def test_02_single_base_position_heat(self):
        """Verifies heat calculation for single open base position (3.0% target)."""
        pos = ActivePosition(
            symbol="USDJPY",
            is_pyramid=False,
            direction="LONG",
            entry_price=155.00,
            current_price=155.00,
            current_stop_price=154.20,  # 80 pips SL
            volume=0.01,
            tick_size=0.001,
            tick_value=2.25,
            friction_buffer_cur=15.0
        )
        # Price loss = (0.80 / 0.001) * 2.25 * 0.01 = 180 THB + 15 THB buffer = 195 THB
        loss = pos.calculate_potential_loss()
        self.assertEqual(loss, 195.0)

        total_loss, heat_pct = PortfolioHeatEngineGate2.calculate_current_heat([pos], self.equity)
        self.assertEqual(total_loss, 195.0)
        self.assertEqual(heat_pct, 0.0195)  # 1.95% heat

    def test_03_base_plus_pyramid_heat(self):
        """Verifies heat calculation when Base is at BE and Pyramid is active."""
        base_pos = ActivePosition(
            symbol="US500",
            is_pyramid=False,
            direction="LONG",
            entry_price=5500.0,
            current_price=5550.0,
            current_stop_price=5500.0,  # Moved to BE
            volume=0.20,
            tick_size=0.01,
            tick_value=0.35,
            friction_buffer_cur=20.0
        )
        pyramid_pos = ActivePosition(
            symbol="US500",
            is_pyramid=True,
            direction="LONG",
            entry_price=5550.0,
            current_price=5550.0,
            current_stop_price=5500.0,  # Stop at 5500 (distance = 50 pts)
            volume=0.13,  # ~2/3 of 0.20
            tick_size=0.01,
            tick_value=0.35,
            friction_buffer_cur=20.0
        )
        # Pyramid loss = (50.0 / 0.01) * 0.35 * 0.13 = 227.50 THB + 20 THB = 247.50 THB
        # Total loss = 20.0 (base buffer) + 247.50 (pyramid) = 267.50 THB
        total_loss, heat_pct = PortfolioHeatEngineGate2.calculate_current_heat([base_pos, pyramid_pos], self.equity)
        self.assertEqual(total_loss, 267.50)
        self.assertEqual(heat_pct, 0.02675)  # 2.675% heat <= 6.0%

    def test_04_heat_boundary_exactly_6_percent_accepted(self):
        """Verifies candidate that brings total heat to exactly 6.0% is accepted."""
        active_pos = [ActivePosition(
            symbol="USDJPY",
            is_pyramid=False,
            direction="LONG",
            entry_price=150.0,
            current_price=150.0,
            current_stop_price=149.0,
            volume=0.01,
            tick_size=0.001,
            tick_value=3.00,
            friction_buffer_cur=0.0  # Loss = 300 THB
        )]
        candidate = CandidateSignal(
            symbol="GBPUSD",
            is_pyramid=False,
            direction="SHORT",
            entry_price=1.3000,
            stop_price=1.3100,
            volume=0.01,
            tick_size=0.0001,
            tick_value=3.00,
            friction_buffer_cur=0.0,  # Loss = 300 THB
            er_14=0.45,
            asset_rank=5
        )
        # Projected total loss = 300 + 300 = 600 THB = 6.0%
        accepted, reason, proj_heat = PortfolioHeatEngineGate2.can_accept_order(active_pos, candidate, self.equity)
        self.assertTrue(accepted)
        self.assertEqual(proj_heat, 0.0600)

    def test_05_heat_boundary_above_6_percent_rejected(self):
        """Verifies candidate that brings total heat to 6.1% is rejected."""
        active_pos = [ActivePosition(
            symbol="USDJPY",
            is_pyramid=False,
            direction="LONG",
            entry_price=150.0,
            current_price=150.0,
            current_stop_price=149.0,
            volume=0.01,
            tick_size=0.001,
            tick_value=3.00,
            friction_buffer_cur=0.0  # 300 THB
        )]
        candidate = CandidateSignal(
            symbol="GBPUSD",
            is_pyramid=False,
            direction="SHORT",
            entry_price=1.3000,
            stop_price=1.3105,  # 315 THB risk
            volume=0.01,
            tick_size=0.0001,
            tick_value=3.00,
            friction_buffer_cur=0.0,
            er_14=0.45,
            asset_rank=5
        )
        # Projected total loss = 300 + 315 = 615 THB = 6.15% > 6.0%
        accepted, reason, proj_heat = PortfolioHeatEngineGate2.can_accept_order(active_pos, candidate, self.equity)
        self.assertFalse(accepted)
        self.assertIn("HEAT_CAP_EXCEEDED", reason)

    def test_06_position_cap_rejection_independent_of_low_heat(self):
        """Proves 3rd position is rejected even if total heat is very low (e.g. 2.0%)."""
        active_pos = [
            ActivePosition("USDJPY", False, "LONG", 150.0, 151.0, 150.0, 0.01, 0.001, 2.0, 10.0),  # 10 THB
            ActivePosition("GBPUSD", False, "LONG", 1.30, 1.31, 1.30, 0.01, 0.0001, 2.0, 10.0)   # 10 THB
        ]
        # Current heat is only (10 + 10) / 10,000 = 0.2%
        candidate = CandidateSignal("XAUUSD", False, "LONG", 2500.0, 2480.0, 0.01, 0.01, 0.35, 15.0, 0.50, 4)

        accepted, reason, proj_heat = PortfolioHeatEngineGate2.can_accept_order(active_pos, candidate, self.equity)
        self.assertFalse(accepted, "Must reject 3rd position due to Position Count Cap = 2")
        self.assertIn("POSITION_CAP_EXCEEDED", reason)

    def test_07_deterministic_signal_collision_sort(self):
        """Proves 3 simultaneous signals are prioritized deterministically by highest ER14."""
        active_pos = []

        cand_xau = CandidateSignal("XAUUSD", False, "LONG", 2500.0, 2480.0, 0.01, 0.01, 0.35, 10.0, er_14=0.42, asset_rank=4)
        cand_jpy = CandidateSignal("USDJPY", False, "LONG", 150.0, 149.0, 0.01, 0.001, 2.25, 10.0, er_14=0.58, asset_rank=2)
        cand_spx = CandidateSignal("US500", False, "LONG", 5500.0, 5450.0, 0.20, 0.01, 0.35, 10.0, er_14=0.51, asset_rank=1)

        results = PortfolioHeatEngineGate2.resolve_signal_collisions(
            active_positions=active_pos,
            candidates=[cand_xau, cand_jpy, cand_spx],
            equity=self.equity
        )

        # Expected priority: USDJPY (ER 0.58) -> US500 (ER 0.51) -> XAUUSD (ER 0.42, Rejected by Position Cap)
        self.assertEqual(results[0][0].symbol, "USDJPY")
        self.assertTrue(results[0][1], "USDJPY (Highest ER 0.58) must be Accepted")

        self.assertEqual(results[1][0].symbol, "US500")
        self.assertTrue(results[1][1], "US500 (2nd Highest ER 0.51) must be Accepted")

        self.assertEqual(results[2][0].symbol, "XAUUSD")
        self.assertFalse(results[2][1], "XAUUSD (3rd signal) must be Rejected due to Max 2 Positions")
        self.assertIn("POSITION_CAP_EXCEEDED", results[2][2])

    def test_08_er_tiebreak_using_canonical_rank(self):
        """Proves when ER14 is identical, canonical asset rank breaks the tie deterministically."""
        active_pos = [
            ActivePosition("BTCUSD", False, "LONG", 60000.0, 61000.0, 60000.0, 0.01, 0.01, 0.35, 10.0)  # Slot 1 used
        ]
        # Two signals with identical ER = 0.4500
        cand_spx = CandidateSignal("US500", False, "LONG", 5500.0, 5450.0, 0.20, 0.01, 0.35, 10.0, er_14=0.45, asset_rank=1)
        cand_gbp = CandidateSignal("GBPUSD", False, "SHORT", 1.30, 1.31, 0.01, 0.0001, 2.25, 10.0, er_14=0.45, asset_rank=5)

        results = PortfolioHeatEngineGate2.resolve_signal_collisions(
            active_positions=active_pos,
            candidates=[cand_gbp, cand_spx],
            equity=self.equity
        )

        # US500 has Rank 1 < GBPUSD Rank 5 -> US500 takes the 2nd slot, GBPUSD is rejected
        self.assertEqual(results[0][0].symbol, "US500")
        self.assertTrue(results[0][1], "US500 must win tiebreaker over GBPUSD")

        self.assertEqual(results[1][0].symbol, "GBPUSD")
        self.assertFalse(results[1][1], "GBPUSD must be rejected due to position cap")


if __name__ == "__main__":
    unittest.main()
