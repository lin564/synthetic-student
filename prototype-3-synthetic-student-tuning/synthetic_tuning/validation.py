"""The test Prototype 3 specifies, plus its transfer step, the aggregate-only
feedback loop, and the caveat demonstration.

From the write-up:

  "Compare ACE tuned on synthetic learners against ACE tuned on whatever real
   pilot data exists, and check whether the synthetic-tuned version performs
   within range on the real cohort, measured only through aggregate outcomes.
   Add one step: take an improvement found on synthetic data (a better
   scaffold threshold, say) and show it transfers to the real cohort without
   any individual record leaving the district. Set the 'within range'
   criterion before running."

Because no real pilot data is available here (an open question in the
write-up), a stand-in "real" cohort is simulated. To keep the test honest it
is deliberately MIS-SPECIFIED relative to the synthetic family: it is the
synthetic distribution made harder, PLUS a high-forgetting tail (absenteeism
/ summer slide) that the synthetic model's unimodal priors cannot express.
That tail is what makes the closing caveat real: matching the aggregates does
not make the synthetic model right about every individual.
"""
from __future__ import annotations
import numpy as np

from .learners import sample_population
from .harness import run_cohort, calibrate, pick_threshold
from .skills import (FT_TARGET, SCAF_TARGET, FT_GRID, SCAF_GRID)

# --- Pre-registered "within range" criterion (set BEFORE running the test) ---
# Synthetic-tuned ACE, evaluated on the real cohort, must match real-tuned ACE
# on every aggregate outcome to within these tolerances.
WITHIN_RANGE = {
    "mean_mastery": 0.03,
    "bottom_quartile_mastery": 0.05,
    "retention": 0.03,
    "opportunities_per_skill": 1.0,
}
OUTCOME_KEYS = list(WITHIN_RANGE.keys())

# Intervention budget for the transfer step: the "better scaffold threshold"
# must help strugglers WITHOUT scaffolding more than this share of encounters.
SCAF_BUDGET = 0.40

# The true difficulty shift of the stand-in real cohort (what the aggregate
# feedback loop should be able to recover from a single number).
REAL_SHIFT = 0.6


def build_real_cohort(n: int = 220, seed: int = 42, shift: float = REAL_SHIFT,
                      tail_frac: float = 0.15, tail_decay: float = 0.55) -> dict:
    """A stand-in real pilot cohort: the synthetic family made harder, plus a
    high-forgetting tail the synthetic priors do not model (model
    mis-specification, on purpose)."""
    pop = sample_population(n, seed=seed, shift=shift)
    r = np.random.default_rng(seed + 1)
    tail = r.random(n) < tail_frac
    pop["decay"] = pop["decay"].copy()
    pop["slip_mult"] = pop["slip_mult"].copy()
    pop["decay"][tail] = np.clip(r.normal(tail_decay, 0.05, tail.sum()), 0.3, 0.75)
    pop["slip_mult"][tail] = np.clip(pop["slip_mult"][tail] + 0.4, 0.4, 2.5)
    return pop


def tune(pop: dict, base_seed: int) -> dict:
    """Calibrate both triggers on `pop` to hit the design-intent firing rates."""
    ft_curve = calibrate(pop, "ft_thr", FT_GRID, base_seed=base_seed)
    sc_curve = calibrate(pop, "scaf_thr", SCAF_GRID, base_seed=base_seed)
    return {
        "ft_thr": pick_threshold(ft_curve, FT_TARGET),
        "scaf_thr": pick_threshold(sc_curve, SCAF_TARGET),
        "ft_curve": ft_curve,
        "scaf_curve": sc_curve,
    }


def _avg_eval(real: dict, thr: dict, seeds) -> tuple:
    """Evaluate one tuned engine on the real cohort over several resamples;
    return (mean per outcome, std per outcome)."""
    runs = [run_cohort(real, s, ft_thr=thr["ft_thr"], scaf_thr=thr["scaf_thr"])
            for s in seeds]
    mean = {k: float(np.mean([r[k] for r in runs])) for k in OUTCOME_KEYS}
    std = {k: float(np.std([r[k] for r in runs])) for k in OUTCOME_KEYS}
    return mean, std


def within_range_test(syn: dict, real: dict, eval_seed: int = 999,
                      n_eval: int = 12) -> dict:
    """Tune on synthetic and on real; evaluate both on the real cohort over
    `n_eval` resamples; check the synthetic-tuned engine is within range on
    aggregate outcomes. The deltas carry a resample std (a confidence band)."""
    syn_tuned = tune(syn, base_seed=100)
    real_tuned = tune(real, base_seed=200)

    seeds = range(eval_seed, eval_seed + n_eval)
    eval_syn, std_syn = _avg_eval(real, syn_tuned, seeds)
    eval_real, std_real = _avg_eval(real, real_tuned, seeds)

    deltas, delta_std, passed = {}, {}, {}
    for k in OUTCOME_KEYS:
        deltas[k] = abs(eval_syn[k] - eval_real[k])
        delta_std[k] = max(std_syn[k], std_real[k])
        passed[k] = deltas[k] <= WITHIN_RANGE[k]

    return {
        "syn_tuned": {"ft_thr": syn_tuned["ft_thr"], "scaf_thr": syn_tuned["scaf_thr"]},
        "real_tuned": {"ft_thr": real_tuned["ft_thr"], "scaf_thr": real_tuned["scaf_thr"]},
        "eval_syn": eval_syn,
        "eval_real": eval_real,
        "deltas": deltas,
        "delta_std": delta_std,
        "passed": passed,
        "overall_pass": all(passed.values()),
        "n_eval": n_eval,
        "curves": {"syn": syn_tuned, "real": real_tuned},
    }


