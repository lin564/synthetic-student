"""Live-data hook: feed the aggregate-only feedback loop a real cohort's number.

The whole privacy argument rests on the engineering stream consuming aggregates
only. This adapter makes that literal: it reads ONE number -- a cohort's
fast-track firing rate -- from a CSV or JSON a district can hand over, enforces
the project's minimum-cohort guardrail, and refuses anything that looks like a
per-student record. It then re-grounds the synthetic population to match, with
no individual data involved.

Drop-in formats (see examples/):

  JSON   {"label": "...", "cohort_size": 180, "fast_track_rate": 0.047}
  CSV    two columns, metric,value, with rows cohort_size and fast_track_rate

Usage:
    from synthetic_tuning.real_data import reground_from_file
    result = reground_from_file("examples/real_aggregate.json", ft_thr=0.92)
"""
from __future__ import annotations
import csv
import json
import os

from .validation import reground_to_rate

# The minimum cohort size below which an aggregate is not accepted, because a
# small class makes re-identification trivial (the write-up's first guardrail).
MIN_COHORT = 30

# Fields that would make this an individual record, not an aggregate. Their
# presence means the file is the wrong kind of data and is refused.
FORBIDDEN_FIELDS = {"student", "student_id", "students", "name", "names",
                    "email", "events", "clickstream", "roster", "records"}


class AggregateError(ValueError):
    """The supplied file is not an acceptable district aggregate."""


def load_aggregate(path: str) -> dict:
    """Read and validate a district aggregate from a .json or .csv file.

    Returns {label, cohort_size, fast_track_rate}. Raises AggregateError if the
    file is missing the required number, is below the minimum cohort size, or
    carries anything that looks like an individual record.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise AggregateError("JSON aggregate must be a single object of fields.")
    elif ext == ".csv":
        data = {}
        with open(path, newline="") as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[0].strip().lower() not in ("metric", ""):
                    data[row[0].strip()] = row[1].strip()
    else:
        raise AggregateError(f"Unsupported file type '{ext}'. Use .json or .csv.")

    present = {k.lower() for k in data}
    leaked = present & FORBIDDEN_FIELDS
    if leaked:
        raise AggregateError(
            f"Refusing this file: it contains per-student field(s) {sorted(leaked)}. "
            "The engineering stream accepts aggregates only.")

    if "fast_track_rate" not in data:
        raise AggregateError("Aggregate must include 'fast_track_rate' (one number).")
    try:
        rate = float(data["fast_track_rate"])
    except (TypeError, ValueError):
        raise AggregateError("'fast_track_rate' must be a number between 0 and 1.")
    if not 0.0 <= rate <= 1.0:
        raise AggregateError("'fast_track_rate' must be between 0 and 1.")

    size = int(float(data.get("cohort_size", 0) or 0))
    if size < MIN_COHORT:
        raise AggregateError(
            f"Cohort size {size} is below the minimum of {MIN_COHORT}. A small "
            "cohort makes re-identification trivial, so the aggregate is not accepted.")

    return {"label": str(data.get("label", "unlabeled cohort")),
            "cohort_size": size, "fast_track_rate": rate}


def reground_from_file(path: str, ft_thr: float, true_shift: float = None) -> dict:
    """Load a district aggregate and re-ground the synthetic population to it."""
    agg = load_aggregate(path)
    kwargs = {} if true_shift is None else {"true_shift": true_shift}
    out = reground_to_rate(agg["fast_track_rate"], ft_thr, **kwargs)
    out["source"] = agg
    return out
