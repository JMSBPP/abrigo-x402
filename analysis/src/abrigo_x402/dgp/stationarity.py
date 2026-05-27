"""PITFALLS section 4 + SC-4 stationarity diagnostic.

Computes per-leg event rate on the train vs held-out segments; decides between
'stationary' and 'piecewise_required' per the +/-25% rate-ratio threshold locked in
PRE_REGISTRATION (SC-4 lock).

Consumed by:
  - fit_report.json :: baseline_stationarity_check (orchestrator 03-07)
  - Plan 03-04 verifier (DGP-04 acceptance grid)

Decision rule (LOCKED PRE_REGISTRATION + SC-4):
  For each leg, compute |held_out_rate - train_rate| / train_rate.
  If EITHER leg exceeds STATIONARITY_RATIO_THRESHOLD (0.25) → decision='piecewise_required'.
  Else → decision='stationary'.
  Safety branch: train_rate == 0 on either leg → ratio=inf, decision='piecewise_required'.
"""
from __future__ import annotations

import numpy as np

from abrigo_x402.dgp.held_out import WallClockSplit

# +/-25% locked by PRE_REGISTRATION + SC-4
STATIONARITY_RATIO_THRESHOLD: float = 0.25


def _rate(events: np.ndarray, duration: float) -> float:
    if duration <= 0.0:
        return float("nan")
    return float(np.asarray(events).size) / float(duration)


def baseline_stationarity_check(split: WallClockSplit) -> dict:
    """Return the fit_report.json :: baseline_stationarity_check block.

    Keys:
      - train_rate: [rate_leg_0, rate_leg_1] events/sec on the train window
      - held_out_rate: [rate_leg_0, rate_leg_1] events/sec on the held-out window
      - ratio: [|ho - tr| / tr for each leg]; inf when train_rate is 0 or NaN
      - decision: 'stationary' | 'piecewise_required'
      - threshold: STATIONARITY_RATIO_THRESHOLD (0.25)
      - per_leg_decision: [leg_0_decision, leg_1_decision]
    """
    train_dur = split.t_split - split.window_start
    held_out_dur = split.window_end - split.t_split

    train_rates = (
        _rate(split.train_leg_0, train_dur),
        _rate(split.train_leg_1, train_dur),
    )
    held_out_rates = (
        _rate(split.held_out_leg_0, held_out_dur),
        _rate(split.held_out_leg_1, held_out_dur),
    )

    ratios: list[float] = []
    leg_decisions: list[str] = []
    for tr, ho in zip(train_rates, held_out_rates):
        if tr == 0.0 or np.isnan(tr):
            ratios.append(float("inf"))
            leg_decisions.append("piecewise_required")
            continue
        rel = abs(ho - tr) / tr
        ratios.append(float(rel))
        leg_decisions.append(
            "piecewise_required"
            if rel > STATIONARITY_RATIO_THRESHOLD
            else "stationary"
        )

    decision = (
        "piecewise_required"
        if "piecewise_required" in leg_decisions
        else "stationary"
    )

    return {
        "train_rate": [float(train_rates[0]), float(train_rates[1])],
        "held_out_rate": [float(held_out_rates[0]), float(held_out_rates[1])],
        "ratio": [float(ratios[0]), float(ratios[1])],
        "decision": decision,
        "threshold": float(STATIONARITY_RATIO_THRESHOLD),
        "per_leg_decision": leg_decisions,
    }
