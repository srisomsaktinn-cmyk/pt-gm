"""
Quantitative performance metrics calculator for backtesting.
Calculates trade statistics, risk/return profiles, drawdowns, streaks,
and multi-dimensional market breakdowns.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import math
from ..portfolio.position import TradeRecord
from ..portfolio.portfolio import EquityPoint
from ..state_machine.states import PositionSide


@dataclass
class PerformanceMetrics:
    """
    Comprehensive performance metrics report container.
    """
    # Trade Stats
    total_trades: int = 0
    long_trades: int = 0
    short_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0
    win_rate_pct: float = 0.0
    loss_rate_pct: float = 0.0

    # PnL & Expectancy
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    total_fees: float = 0.0
    total_slippage: float = 0.0
    total_net_pnl: float = 0.0
    profit_factor: float = 0.0
    expectancy_per_trade: float = 0.0
    expectancy_pct: float = 0.0

    # Win/Loss Amounts
    avg_win: float = 0.0
    avg_loss: float = 0.0
    win_loss_payoff_ratio: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    avg_trade_pnl: float = 0.0

    # Duration & Streaks
    avg_holding_bars: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0

    # Drawdowns
    max_drawdown_amount: float = 0.0
    max_drawdown_pct: float = 0.0
    initial_capital: float = 10000.0
    ending_equity: float = 10000.0
    total_return_pct: float = 0.0

    # Breakdowns
    direction_breakdown: Dict[str, Any] = field(default_factory=dict)
    yearly_breakdown: Dict[int, Any] = field(default_factory=dict)
    monthly_breakdown: Dict[str, Any] = field(default_factory=dict)
    duration_buckets: Dict[str, Any] = field(default_factory=dict)


class MetricsCalculator:
    """
    Calculates statistical and financial metrics from completed trades and equity curves.
    """

    @classmethod
    def calculate(
        cls,
        trades: List[TradeRecord],
        equity_curve: List[EquityPoint],
        initial_capital: float = 10000.0
    ) -> PerformanceMetrics:
        metrics = PerformanceMetrics(initial_capital=initial_capital)
        if not equity_curve:
            return metrics

        metrics.ending_equity = equity_curve[-1].equity
        metrics.total_return_pct = ((metrics.ending_equity / initial_capital) - 1.0) * 100.0

        # Calculate max drawdown from equity curve
        max_dd_amt = 0.0
        max_dd_pct = 0.0
        for pt in equity_curve:
            if pt.drawdown_amount > max_dd_amt:
                max_dd_amt = pt.drawdown_amount
            if pt.drawdown_pct > max_dd_pct:
                max_dd_pct = pt.drawdown_pct
        metrics.max_drawdown_amount = round(max_dd_amt, 4)
        metrics.max_drawdown_pct = round(max_dd_pct, 4)

        if not trades:
            return metrics

        metrics.total_trades = len(trades)
        metrics.long_trades = sum(1 for t in trades if t.direction == PositionSide.LONG)
        metrics.short_trades = sum(1 for t in trades if t.direction == PositionSide.SHORT)

        wins = [t for t in trades if t.net_pnl > 0]
        losses = [t for t in trades if t.net_pnl < 0]
        bes = [t for t in trades if t.net_pnl == 0]

        metrics.winning_trades = len(wins)
        metrics.losing_trades = len(losses)
        metrics.breakeven_trades = len(bes)
        metrics.win_rate_pct = round((len(wins) / len(trades)) * 100.0, 2)
        metrics.loss_rate_pct = round((len(losses) / len(trades)) * 100.0, 2)

        # Profits and Losses
        metrics.gross_profit = round(sum(t.gross_pnl for t in wins), 4)
        metrics.gross_loss = round(abs(sum(t.gross_pnl for t in losses)), 4)
        metrics.total_fees = round(sum(t.fees for t in trades), 4)
        metrics.total_slippage = round(sum(t.slippage for t in trades), 4)
        metrics.total_net_pnl = round(sum(t.net_pnl for t in trades), 4)

        metrics.profit_factor = round(
            (metrics.gross_profit / metrics.gross_loss) if metrics.gross_loss > 0 else (999.0 if metrics.gross_profit > 0 else 0.0),
            3
        )

        metrics.avg_win = round(sum(t.net_pnl for t in wins) / len(wins), 4) if wins else 0.0
        metrics.avg_loss = round(abs(sum(t.net_pnl for t in losses) / len(losses)), 4) if losses else 0.0
        metrics.win_loss_payoff_ratio = round((metrics.avg_win / metrics.avg_loss), 3) if metrics.avg_loss > 0 else 0.0

        metrics.largest_win = round(max((t.net_pnl for t in wins), default=0.0), 4)
        metrics.largest_loss = round(min((t.net_pnl for t in losses), default=0.0), 4)
        metrics.avg_trade_pnl = round(metrics.total_net_pnl / len(trades), 4)

        # Expectancy: (WinRate * AvgWin) - (LossRate * AvgLoss)
        win_prob = len(wins) / len(trades)
        loss_prob = len(losses) / len(trades)
        metrics.expectancy_per_trade = round((win_prob * metrics.avg_win) - (loss_prob * metrics.avg_loss), 4)
        metrics.expectancy_pct = round(sum(t.return_pct for t in trades) / len(trades), 4)

        # Holding duration
        metrics.avg_holding_bars = round(sum(t.holding_bars for t in trades) / len(trades), 2)

        # Streaks
        cur_w_streak, max_w_streak = 0, 0
        cur_l_streak, max_l_streak = 0, 0
        for t in trades:
            if t.net_pnl > 0:
                cur_w_streak += 1
                cur_l_streak = 0
                max_w_streak = max(max_w_streak, cur_w_streak)
            elif t.net_pnl < 0:
                cur_l_streak += 1
                cur_w_streak = 0
                max_l_streak = max(max_l_streak, cur_l_streak)
            else:
                cur_w_streak = 0
                cur_l_streak = 0
        metrics.max_consecutive_wins = max_w_streak
        metrics.max_consecutive_losses = max_l_streak

        # ── Breakdowns ──
        metrics.direction_breakdown = cls._calc_direction_breakdown(trades)
        metrics.yearly_breakdown = cls._calc_yearly_breakdown(trades)
        metrics.monthly_breakdown = cls._calc_monthly_breakdown(trades)
        metrics.duration_buckets = cls._calc_duration_buckets(trades)

        return metrics

    @staticmethod
    def _calc_direction_breakdown(trades: List[TradeRecord]) -> Dict[str, Any]:
        result = {}
        for side in [PositionSide.LONG, PositionSide.SHORT]:
            sub = [t for t in trades if t.direction == side]
            if not sub:
                result[side.value] = {"trades": 0, "net_pnl": 0.0, "win_rate": 0.0}
                continue
            wins = sum(1 for t in sub if t.net_pnl > 0)
            result[side.value] = {
                "trades": len(sub),
                "wins": wins,
                "losses": sum(1 for t in sub if t.net_pnl < 0),
                "win_rate": round((wins / len(sub)) * 100.0, 2),
                "net_pnl": round(sum(t.net_pnl for t in sub), 4),
                "avg_trade": round(sum(t.net_pnl for t in sub) / len(sub), 4),
                "profit_factor": round(
                    (sum(t.net_pnl for t in sub if t.net_pnl > 0) / abs(sum(t.net_pnl for t in sub if t.net_pnl < 0)))
                    if any(t.net_pnl < 0 for t in sub) else 999.0, 3
                )
            }
        return result

    @staticmethod
    def _calc_yearly_breakdown(trades: List[TradeRecord]) -> Dict[int, Any]:
        years: Dict[int, List[TradeRecord]] = {}
        for t in trades:
            y = t.entry_timestamp.year
            years.setdefault(y, []).append(t)

        result = {}
        for y, sub in sorted(years.items()):
            wins = sum(1 for t in sub if t.net_pnl > 0)
            result[y] = {
                "trades": len(sub),
                "win_rate": round((wins / len(sub)) * 100.0, 2),
                "net_pnl": round(sum(t.net_pnl for t in sub), 4),
                "avg_trade": round(sum(t.net_pnl for t in sub) / len(sub), 4),
                "gross_profit": round(sum(t.net_pnl for t in sub if t.net_pnl > 0), 4),
                "gross_loss": round(abs(sum(t.net_pnl for t in sub if t.net_pnl < 0)), 4)
            }
        return result

    @staticmethod
    def _calc_monthly_breakdown(trades: List[TradeRecord]) -> Dict[str, Any]:
        months: Dict[str, List[TradeRecord]] = {}
        for t in trades:
            m = t.entry_timestamp.strftime("%Y-%m")
            months.setdefault(m, []).append(t)

        result = {}
        for m, sub in sorted(months.items()):
            wins = sum(1 for t in sub if t.net_pnl > 0)
            result[m] = {
                "trades": len(sub),
                "win_rate": round((wins / len(sub)) * 100.0, 2),
                "net_pnl": round(sum(t.net_pnl for t in sub), 4)
            }
        return result

    @staticmethod
    def _calc_duration_buckets(trades: List[TradeRecord]) -> Dict[str, Any]:
        buckets = {
            "1-5 bars": [],
            "6-15 bars": [],
            "16-30 bars": [],
            "31+ bars": []
        }
        for t in trades:
            if t.holding_bars <= 5:
                buckets["1-5 bars"].append(t)
            elif t.holding_bars <= 15:
                buckets["6-15 bars"].append(t)
            elif t.holding_bars <= 30:
                buckets["16-30 bars"].append(t)
            else:
                buckets["31+ bars"].append(t)

        result = {}
        for b_name, sub in buckets.items():
            if not sub:
                result[b_name] = {"trades": 0, "win_rate": 0.0, "net_pnl": 0.0}
                continue
            wins = sum(1 for t in sub if t.net_pnl > 0)
            result[b_name] = {
                "trades": len(sub),
                "wins": wins,
                "win_rate": round((wins / len(sub)) * 100.0, 2),
                "net_pnl": round(sum(t.net_pnl for t in sub), 4),
                "avg_trade": round(sum(t.net_pnl for t in sub) / len(sub), 4)
            }
        return result
