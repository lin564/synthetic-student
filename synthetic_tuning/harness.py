"""The simulation harness: run a cohort, return aggregates only, calibrate.

This module is where the two-stream principle is enforced in code. A whole
cohort of synthetic students is simulated, but `run_cohort` returns a small
dict of COHORT-LEVEL aggregates and nothing per-student. That mirrors the
engineering-stream rule from the write-up: "The real-world input to the
engineering stream is aggregate only: did the fast-track trigger fire too
often across a cohort, not for whom." The per-student records are built,
used to compute the aggregates, and discarded inside this function.

`calibrate` sweeps one trigger threshold across a grid, averaging each point
over several cohort resamples so the calibration curves are smooth.
"""
from __future__ import annotations
import numpy as np

from .skills import SKILLS
from .learners import population_size
from .ace import run_student


def run_cohort(pop: dict, seed: int, ft_thr: float = 0.90,
               scaf_thr: float = 0.55, ft_hint_cap: float = 0.34) -> dict:
    """Simulate the whole cohort and return AGGREGATES ONLY.

    Nothing identifiable about any single synthetic student leaves this
    function; only cohort statistics are returned.
    """
    n = population_size(pop)
    S = len(SKILLS)
    rng = np.random.default_rng(seed)

    mastery = np.zeros((n, S))
    retention = np.zeros((n, S))
    ft = 0
    scaf = 0
    opps = 0

    for i in range(n):
        rec = run_student(pop, i, rng, ft_thr=ft_thr, scaf_thr=scaf_thr,
                          ft_hint_cap=ft_hint_cap)
        mastery[i] = rec["mastery"]
        retention[i] = rec["retention"]
        ft += rec["ft_fired"]
        scaf += rec["scaf_fired"]
        opps += rec["opportunities"]

    encounters = n * S
    per_student_mastery = mastery.mean(axis=1)   # local; not returned

    return {
        # --- trigger firing rates (per skill encounter) ---
        "ft_rate": ft / encounters,
        "scaf_rate": scaf / encounters,
        # --- aggregate learning outcomes ---
        "mean_mastery": float(mastery.mean()),
        "bottom_quartile_mastery": float(np.quantile(per_student_mastery, 0.25)),
        "retention": float(retention.mean()),
        "opportunities_per_skill": opps / encounters,
        # --- bookkeeping ---
        "n_students": n,
    }


def calibrate(pop: dict, which: str, grid, base_seed: int = 100,
              n_seeds: int = 5, **fixed) -> dict:
    """Sweep `which` ('ft_thr' or 'scaf_thr') over `grid`.

    Each threshold is averaged over `n_seeds` cohort resamples. Returns the
    grid, the mean firing rate of the matching trigger, its std band, and the
    mean outcome curves (mastery / bottom-quartile / retention / efficiency).
    """
    rate_key = "ft_rate" if which == "ft_thr" else "scaf_rate"
    rate_mean, rate_std = [], []
    mastery, bottomq, retention, opps = [], [], [], []

    for v in grid:
        kwargs = dict(fixed)
        kwargs[which] = v
        runs = [run_cohort(pop, base_seed + k, **kwargs) for k in range(n_seeds)]
        rates = [r[rate_key] for r in runs]
        rate_mean.append(float(np.mean(rates)))
        rate_std.append(float(np.std(rates)))
        mastery.append(float(np.mean([r["mean_mastery"] for r in runs])))
        bottomq.append(float(np.mean([r["bottom_quartile_mastery"] for r in runs])))
        retention.append(float(np.mean([r["retention"] for r in runs])))
        opps.append(float(np.mean([r["opportunities_per_skill"] for r in runs])))

    return {
        "which": which,
        "grid": list(grid),
        "rate_key": rate_key,
        "rate_mean": rate_mean,
        "rate_std": rate_std,
        "mean_mastery": mastery,
        "bottom_quartile_mastery": bottomq,
        "retention": retention,
        "opportunities_per_skill": opps,
    }


def pick_threshold(curve: dict, target: float) -> float:
    """Return the grid threshold whose mean firing rate is closest to `target`."""
    rates = curve["rate_mean"]
    grid = curve["grid"]
    idx = int(np.argmin([abs(r - target) for r in rates]))
    return grid[idx]
