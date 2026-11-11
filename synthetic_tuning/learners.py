"""Synthetic learner agents.

The real work of Prototype 3, per the write-up: "a population of synthetic
learners as agents with parameterized prior knowledge, error tendencies,
hint-seeking behavior, and mastery decay rates."

Each agent carries exactly five parameters, each grounded in published
learning-science literature rather than invented:

    prior       P(L0), initial probability a skill is already known
                -- Bayesian Knowledge Tracing (Corbett & Anderson, 1995)
    learn_mult  scales the per-skill acquisition rate P(T); the engine of the
                power law of practice (Newell & Rosenbloom, 1981)
    slip_mult   scales the per-skill slip P(S) -- a learner's "error tendency"
                even on mastered material (Corbett & Anderson, 1995)
    hint        hint-seeking propensity; the help-seeking / help-avoidance
                dimension (Aleven, McLaren, Roll & Koedinger, 2006)
    decay       per-skill forgetting rate used in the retention probe;
                the Ebbinghaus forgetting curve, as formalised in ACT-R and
                the spacing/decay work of Pavlik & Anderson (2005)

`sample_population` draws a cohort from Normal priors truncated to sane
ranges. The `shift` argument makes a population uniformly harder (lower
learning, more slips, more forgetting, more hint-leaning): shift=0 is the
optimistic synthetic prior QuestSim starts with; a positive shift stands in
for a tougher real-world cohort. No real child is ever involved.
"""
from __future__ import annotations
import numpy as np

# Parameter order used for arrays / plots.
PARAMS = ("prior", "learn_mult", "slip_mult", "hint", "decay")


def sample_population(n: int, seed: int, shift: float = 0.0) -> dict:
    """Return a cohort of `n` synthetic learners as a dict of parameter arrays.

    `shift` (>= 0) moves the whole population toward "harder": used to build a
    stand-in real cohort that the optimistic synthetic prior has not yet seen.
    """
    r = np.random.default_rng(seed)
    return {
        "prior":      np.clip(r.normal(0.20 - 0.08 * shift, 0.10, n), 0.02, 0.70),
        "learn_mult": np.clip(r.normal(1.00 - shift,        0.30, n), 0.25, 2.20),
        "slip_mult":  np.clip(r.normal(1.00 + shift,        0.30, n), 0.40, 2.50),
        "hint":       np.clip(r.normal(0.35 + 0.10 * shift, 0.18, n), 0.00, 0.95),
        "decay":      np.clip(r.normal(0.20 + 0.10 * shift, 0.10, n), 0.02, 0.60),
    }


def population_size(pop: dict) -> int:
    return len(pop["prior"])
