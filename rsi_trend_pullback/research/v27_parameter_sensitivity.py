"""
Strategy V2.7 Parameter Avalanche & Landscape Sensitivity Engine.
THIS IS STRICTLY SENSITIVITY ANALYSIS - NOT OPTIMIZATION.
Evaluates the stability plateau around the Frozen V2.7 parameters:
- ER Threshold: 0.30 -> 0.50 (Step 0.05, Baseline: 0.40)
- RSI Smoothing: 10 -> 18 (Step 2, Baseline: 14)
- ATR Stop Multiple: 2.0 -> 3.0 (Step 0.25, Baseline: 2.5)
- Pyramid Trigger: 1.0R -> 2.0R (Step 0.25R, Baseline: 1.5R)
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, "d:/Kaeha")

from rsi_trend_pullback.research.v27_robustness_stress_oos_suite import run_parameter_sensitivity_audit


def run_full_parameter_landscape() -> Dict[str, Any]:
    sens_results = run_parameter_sensitivity_audit()

    output_path = "d:/Kaeha/v27_parameter_landscape_summary.json"
    summary = {
        "analysis": "Strategy V2.7 Parameter Landscape Sensitivity",
        "timestamp": datetime.now().isoformat(),
        "variations": sens_results
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    return summary


if __name__ == "__main__":
    res = run_full_parameter_landscape()
    print("=" * 80)
    print("V2.7 PARAMETER SENSITIVITY LANDSCAPE COMPLETE")
    print(f"Total Variations Tested: {len(res['variations'])}")
    print("=" * 80)
