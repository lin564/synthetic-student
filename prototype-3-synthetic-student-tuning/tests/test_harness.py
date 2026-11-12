"""Test suite for the Synthetic Student Tuning harness.

Run from the prototype directory:  python -m pytest -q
"""
import numbers

import numpy as np
import pytest

from synthetic_tuning import (
    sample_population, run_cohort, calibrate, FT_GRID, SCAF_GRID,
    FT_TARGET, SCAF_TARGET, PARAMS,
)
from synthetic_tuning import validation as V
from synthetic_tuning import analysis as A
from synthetic_tuning.real_data import load_aggregate, reground_from_file, AggregateError


# --- determinism -----------------------------------------------------------

def test_population_is_deterministic():
    a = sample_population(100, seed=5)
    b = sample_population(100, seed=5)
    for k in PARAMS:
        assert np.array_equal(a[k], b[k])


def test_run_cohort_is_deterministic():
    pop = sample_population(150, seed=3)
    r1 = run_cohort(pop, seed=100)
    r2 = run_cohort(pop, seed=100)
    assert r1 == r2


def test_population_has_six_grounded_parameters():
    pop = sample_population(50, seed=1)
    assert set(PARAMS) == {"prior", "learn_mult", "slip_mult", "guess_mult", "hint", "decay"}
    for k in PARAMS:
        assert len(pop[k]) == 50


# --- the two-stream privacy invariant --------------------------------------

def test_run_cohort_returns_aggregates_only():
    """No per-student array ever leaves run_cohort -- the engineering-stream rule."""
    pop = sample_population(200, seed=1)
    out = run_cohort(pop, seed=100)
    for key, value in out.items():
        assert isinstance(value, numbers.Number), f"{key} is not a scalar aggregate"
    # nothing the size of the cohort (that would be a per-student record)
    assert not any(isinstance(v, (list, tuple, np.ndarray)) for v in out.values())


# --- model sanity ----------------------------------------------------------

def test_harder_shift_lowers_mastery():
    easy = run_cohort(sample_population(200, seed=1, shift=0.0), seed=7)
    hard = run_cohort(sample_population(200, seed=1, shift=0.8), seed=7)
    assert hard["mean_mastery"] < easy["mean_mastery"]
    assert hard["opportunities_per_skill"] > easy["opportunities_per_skill"]


def test_retention_never_exceeds_mastery():
    out = run_cohort(sample_population(200, seed=2), seed=9)
    assert out["retention"] <= out["mean_mastery"] + 1e-9


# --- calibration -----------------------------------------------------------

def test_fasttrack_calibration_is_monotone():
    pop = sample_population(200, seed=1)
    curve = calibrate(pop, "ft_thr", FT_GRID)
    rates = curve["rate_mean"]
    # non-increasing (small Monte-Carlo slack allowed)
    assert all(rates[i] >= rates[i + 1] - 0.03 for i in range(len(rates) - 1))
    assert rates[0] > rates[-1]


def test_scaffold_calibration_is_monotone():
    pop = sample_population(200, seed=1)
    curve = calibrate(pop, "scaf_thr", SCAF_GRID)
    rates = curve["rate_mean"]
    assert all(rates[i] >= rates[i + 1] - 0.03 for i in range(len(rates) - 1))


# --- the validation story --------------------------------------------------

def test_within_range_passes_on_default():
    syn = sample_population(200, seed=1, shift=0.0)
    real = V.build_real_cohort()
    wr = V.within_range_test(syn, real)
    assert wr["overall_pass"]


def test_aggregate_feedback_uses_one_number_and_recovers_shift():
    syn = sample_population(200, seed=1, shift=0.0)
    real = V.build_real_cohort()
    wr = V.within_range_test(syn, real)
    af = V.aggregate_feedback(real, wr["syn_tuned"]["ft_thr"])
    assert af["n_aggregates_used"] == 1
    assert abs(af["recovered_shift"] - af["true_shift"]) <= 0.15


def test_parameter_recovery_is_accurate():
    mae = A.parameter_recovery(ft_thr=0.92, n_trials=2)["mae"]
    assert mae < 0.10, f"recovery MAE too high: {mae}"


def test_caveat_retention_gap_exceeds_mastery_gap():
    syn = sample_population(200, seed=1, shift=0.0)
    real = V.build_real_cohort()
    af = V.aggregate_feedback(real, 0.92)
    cv = V.caveat_demo(real, af["recovered_shift"])
    assert cv["retention_gap"] > cv["mastery_gap"]


# --- live-data hook guardrails ---------------------------------------------

def test_example_aggregate_loads(tmp_path):
    out = reground_from_file("examples/real_aggregate.json", ft_thr=0.92)
    assert out["source"]["cohort_size"] == 180
    assert 0 <= out["recovered_shift"] <= 1.2


def test_small_cohort_is_refused(tmp_path):
    p = tmp_path / "a.json"
    p.write_text('{"fast_track_rate": 0.05, "cohort_size": 10}')
    with pytest.raises(AggregateError):
        load_aggregate(str(p))


def test_per_student_field_is_refused(tmp_path):
    p = tmp_path / "a.json"
    p.write_text('{"fast_track_rate": 0.05, "cohort_size": 100, "student_id": "x"}')
    with pytest.raises(AggregateError):
        load_aggregate(str(p))


def test_missing_rate_is_refused(tmp_path):
    p = tmp_path / "a.json"
    p.write_text('{"cohort_size": 100}')
    with pytest.raises(AggregateError):
        load_aggregate(str(p))
