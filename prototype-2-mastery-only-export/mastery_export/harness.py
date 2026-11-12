"""The side-by-side replay harness.

Replays each fixed logged session through the on-device model and the server
model, records every adaptation decision each makes, and reports the share
that diverge — overall and among scaffold and fast-track triggers — plus an
attribution of each divergence to the fine-grained signal that caused it and
the data footprint that leaves the device under each design.
"""
from __future__ import annotations
import numpy as np

from .skills import SKILLS, DIVERGENCE_THRESHOLD
from .models import replay, divergence_cause
from .sessions import session_footprint


def run_harness(logs: list, n_seeds_note: int = 1) -> dict:
    decisions = 0
    diverged = 0
    ft_total = ft_div = 0
    scaf_total = scaf_div = 0
    causes = {"latency": 0, "hint_timing": 0, "other": 0}
    raw_bytes = mastery_bytes = 0
    events_total = 0

    for L in logs:
        params = SKILLS[L["skill"]][1]
        server = replay(L["events"], params, use_fine_signals=True)
        device = replay(L["events"], params, use_fine_signals=False)

        fp = session_footprint(L)
        raw_bytes += fp["raw_bytes"]
        mastery_bytes += fp["mastery_bytes"]
        events_total += fp["events"]

        for k, (a, b) in enumerate(zip(server, device)):
            decisions += 1
            fired = (a in ("scaffold", "fast_track")) or (b in ("scaffold", "fast_track"))
            if a == "fast_track" or b == "fast_track":
                ft_total += 1
                if a != b:
                    ft_div += 1
            if a == "scaffold" or b == "scaffold":
                scaf_total += 1
                if a != b:
                    scaf_div += 1
            if a != b:
                diverged += 1
                causes[divergence_cause(L["events"][k], a, b)] += 1

    trig_total = ft_total + scaf_total
    trig_div = ft_div + scaf_div
    combined = trig_div / trig_total if trig_total else 0.0

    return {
        "sessions": len(logs),
        "decision_points": decisions,
        "overall_divergence": diverged / decisions if decisions else 0.0,
        "trigger_divergence": combined,
        "fast_track": {"total": ft_total, "diverged": ft_div,
                       "rate": ft_div / ft_total if ft_total else 0.0},
        "scaffold": {"total": scaf_total, "diverged": scaf_div,
                     "rate": scaf_div / scaf_total if scaf_total else 0.0},
        "causes": causes,
        "threshold": DIVERGENCE_THRESHOLD,
        "passes": combined < DIVERGENCE_THRESHOLD,
        "footprint": {
            "raw_bytes": raw_bytes,
            "mastery_bytes": mastery_bytes,
            "events": events_total,
            "reduction_x": raw_bytes / mastery_bytes if mastery_bytes else 0.0,
            "pct_leaving": 100.0 * mastery_bytes / raw_bytes if raw_bytes else 0.0,
        },
    }


def run_multi(sample_population, log_sessions, pop_seed=1, log_seeds=(100, 101, 102, 103, 104)):
    """Run the harness over several session resamples for a stable estimate."""
    pop = sample_population(200, seed=pop_seed)
    runs = [run_harness(log_sessions(pop, seed=s)) for s in log_seeds]
    combined = [r["trigger_divergence"] for r in runs]
    base = runs[0]
    base["trigger_divergence_mean"] = float(np.mean(combined))
    base["trigger_divergence_std"] = float(np.std(combined))
    base["passes"] = base["trigger_divergence_mean"] < base["threshold"]
    base["n_resamples"] = len(runs)
    return base