def transfer_test(syn: dict, real: dict, tuned_scaf: float,
                  eval_seed: int = 999) -> dict:
    """Find a better scaffold threshold on synthetic data (maximise
    bottom-quartile mastery within the intervention budget), then show the
    SAME threshold improves the real cohort -- no individual record leaves."""
    curve = calibrate(syn, "scaf_thr", SCAF_GRID, base_seed=100)
    feasible = [(v, bq, rt) for v, bq, rt in zip(
        curve["grid"], curve["bottom_quartile_mastery"], curve["rate_mean"])
        if rt <= SCAF_BUDGET]
    improved_scaf = max(feasible, key=lambda t: t[1])[0]

    syn_before = run_cohort(syn, 100, scaf_thr=tuned_scaf)["bottom_quartile_mastery"]
    syn_after = run_cohort(syn, 100, scaf_thr=improved_scaf)["bottom_quartile_mastery"]
    real_before = run_cohort(real, eval_seed, scaf_thr=tuned_scaf)["bottom_quartile_mastery"]
    real_after = run_cohort(real, eval_seed, scaf_thr=improved_scaf)["bottom_quartile_mastery"]

    return {
        "tuned_scaf": tuned_scaf,
        "improved_scaf": improved_scaf,
        "syn_before": syn_before, "syn_after": syn_after,
        "real_before": real_before, "real_after": real_after,
        "syn_gain": syn_after - syn_before,
        "real_gain": real_after - real_before,
        "transfers": (syn_after > syn_before) and (real_after > real_before),
    }


def reground_to_rate(real_ft_rate: float, ft_thr: float, base_seed: int = 300,
                     max_shift: float = 1.2, step: float = 0.05,
                     tol: float = 0.01, true_shift: float = REAL_SHIFT) -> dict:
    """Given ONE aggregate number -- a cohort's fast-track firing rate -- find
    the synthetic difficulty shift whose own fast-track rate best matches it.
    This is the whole feedback loop, and it never reads an individual record.
    The number can come from a simulated real cohort or a real pilot (see
    real_data). The search scans the whole range and takes the closest match,
    so it is unbiased rather than stopping at the first point within tolerance."""
    trace = []
    best_shift, best_diff = 0.0, float("inf")
    shift = 0.0
    while shift <= max_shift + 1e-9:
        syn = sample_population(200, seed=1, shift=shift)
        syn_ft = float(np.mean([run_cohort(syn, base_seed + k, ft_thr=ft_thr)["ft_rate"]
                                for k in range(3)]))
        trace.append((round(shift, 3), syn_ft))
        diff = abs(syn_ft - real_ft_rate)
        if diff < best_diff:
            best_diff, best_shift = diff, shift
        shift += step

    return {
        "real_ft_rate": real_ft_rate,
        "recovered_shift": round(best_shift, 3),
        "match_error": best_diff,
        "within_tol": best_diff <= tol,
        "true_shift": true_shift,
        "trace": trace,
        "n_aggregates_used": 1,
    }


def aggregate_feedback(real: dict, ft_thr: float, base_seed: int = 300,
                       max_shift: float = 1.2, step: float = 0.05,
                       tol: float = 0.01) -> dict:
    """Measure the real cohort's fast-track firing rate (one number) and feed it
    back through `reground_to_rate` to re-ground the synthetic population."""
    real_ft = float(np.mean([run_cohort(real, 200 + k, ft_thr=ft_thr)["ft_rate"]
                             for k in range(5)]))
    return reground_to_rate(real_ft, ft_thr, base_seed=base_seed,
                            max_shift=max_shift, step=step, tol=tol)


def caveat_demo(real: dict, recovered_shift: float, base_seed: int = 400) -> dict:
    """After matching the aggregate, the synthetic cohort still mis-predicts
    retention, because the real cohort's high-forgetting tail is outside the
    synthetic family. Aggregate match != right about individuals."""
    nudged = sample_population(220, seed=7, shift=recovered_shift)
    syn_agg = run_cohort(nudged, base_seed)
    real_agg = run_cohort(real, base_seed + 1)
    return {
        "recovered_shift": recovered_shift,
        "syn_mean_mastery": syn_agg["mean_mastery"],
        "real_mean_mastery": real_agg["mean_mastery"],
        "mastery_gap": abs(syn_agg["mean_mastery"] - real_agg["mean_mastery"]),
        "syn_retention": syn_agg["retention"],
        "real_retention": real_agg["retention"],
        "retention_gap": abs(syn_agg["retention"] - real_agg["retention"]),
    }


def run_scenarios(syn: dict, names=None) -> dict:
    """Run the whole test suite against each stand-in real-cohort scenario and
    summarise where synthetic tuning holds and where it strains."""
    from . import scenarios as sc
    if names is None:
        names = list(sc.SCENARIOS.keys())

    out = {}
    for name in names:
        builder, desc, in_family = sc.SCENARIOS[name]
        real = builder()
        wr = within_range_test(syn, real)
        af = aggregate_feedback(real, wr["syn_tuned"]["ft_thr"])
        cv = caveat_demo(real, af["recovered_shift"])
        out[name] = {
            "description": desc,
            "in_family": in_family,
            "overall_pass": wr["overall_pass"],
            "passed": wr["passed"],
            "deltas": wr["deltas"],
            "recovered_shift": af["recovered_shift"],
            "true_shift": af["true_shift"],
            "retention_gap": cv["retention_gap"],
            "mastery_gap": cv["mastery_gap"],
        }
    return out
