"""
Standalone runner for Independent V2.7 Validation.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from compare_v27_independent_vs_original import perform_full_independent_comparison

if __name__ == "__main__":
    perform_full_independent_comparison()
