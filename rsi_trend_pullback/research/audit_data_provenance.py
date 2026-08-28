"""
Data Provenance & Dataset File Audit Script.
Directly inspects all CSV dataset files in d:/Kaeha/rsi_trend_pullback/data/
Reports exact line counts, first/last timestamps, duplicates, and calendar coverage.
"""

import os
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List

DATA_DIR = "d:/Kaeha/rsi_trend_pullback/data"

def inspect_dataset_file(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        return {"exists": False, "file_name": os.path.basename(file_path)}

    timestamps = []
    total_rows = 0
    duplicate_count = 0
    seen_timestamps = set()

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            ts_str = row.get("timestamp") or row.get("Date") or row.get("time") or row.get("Time")
            if ts_str:
                # Handle possible formats
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M"):
                    try:
                        dt = datetime.strptime(ts_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    continue

                if dt in seen_timestamps:
                    duplicate_count += 1
                else:
                    seen_timestamps.add(dt)
                timestamps.append(dt)

    if not timestamps:
        return {"exists": True, "file_name": os.path.basename(file_path), "total_rows": total_rows, "valid_timestamps": 0}

    timestamps.sort()
    first_ts = timestamps[0]
    last_ts = timestamps[-1]

    return {
        "exists": True,
        "file_name": os.path.basename(file_path),
        "total_rows": total_rows,
        "unique_timestamps": len(seen_timestamps),
        "duplicate_rows": duplicate_count,
        "first_timestamp": str(first_ts),
        "last_timestamp": str(last_ts),
        "days_span": (last_ts - first_ts).days
    }


def run_full_provenance_audit():
    print("=" * 95)
    print("DATA PROVENANCE & RAW DATASET FILE AUDIT")
    print(f"Inspecting directory: {DATA_DIR}")
    print("=" * 95)

    files_to_check = [
        # In-Sample 2020-2025
        "xauusd_h1_2020_2025.csv",
        "usdjpy_h1_2020_2025.csv",
        "gbpusd_h1_2020_2025.csv",
        "us500_h1_2020_2025.csv",
        "btcusd_h1_2020_2025.csv",
        # Historical / Other datasets
        "xauusd_h1_2014_2025.csv",
        "xauusd_h1_2014_2019.csv",
        "xauusd_h1_2020_2024.csv",
        "xauusd_m15_2020_2024.csv"
    ]

    for fname in files_to_check:
        fpath = os.path.join(DATA_DIR, fname)
        info = inspect_dataset_file(fpath)
        if info["exists"]:
            print(f"\n📄 File: {info['file_name']}")
            print(f"  • Total Rows:          {info['total_rows']:,}")
            print(f"  • Unique Timestamps:   {info['unique_timestamps']:,}")
            print(f"  • Duplicate Rows:      {info['duplicate_rows']}")
            print(f"  • First Timestamp:     {info['first_timestamp']}")
            print(f"  • Last Timestamp:      {info['last_timestamp']}")
            print(f"  • Calendar Span:       {info['days_span']:,} days (~{info['days_span']/365.25:.1f} years)")
        else:
            print(f"\n❌ File NOT found: {fname}")

if __name__ == "__main__":
    run_full_provenance_audit()
