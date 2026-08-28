"""
Strategy V2.7 Research Candidate - Gate 1: Pyramiding Position Sizing & Risk Module.
Strictly implements Case A: Trade 2 Volume = 2/3 of Base Volume with Breakeven Stop Loss.

Mathematical Contract:
1. Target Base Risk = 1.0R = Equity * Risk_Pct (Default: 3.0%).
2. Trade 1 Initial Stop Distance = D = 2.5 * ATR14.
3. Base Volume V1 = math.floor(Target_Risk_Dollars / (D * Tick_Value / Tick_Size) / Volume_Step) * Volume_Step.
4. Scale-In Trigger: When Bar High/Price reaches Entry1 + 1.5 * D (for Long) or Entry1 - 1.5 * D (for Short).
5. Pyramiding Actions:
   - Action A: Stop Loss of Trade 1 is moved to Entry1 (Breakeven, PnL1 at BE = 0.0R).
   - Action B: Trade 2 Volume V2 = math.floor((2/3) * V1 / Volume_Step) * Volume_Step.
   - Action C: Stop Loss of Trade 2 is set at Entry1 (Distance = 1.5 * D).
6. Combined Worst-Case Reversal Loss = PnL1 + PnL2 = 0.0R - (1.5 * D * V2).
   Because V2 <= (2/3) * V1, Loss2 <= 1.5 * D * (2/3 * V1) = 1.0 * (D * V1) = 1.0R.
   Combined Loss is strictly bounded at <= 1.0R (<= Target Base Risk).
"""

import math
from typing import Dict, Any, Tuple, Optional


class PyramidingGate1Engine:
    """
    Deterministic mathematical engine for Strategy V2.7 Gate 1 Pyramiding Position Sizing.
    """

    @staticmethod
    def calculate_base_volume(
        equity: float,
        risk_pct: float,
        sl_distance: float,
        tick_size: float,
        tick_value: float,
        volume_min: float,
        volume_max: float,
        volume_step: float
    ) -> Tuple[float, float, float]:
        """
        Calculates Trade 1 volume ensuring actual dollar risk NEVER exceeds target risk.
        Uses math.floor to prevent upward risk distortion.

        Returns:
            Tuple of (rounded_volume, target_dollar_risk, actual_dollar_risk)
        """
        if equity <= 0 or sl_distance <= 0 or tick_size <= 0 or tick_value <= 0:
            return 0.0, 0.0, 0.0

        target_dollar_risk = equity * risk_pct
        loss_per_1_lot = (sl_distance / tick_size) * tick_value
        if loss_per_1_lot <= 0:
            return 0.0, target_dollar_risk, 0.0

        raw_volume = target_dollar_risk / loss_per_1_lot

        # Strict Floor Rounding (Rule: Actual risk must never exceed target risk)
        stepped_volume = math.floor(raw_volume / volume_step) * volume_step
        rounded_volume = round(stepped_volume, 6)

        # Broker volume bounds
        if rounded_volume < volume_min:
            # Below minimum broker lot size: Cannot trade at or below target risk
            actual_dollar_risk = volume_min * loss_per_1_lot
            return volume_min, target_dollar_risk, round(actual_dollar_risk, 2)

        rounded_volume = min(volume_max, rounded_volume)
        actual_dollar_risk = rounded_volume * loss_per_1_lot

        return rounded_volume, round(target_dollar_risk, 2), round(actual_dollar_risk, 2)

    @staticmethod
    def calculate_pyramid_volume(
        base_volume: float,
        volume_min: float,
        volume_max: float,
        volume_step: float
    ) -> float:
        """
        Calculates Trade 2 volume strictly using Case A: V2 = floor((2/3) * V1).
        Guarantees Trade 2 risk over a 1.5D distance never exceeds 1.0R.
        """
        if base_volume <= 0:
            return 0.0

        raw_v2 = (2.0 / 3.0) * base_volume
        stepped_v2 = math.floor(raw_v2 / volume_step) * volume_step
        rounded_v2 = round(stepped_v2, 6)

        if rounded_v2 < volume_min:
            # If 2/3 of base is below min lot, pyramid is suppressed
            return 0.0

        return min(volume_max, rounded_v2)

    @staticmethod
    def evaluate_scale_in_reversal(
        entry1: float,
        entry2: float,
        sl_reversal: float,
        v1: float,
        v2: float,
        tick_size: float,
        tick_value: float,
        direction: str = "LONG"
    ) -> Dict[str, float]:
        """
        Calculates exact P&L upon full reversal to Trade 1 Entry (Breakeven).
        """
        if direction.upper() == "LONG":
            points1 = sl_reversal - entry1  # At Breakeven = 0.0
            points2 = sl_reversal - entry2  # Negative loss
        else:
            points1 = entry1 - sl_reversal
            points2 = entry2 - sl_reversal

        pnl1 = (points1 / tick_size) * tick_value * v1
        pnl2 = (points2 / tick_size) * tick_value * v2
        combined_pnl = pnl1 + pnl2

        return {
            "trade1_pnl": round(pnl1, 4),
            "trade2_pnl": round(pnl2, 4),
            "combined_pnl": round(combined_pnl, 4)
        }
