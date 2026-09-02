"""
Strategy V2.7 Research Candidate - Gate 2: Advanced Portfolio Heat & Multi-Asset Risk Engine.
Strictly implements:
1. Dynamic Portfolio Heat calculation based on open stop distance + explicit friction buffer.
2. Hard Heat Ceiling: Aggregate Portfolio Heat <= 6.0%.
3. Macro Economic Cluster Sub-Cap: Cluster Risk <= 4.0% (USD_BLOC vs CRYPTO) to structurally prevent FOMC/NFP shock correlation stacking.
4. Hard Position Count Cap: Max Active Positions <= 2.
5. Max Single-Order Volume Safety Ceiling: 0.50 lots.
6. Clean 3-Tier Deterministic Signal Collision Resolution (ZERO Historical Performance Bias):
   - Tier 1: Highest Kaufman ER14 (Descending)
   - Tier 2: Lowest Spread / ATR14 Friction Ratio (Ascending)
   - Tier 3: Deterministic Canonical Symbol Order (Alphabetical: BTCUSD, GBPUSD, US500, USDJPY, XAUUSD)
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional, Set
import math


@dataclass
class ActivePosition:
    symbol: str
    is_pyramid: bool
    direction: str  # "LONG" or "SHORT"
    entry_price: float
    current_price: float
    current_stop_price: float
    volume: float
    tick_size: float
    tick_value: float  # Value of 1 tick in Account Base Currency (e.g. THB)
    friction_buffer_cur: float  # Explicit friction/slippage buffer in Account Base Currency

    def calculate_potential_loss(self) -> float:
        """
        Calculates maximum monetary loss to current stop level in account currency.
        If stop is in profit or at BE, price loss is 0, but friction buffer is preserved.
        """
        if self.direction.upper() == "LONG":
            loss_ticks = (max(0.0, self.entry_price - self.current_stop_price) / self.tick_size) if self.current_stop_price < self.entry_price else 0.0
        else:
            loss_ticks = (max(0.0, self.current_stop_price - self.entry_price) / self.tick_size) if self.current_stop_price > self.entry_price else 0.0

        monetary_loss = loss_ticks * self.tick_value * self.volume
        return monetary_loss + self.friction_buffer_cur


@dataclass
class CandidateSignal:
    symbol: str
    is_pyramid: bool
    direction: str
    entry_price: float
    stop_price: float
    volume: float
    tick_size: float
    tick_value: float
    friction_buffer_cur: float
    er_14: float  # Tier 1: Kaufman Efficiency Ratio
    spread_atr_ratio: float  # Tier 2: Spread / ATR14 Friction Ratio (Cost efficiency)

    def calculate_new_order_risk(self) -> float:
        if self.direction.upper() == "LONG":
            dist = max(0.0, self.entry_price - self.stop_price)
        else:
            dist = max(0.0, self.stop_price - self.entry_price)
        loss_ticks = dist / self.tick_size
        return (loss_ticks * self.tick_value * self.volume) + self.friction_buffer_cur


class PortfolioHeatEngineGate2:
    """
    Deterministic Gate 2 Portfolio Heat & Macro Cluster Management Engine.
    """
    MAX_HEAT_RATIO: float = 0.060          # 6.0% Maximum Aggregate Portfolio Heat
    MAX_CLUSTER_HEAT_RATIO: float = 0.040  # 4.0% Maximum Economic Cluster Sub-Cap
    MAX_ACTIVE_POSITIONS: int = 2           # Maximum 2 concurrent positions across portfolio
    MAX_VOLUME_CEILING: float = 0.50        # Hard safety ceiling of 0.50 lots per order

    ECONOMIC_CLUSTERS: Dict[str, str] = {
        "XAUUSD": "USD_BLOC",
        "USDJPY": "USD_BLOC",
        "GBPUSD": "USD_BLOC",
        "US500":  "USD_BLOC",
        "BTCUSD": "CRYPTO"
    }

    @classmethod
    def get_cluster(cls, symbol: str) -> str:
        sym_clean = symbol.upper().replace("#", "").replace("M", "").replace("CASH", "")
        for k, v in cls.ECONOMIC_CLUSTERS.items():
            if k in sym_clean or sym_clean in k:
                return v
        return "GENERAL"

    @classmethod
    def calculate_current_heat(cls, active_positions: List[ActivePosition], equity: float) -> Tuple[float, float]:
        if equity <= 0:
            return 0.0, 1.0

        total_potential_loss = sum(pos.calculate_potential_loss() for pos in active_positions)
        heat_pct = total_potential_loss / equity
        return round(total_potential_loss, 2), round(heat_pct, 6)

    @classmethod
    def calculate_cluster_heat(cls, active_positions: List[ActivePosition], cluster_name: str, equity: float) -> Tuple[float, float]:
        if equity <= 0:
            return 0.0, 1.0

        cluster_loss = sum(
            pos.calculate_potential_loss()
            for pos in active_positions
            if cls.get_cluster(pos.symbol) == cluster_name
        )
        cluster_heat_pct = cluster_loss / equity
        return round(cluster_loss, 2), round(cluster_heat_pct, 6)

    @classmethod
    def can_accept_order(
        cls,
        active_positions: List[ActivePosition],
        candidate: CandidateSignal,
        equity: float
    ) -> Tuple[bool, str, float]:
        # 1. Check Max Active Position Cap
        if len(active_positions) >= cls.MAX_ACTIVE_POSITIONS:
            current_loss, current_heat = cls.calculate_current_heat(active_positions, equity)
            return False, f"POSITION_CAP_EXCEEDED: Active positions ({len(active_positions)}) >= Max ({cls.MAX_ACTIVE_POSITIONS})", current_heat

        # 2. Check Hard Volume Ceiling
        if candidate.volume > cls.MAX_VOLUME_CEILING + 1e-7:
            _, current_heat = cls.calculate_current_heat(active_positions, equity)
            return False, f"MAX_VOLUME_EXCEEDED: Volume ({candidate.volume:.2f}) exceeds hard ceiling ({cls.MAX_VOLUME_CEILING:.2f})", current_heat

        current_loss, _ = cls.calculate_current_heat(active_positions, equity)
        new_order_risk = candidate.calculate_new_order_risk()
        projected_total_loss = current_loss + new_order_risk
        projected_heat_pct = projected_total_loss / equity

        # 3. Check Aggregate Portfolio Heat Ceiling (6.0%)
        if projected_heat_pct > (cls.MAX_HEAT_RATIO + 1e-7):
            return False, f"HEAT_CAP_EXCEEDED: Projected heat ({projected_heat_pct*100:.2f}%) > Max ({cls.MAX_HEAT_RATIO*100:.1f}%)", round(projected_heat_pct, 6)

        # 4. Check Macro Economic Cluster Sub-Cap (4.0%)
        target_cluster = cls.get_cluster(candidate.symbol)
        cluster_loss, _ = cls.calculate_cluster_heat(active_positions, target_cluster, equity)
        projected_cluster_loss = cluster_loss + new_order_risk
        projected_cluster_heat_pct = projected_cluster_loss / equity

        if projected_cluster_heat_pct > (cls.MAX_CLUSTER_HEAT_RATIO + 1e-7):
            return False, f"CLUSTER_HEAT_CAP_EXCEEDED: Projected {target_cluster} heat ({projected_cluster_heat_pct*100:.2f}%) > Max ({cls.MAX_CLUSTER_HEAT_RATIO*100:.1f}%)", round(projected_heat_pct, 6)

        return True, "ACCEPTED", round(projected_heat_pct, 6)

    @classmethod
    def resolve_signal_collisions(
        cls,
        active_positions: List[ActivePosition],
        candidates: List[CandidateSignal],
        equity: float
    ) -> List[Tuple[CandidateSignal, bool, str]]:
        """
        Clean 3-Tier Deterministic Collision Resolution (ZERO historical performance bias):
        1. Primary: Highest Kaufman ER14 (Descending) -> strongest directional velocity.
        2. Secondary: Lowest Spread / ATR14 Ratio (Ascending) -> lowest frictional drag.
        3. Tertiary: Canonical Alphabetical Symbol Name (Ascending: BTCUSD < GBPUSD < US500 < USDJPY < XAUUSD).
        """
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (-round(c.er_14, 4), round(c.spread_atr_ratio, 4), c.symbol.upper())
        )

        results = []
        current_active = list(active_positions)

        for cand in sorted_candidates:
            accepted, reason, proj_heat = cls.can_accept_order(current_active, cand, equity)
            results.append((cand, accepted, reason))
            if accepted:
                current_active.append(ActivePosition(
                    symbol=cand.symbol,
                    is_pyramid=cand.is_pyramid,
                    direction=cand.direction,
                    entry_price=cand.entry_price,
                    current_price=cand.entry_price,
                    current_stop_price=cand.stop_price,
                    volume=cand.volume,
                    tick_size=cand.tick_size,
                    tick_value=cand.tick_value,
                    friction_buffer_cur=cand.friction_buffer_cur
                ))

        return results
