"""
Runner for V2.7 Ablation Study.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from rsi_trend_pullback.research.v27_ablation_study import run_full_ablation_matrix

if __name__ == "__main__":
    run_full_ablation_matrix()
