"""
Report generator for backtest results, CSV trade logs, and state transition audits.
"""

from typing import List, Optional
import csv
import os
from ..metrics.performance import PerformanceMetrics
from ..portfolio.position import TradeRecord
from ..state_machine.states import StateTransitionRecord
from ..portfolio.portfolio import EquityPoint


class ReportGenerator:
    """
    Exports CSV logs and formats quantitative markdown reports.
    """

    @staticmethod
    def export_trade_log_csv(trades: List[TradeRecord], output_path: str) -> None:
        """
        Exports trade log matching the exact required schema.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "trade_id",
                "direction",
                "signal_timestamp",
                "entry_timestamp",
                "entry_price",
                "exit_signal_timestamp",
                "exit_timestamp",
                "exit_price",
                "holding_bars",
                "gross_pnl",
                "fees",
                "slippage",
                "net_pnl",
                "return_pct",
                "state_at_entry",
                "state_at_exit",
                "exit_reason"
            ])
            for t in trades:
                writer.writerow([
                    t.trade_id,
                    t.direction.value,
                    t.signal_timestamp.isoformat() if t.signal_timestamp else "",
                    t.entry_timestamp.isoformat() if t.entry_timestamp else "",
                    f"{t.entry_price:.5f}",
                    t.exit_signal_timestamp.isoformat() if t.exit_signal_timestamp else "",
                    t.exit_timestamp.isoformat() if t.exit_timestamp else "",
                    f"{t.exit_price:.5f}" if t.exit_price is not None else "",
                    t.holding_bars,
                    f"{t.gross_pnl:.4f}",
                    f"{t.fees:.4f}",
                    f"{t.slippage:.4f}",
                    f"{t.net_pnl:.4f}",
                    f"{t.return_pct:.4f}",
                    t.state_at_entry.value if t.state_at_entry else "",
                    t.state_at_exit.value if t.state_at_exit else "",
                    t.exit_reason
                ])

    @staticmethod
    def export_state_log_csv(transitions: List[StateTransitionRecord], output_path: str) -> None:
        """
        Exports state transition log for complete auditability.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "bar_index",
                "timestamp",
                "previous_state",
                "current_state",
                "RSI",
                "transition_reason"
            ])
            for r in transitions:
                writer.writerow([
                    r.bar_index,
                    r.timestamp.isoformat(),
                    r.previous_state.value,
                    r.current_state.value,
                    f"{r.rsi:.4f}" if r.rsi is not None else "NaN",
                    r.transition_reason
                ])

    @staticmethod
    def format_markdown_summary(
        dataset_name: str,
        metrics: PerformanceMetrics,
        is_realistic: bool
    ) -> str:
        """
        Generates a clean, comprehensive markdown performance summary.
        """
        mode_str = "Realistic (Commission + Spread + Slippage)" if is_realistic else "Raw (Zero Cost)"
        
        md = []
        md.append(f"## Backtest Report — {dataset_name}")
        md.append(f"**Execution Mode:** {mode_str}\n")
        md.append(f"### 1. Key Performance Overview")
        md.append("| Metric | Value | Metric | Value |")
        md.append("|---|---|---|---|")
        md.append(f"| **Initial Capital** | ${metrics.initial_capital:,.2f} | **Ending Equity** | ${metrics.ending_equity:,.2f} |")
        md.append(f"| **Total Net P&L** | ${metrics.total_net_pnl:,.2f} | **Total Return** | {metrics.total_return_pct:+.2f}% |")
        md.append(f"| **Profit Factor** | {metrics.profit_factor:.2f} | **Win Rate** | {metrics.win_rate_pct:.2f}% |")
        md.append(f"| **Max Drawdown ($)** | ${metrics.max_drawdown_amount:,.2f} | **Max Drawdown (%)** | {metrics.max_drawdown_pct:.2f}% |")
        md.append(f"| **Expectancy / Trade** | ${metrics.expectancy_per_trade:+.2f} | **Avg Holding Bars** | {metrics.avg_holding_bars:.1f} bars |")

        md.append(f"\n### 2. Trade Statistics")
        md.append("| Trade Metric | Value |")
        md.append("|---|---|")
        md.append(f"| Total Trades | **{metrics.total_trades}** |")
        md.append(f"| Long Trades | {metrics.long_trades} |")
        md.append(f"| Short Trades | {metrics.short_trades} |")
        md.append(f"| Winning Trades | {metrics.winning_trades} ({metrics.win_rate_pct:.1f}%) |")
        md.append(f"| Losing Trades | {metrics.losing_trades} ({metrics.loss_rate_pct:.1f}%) |")
        md.append(f"| Average Win | ${metrics.avg_win:,.2f} |")
        md.append(f"| Average Loss | ${metrics.avg_loss:,.2f} |")
        md.append(f"| Payoff Ratio (Avg Win / Avg Loss) | {metrics.win_loss_payoff_ratio:.2f} |")
        md.append(f"| Largest Win | ${metrics.largest_win:,.2f} |")
        md.append(f"| Largest Loss | ${metrics.largest_loss:,.2f} |")
        md.append(f"| Max Consecutive Wins | {metrics.max_consecutive_wins} |")
        md.append(f"| Max Consecutive Losses | {metrics.max_consecutive_losses} |")
        md.append(f"| Gross Profit | ${metrics.gross_profit:,.2f} |")
        md.append(f"| Gross Loss | ${metrics.gross_loss:,.2f} |")
        md.append(f"| Total Fees & Slippage | ${metrics.total_fees + metrics.total_slippage:,.2f} |")

        md.append(f"\n### 3. Directional Breakdown")
        md.append("| Direction | Trades | Win Rate | Net P&L | Avg Trade | Profit Factor |")
        md.append("|---|---|---|---|---|---|")
        for side, d in metrics.direction_breakdown.items():
            md.append(f"| **{side}** | {d.get('trades', 0)} | {d.get('win_rate', 0.0):.1f}% | ${d.get('net_pnl', 0.0):+,.2f} | ${d.get('avg_trade', 0.0):+,.2f} | {d.get('profit_factor', 0.0):.2f} |")

        md.append(f"\n### 4. Holding Duration Breakdown")
        md.append("| Duration Bucket | Trades | Win Rate | Net P&L | Avg Trade |")
        md.append("|---|---|---|---|---|")
        for b_name, d in metrics.duration_buckets.items():
            md.append(f"| **{b_name}** | {d.get('trades', 0)} | {d.get('win_rate', 0.0):.1f}% | ${d.get('net_pnl', 0.0):+,.2f} | ${d.get('avg_trade', 0.0):+,.2f} |")

        if metrics.yearly_breakdown:
            md.append(f"\n### 5. Annual Breakdown")
            md.append("| Year | Trades | Win Rate | Net P&L | Avg Trade |")
            md.append("|---|---|---|---|---|")
            for yr, d in metrics.yearly_breakdown.items():
                md.append(f"| **{yr}** | {d.get('trades', 0)} | {d.get('win_rate', 0.0):.1f}% | ${d.get('net_pnl', 0.0):+,.2f} | ${d.get('avg_trade', 0.0):+,.2f} |")

        return "\n".join(md)
