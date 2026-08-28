"""
Execution runner for Missed Signal Scanner.
Scans XAUUSD H1 historical dataset (2020-2025) and reports availability coverage in Bangkok time (UTC+7).
"""

import os
from rsi_trend_pullback.data.loader import DataLoader
from rsi_trend_pullback.data.xauusd_builder import generate_xauusd_h1_historical_dataset, save_xauusd_csv
from rsi_trend_pullback.missed_signal_scanner import MissedSignalScanner


def run_scanner():
    h1_path = "d:/Kaeha/rsi_trend_pullback/data/xauusd_h1_2020_2025.csv"
    if not os.path.exists(h1_path):
        candles = generate_xauusd_h1_historical_dataset()
        save_xauusd_csv(candles, h1_path)

    candles = DataLoader.load_from_csv(h1_path)
    scanner = MissedSignalScanner(data_timezone_offset_hours=0) # Data is UTC

    sig_records, daily_summaries, stats = scanner.scan_dataset(candles)

    out_dir = "d:/Kaeha/rsi_trend_pullback/output_missed_signals"
    out_sig_csv = f"{out_dir}/missed_signals_log.csv"
    out_daily_csv = f"{out_dir}/missed_signals_daily_summary.csv"

    scanner.export_csv_reports(sig_records, daily_summaries, out_sig_csv, out_daily_csv)

    print("=" * 80)
    print("MISSED SIGNAL SCANNER REPORT — STRATEGY V2.6 (XAUUSD H1 2020-2025)")
    print(f"Schedule (Asia/Bangkok): Online [09:00-16:00, 17:00-22:00] | Offline [16:00-17:00, 22:00-09:00]")
    print("=" * 80)
    print(f"  * Total Strategy V2.6 Signals : {stats['total_signals']} signals")
    print(f"  * Paper-Executed Signals (Online) : {stats['paper_executed_signals']} signals ({100.0 - stats['pct_missed']:.1f}%)")
    print(f"  * Missed Signals (Offline)       : {stats['missed_signals']} signals ({stats['pct_missed']:.1f}%)")
    print("-" * 80)
    print("SIGNAL DISTRIBUTION BY HOUR (Asia/Bangkok Time UTC+7):")
    print("  Hour   | Online Status | Signals Count | % of Total")
    print("  -------|---------------|---------------|-----------")
    for h in range(24):
        cnt = stats['hourly_distribution'].get(h, 0)
        pct = (cnt / stats['total_signals'] * 100.0) if stats['total_signals'] > 0 else 0.0
        is_on = (9 <= h < 16) or (17 <= h < 22)
        status_lbl = "ONLINE " if is_on else "OFFLINE"
        bar_chart = "█" * int(pct * 1.5)
        print(f"  {h:02d}:00  | {status_lbl}       | {cnt:4d} signals  | {pct:5.1f}%  {bar_chart}")

    print("-" * 80)
    print("SIGNAL DISTRIBUTION BY DAY OF WEEK:")
    for day, cnt in stats['weekday_distribution'].items():
        pct = (cnt / stats['total_signals'] * 100.0) if stats['total_signals'] > 0 else 0.0
        bar_chart = "█" * int(pct * 1.5)
        print(f"  {day:<10} : {cnt:4d} signals ({pct:5.1f}%) {bar_chart}")
    print("=" * 80)
    print(f"[CSV EXPORTED] Detailed Signals Log : {out_sig_csv}")
    print(f"[CSV EXPORTED] Daily Summaries Log   : {out_daily_csv}")
    print("=" * 80)

    return stats


if __name__ == "__main__":
    run_scanner()
