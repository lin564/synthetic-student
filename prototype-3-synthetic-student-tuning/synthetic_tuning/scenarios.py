"""A library of stand-in "real cohort" scenarios.

The core demonstration uses one stand-in real cohort (harder than the synthetic
prior, plus a high-forgetting tail). Reality comes in more shapes than that, and
a method that only works against one of them is not worth much. Each scenario
here builds a different real cohort; `validation.run_scenarios` then runs the
whole test suite against each and reports where synthetic tuning holds and where
it strains.

Every builder returns a cohort in the same form as `sample_population`, so the
rest of the harness is unchanged. Some scenarios are inside the synthetic family
(a parameter shift the feedback loop can recover); others are deliberately
mis-specified (a shape the unimodal synthetic priors cannot express), which is
where the caveat bites.
"""
from __future__ import annotations
import numpy as np

from .learners import sample_population


def uniform_harder(n: int = 220, seed: int = 42, shift: float = 0.6) -> dict:
    """The synthetic family, just harder. Inside the family -> the feedback loop
    should recover it and tuning should hold on every outcome."""
    return sample_population(n, seed=seed, shift=shift)


def forgetting_tail(n: int = 220, seed: int = 42, shift: float = 0.6,
                    tail_frac: float = 0.15, tail_decay: float = 0.55) -> dict:
    """Harder, plus a high-forgetting tail (absenteeism / summer slide) the
    synthetic priors cannot express. Immediate outcomes match; retention is the
    blind spot. This is the default stand-in used elsewhere in the project."""
    pop = sample_population(n, seed=seed, shift=shift)
    r = np.random.default_rng(seed + 1)
    tail = r.random(n) < tail_frac
    pop["decay"] = pop["decay"].copy()
    pop["slip_mult"] = pop["slip_mult"].copy()
    pop["decay"][tail] = np.clip(r.normal(tail_decay, 0.05, tail.sum()), 0.3, 0.75)
    pop["slip_mult"][tail] = np.clip(pop["slip_mult"][tail] + 0.4, 0.4, 2.5)
    return pop


def bimodal(n: int = 220, seed: int = 42, advanced_frac: float = 0.4) -> dict:
    """Two subpopulations — an advanced group and a struggling group — rather
    than one hump. A unimodal synthetic prior can match the average while missing
    both tails, so this strains the within-range test more than a uniform shift."""
    r = np.random.default_rng(seed)
    adv = sample_population(n, seed=seed, shift=-0.2)
    strg = sample_population(n, seed=seed + 5, shift=0.9)
    is_adv = r.random(n) < advanced_frac
    out = {}
    for k in adv:
        out[k] = np.where(is_adv, adv[k], strg[k])
    return out


def high_gaming(n: int = 220, seed: int = 42, shift: float = 0.5) -> dict:
    """A cohort that games the system — elevated guessing — on top of being
    harder. Tests whether guessing inflates the fast-track firing the loop sees."""
    pop = sample_population(n, seed=seed, shift=shift)
    r = np.random.default_rng(seed + 2)
    pop["guess_mult"] = np.clip(pop["guess_mult"] + r.normal(0.4, 0.15, n), 0.4, 1.9)
    return pop


def slow_acquisition(n: int = 220, seed: int = 42) -> dict:
    """A cohort that simply needs more support — low learning rate and higher
    slip, but no exotic shape. Inside the family in spirit; a stress test of the
    scaffold side rather than fast-track."""
    pop = sample_population(n, seed=seed, shift=0.0)
    r = np.random.default_rng(seed + 3)
    pop["learn_mult"] = np.clip(pop["learn_mult"] * r.normal(0.7, 0.1, n), 0.25, 2.2)
    pop["slip_mult"] = np.clip(pop["slip_mult"] + 0.35, 0.4, 2.5)
    return pop


# name -> (builder, one-line description, is it inside the synthetic family?)
SCENARIOS = {
    "uniform_harder": (uniform_harder,
                       "The synthetic family, just harder.", True),
    "forgetting_tail": (forgetting_tail,
                        "Harder + a high-forgetting tail (absenteeism).", False),
    "bimodal": (bimodal,
                "Advanced + struggling subpopulations, not one hump.", False),
    "high_gaming": (high_gaming,
                    "Harder + elevated guessing / gaming.", False),
    "slow_acquisition": (slow_acquisition,
                         "Needs more support: low learning rate, high slip.", True),
}


def build(name: str, **kwargs) -> dict:
    return SCENARIOS[name][0](**kwargs)
