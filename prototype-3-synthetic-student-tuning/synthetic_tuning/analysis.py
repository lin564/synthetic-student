"""Rigor analyses on top of the core harness.

- parameter_recovery : can the aggregate-only feedback loop recover a cohort's
  true difficulty from one number? Recover a range of known shifts and measure
  the error. This is the method validating itself.
- sensitivity        : how do the headline conclusions move as the (unknown)
  real-cohort assumptions and the method's own knobs change? One-at-a-time
  sweeps, reported as the swing in a metric.
- bootstrap_ci       : resample the real cohort many times and put a confidence
  interval on the recovered shift and the retention gap.
"""
from __future__ import annotations
import numpy as np

from .learners import sample_population
from .harness import run_cohort
from .validation import reground_to_rate, caveat_demo
from . import scenarios as sc


def _real_ft_rate(real: dict, ft_thr: float, n: int = 5) -> float:
    return float(np.mean([run_cohort(real, 200 + k, ft_thr=ft_thr)["ft_rate"]
                          for k in range(n)]))


def parameter_recovery(ft_thr: float, shifts=(0.0, 0.3, 0.6, 0.9),
                       n_trials: int = 2) -> dict:
    """Build a cohort at a known difficulty shift, feed its one aggregate number
    back, and see what shift the loop recovers. Accurate recovery means the
    aggregate-only loop is really identifying difficulty, not fitting noise."""
    rows = []
    for sh in shifts:
        recs = []
        for t in range(n_trials):
            real = sample_population(220, seed=42 + t, shift=sh)
            rate = _real_ft_rate(real, ft_thr)
            rec = reground_to_rate(rate, ft_thr, true_shift=sh)["recovered_shift"]
            recs.append(rec)
        rows.append({"true": sh, "recovered_mean": float(np.mean(recs)),
                     "recovered_std": float(np.std(recs))})
    mae = float(np.mean([abs(r["recovered_mean"] - r["true"]) for r in rows]))
    return {"rows": rows, "mae": mae}


def sensitivity(ft_thr: float) -> dict:
    """One-at-a-time sweeps of the real-cohort assumptions, measuring the
    retention gap (the caveat) and the recovered shift. Shows which assumptions
    the conclusions actually depend on."""
    def gap_for(real):
        rate = _real_ft_rate(real, ft_thr)
        rec = reground_to_rate(rate, ft_thr)["recovered_shift"]
        cv = caveat_demo(real, rec)
        return cv["retention_gap"], rec

    sweeps = {}

    # how hard is the real cohort
    rows = []
    for shift in (0.3, 0.6, 0.9):
        g, rec = gap_for(sc.forgetting_tail(shift=shift))
        rows.append({"value": shift, "retention_gap": g, "recovered_shift": rec})
    sweeps["real_shift"] = rows

    # size of the high-forgetting tail
    rows = []
    for frac in (0.0, 0.15, 0.30):
        g, rec = gap_for(sc.forgetting_tail(tail_frac=frac))
        rows.append({"value": frac, "retention_gap": g, "recovered_shift": rec})
    sweeps["tail_fraction"] = rows

    # cohort shape family
    rows = []
    for name in ("uniform_harder", "forgetting_tail", "bimodal", "high_gaming"):
        g, rec = gap_for(sc.build(name))
        rows.append({"value": name, "retention_gap": g, "recovered_shift": rec})
    sweeps["cohort_shape"] = rows

    # span of the retention gap across everything tried -> the headline swing
    all_gaps = [r["retention_gap"] for rows in sweeps.values() for r in rows]
    return {"sweeps": sweeps,
            "retention_gap_min": float(min(all_gaps)),
            "retention_gap_max": float(max(all_gaps))}


def bootstrap_ci(ft_thr: float, builder=None, n_boot: int = 12) -> dict:
    """Resample the real cohort `n_boot` times and put a 95% interval on the
    recovered shift and the retention gap."""
    if builder is None:
        builder = sc.forgetting_tail
    shifts, gaps = [], []
    for b in range(n_boot):
        real = builder(seed=42 + b)
        rate = _real_ft_rate(real, ft_thr)
        rec = reground_to_rate(rate, ft_thr)["recovered_shift"]
        cv = caveat_demo(real, rec)
        shifts.append(rec)
        gaps.append(cv["retention_gap"])

    def ci(xs):
        a = np.array(xs)
        return {"mean": float(a.mean()),
                "lo": float(np.percentile(a, 2.5)),
                "hi": float(np.percentile(a, 97.5))}

    return {"n_boot": n_boot,
            "recovered_shift": ci(shifts),
            "retention_gap": ci(gaps)}
