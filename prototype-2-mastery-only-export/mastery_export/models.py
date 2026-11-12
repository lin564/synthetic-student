"""The two learner models the harness replays each logged session through.

Both maintain the same correctness-only Bayesian Knowledge Tracing mastery
estimate — the per-skill mastery vector that is the ONLY thing the proposed
design lets leave the device. They share the same base trigger thresholds.
The one difference is the data each is allowed to use for its decisions:

  on-device  : mastery (correctness) only. Everything it needs is in the
               mastery vector, so nothing else has to leave the device.

  server     : mastery PLUS the two fine-grained signals districts object to —
               response latency (to catch a fast lucky guess before
               fast-tracking) and hint timing (to scaffold a borderline
               struggler who reaches for a hint early).

Replaying the same fixed log through both and comparing their per-opportunity
decisions isolates exactly what the fine-grained signals buy.
"""
from __future__ import annotations

from .skills import (FT_CHECK, EWMA_ALPHA, FT_THRESHOLD, SCAF_THRESHOLD, HINT_BAND)


def mastery_trail(events: list, skill_params: dict) -> list:
    """Correctness-only BKT posterior after each event — the mastery vector's
    trajectory. Uses nominal skill parameters (what ACE knows), not the
    learner's hidden multipliers."""
    guess = min(0.45, skill_params["guess"])
    slip = min(0.45, skill_params["slip"])
    learn = min(0.60, skill_params["learn"])
    pL = 0.20
    out = []
    for e in events:
        p_correct = pL * (1 - slip) + (1 - pL) * guess
        if e["correct"]:
            num, den = pL * (1 - slip), p_correct
        else:
            num, den = pL * slip, (1 - p_correct)
        pL = (num / den) if den > 0 else pL
        pL = pL + (1 - pL) * learn
        out.append(pL)
    return out


def replay(events: list, skill_params: dict, use_fine_signals: bool) -> list:
    """Return the model's action at each opportunity: 'none', 'fast_track',
    or 'scaffold'. The log is fixed; the model only decides."""
    trail = mastery_trail(events, skill_params)
    struggle = 0.0
    scaffolded = False
    actions = []
    for k, e in enumerate(events):
        opp = k + 1
        act = "none"
        struggle = EWMA_ALPHA * (0 if e["correct"] else 1) + (1 - EWMA_ALPHA) * struggle

        if opp == FT_CHECK and trail[k] >= FT_THRESHOLD:
            # server withholds fast-track when latency says the correct answer
            # was a fast lucky guess; on-device cannot see latency.
            lucky = (use_fine_signals and e["correct"]
                     and e["latency"] < 1.7 and trail[k] < 0.985)
            act = "none" if lucky else "fast_track"
        elif not scaffolded:
            # server lets an early hint pull a borderline struggler in; the
            # on-device model only has the correctness-based struggle signal.
            early_hint = (use_fine_signals and e["hint_used"]
                          and e["hint_time"] is not None and e["hint_time"] < 0.30)
            if struggle >= SCAF_THRESHOLD or (early_hint and struggle >= SCAF_THRESHOLD - HINT_BAND):
                act = "scaffold"
                scaffolded = True
        actions.append(act)
    return actions


def divergence_cause(event: dict, server_act: str, device_act: str) -> str:
    """Best-effort attribution of one divergent decision to a fine signal."""
    if (server_act == "fast_track") != (device_act == "fast_track"):
        if event["correct"] and event["latency"] < 1.7:
            return "latency"
    if (server_act == "scaffold") != (device_act == "scaffold"):
        if event["hint_used"] and event["hint_time"] is not None and event["hint_time"] < 0.30:
            return "hint_timing"
    return "other"
