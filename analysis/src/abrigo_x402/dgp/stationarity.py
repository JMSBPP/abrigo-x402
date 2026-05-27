"""Baseline stationarity diagnostic (PITFALLS section 4: +/-25% train_rate vs held_out_rate)."""
from __future__ import annotations
import numpy as np

STATIONARITY_RATIO_THRESHOLD: float = 0.25


def baseline_stationarity_check(split) -> dict:
    """Returns dict: train_rate (per leg), held_out_rate (per leg), ratio,
    decision ('stationary' | 'piecewise_required'), threshold, per_leg_decision.

    `split` is the WallClockSplit dataclass from held_out.py (Wave-1 03-04 surface).
    """
    raise NotImplementedError("Wave 1 plan 03-04 implements this (DGP-04 + SC-4)")
