"""
Periodic Batch Reporter for Paper Trading Audits (Generated every 10 trades).
Monitors execution quality, friction drag delta, and flags human-review risk alerts without auto-termination.
"""

from typing import List, Dict, Any
from .audit_logger import ShadowAuditRecord, DivergenceCategory


class PeriodicBatchReporter:
    """
    Generates structured 10-trade audit reports.
    """

    @staticmethod
    def generate_10_trade_summary(
        records: List[ShadowAuditRecord],
        batch_number: int,
        initial_capital: float = 100000.0,
        mc_warning_threshold_pct: float = 11.8
    ) -> str:
        if not records:
            return "No trades recorded in batch."

        n_trades = len(records)
        wins = [r for r in records if r.actual_net_pnl > 0]
        losses = [r for r in records if r.actual_net_pnl < 0]

        theo_pnl = sum(r.theoretical_net_pnl for r in records)
        actual_pnl = sum(r.actual_net_pnl for r in records)
        friction_drag = sum(r.friction_drag for r in records)

        avg_slip_entry = sum(r.entry_slippage for r in records) / n_trades
        avg_spread = sum(r.spread_at_entry for r in records) / n_trades
        avg_latency = sum(r.execution_delay_ms for r in records) / n_trades

        # Drawdown calculation
        eq = initial_capital
        peak = initial_capital
        max_dd = 0.0
        for r in records:
            eq += r.actual_net_pnl
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

        status_warning = "NORMAL OPERATION"
        if max_dd >= mc_warning_threshold_pct:
            status_warning = (
                f"RISK_ALERT: Current Drawdown ({max_dd:.2f}%) exceeded historical Monte Carlo sequence benchmark ({mc_warning_threshold_pct}%). "
                f"Action: Flagged for Human Investigation / Oversight (Strategy NOT automatically shut down)."
            )

        mismatches = [r for r in records if r.divergence_category != DivergenceCategory.NONE]

        report = []
        report.append(f"### [Paper Trading Audit] Batch #{batch_number} Summary (Trades {n_trades-9 if n_trades>=10 else 1} to {n_trades})")
        report.append(f"**Operational Status:** `{status_warning}`\n")
        
        report.append("| Metric | Value | Metric | Value |")
        report.append("|---|---|---|---|")
        report.append(f"| **Batch Trades** | {len(records[-10:])} | **Cumulative Trades** | {n_trades} |")
        report.append(f"| **Cumulative Win Rate** | {len(wins)/n_trades*100:.1f}% ({len(wins)}W/{len(losses)}L) | **Actual Net P&L** | ${actual_pnl:+,.2f} |")
        report.append(f"| **Theoretical Net P&L** | ${theo_pnl:+,.2f} | **Friction Drag Delta** | ${friction_drag:,.2f} |")
        report.append(f"| **Avg Entry Slippage** | ${avg_slip_entry:.2f} / oz | **Avg Entry Spread** | ${avg_spread:.2f} / oz |")
        report.append(f"| **Avg Latency** | {avg_latency:.1f} ms | **Current Max DD** | {max_dd:.2f}% |")

        if mismatches:
            report.append(f"\n**Execution Divergences Flagged ({len(mismatches)} total):**")
            for m in mismatches[-5:]:
                report.append(f"- `Trade #{m.trade_id}` [{m.divergence_category.value}]: {m.divergence_notes}")
        else:
            report.append("\n**Execution Divergences:** Zero anomalies detected. Live execution strictly synchronized with theoretical model.")

        return "\n".join(report)
