"""ACE, the adaptive engine, running against one synthetic learner.

ACE tracks per-skill mastery with a standard Bayesian Knowledge Tracing
update and makes two interventions, each governed by one calibratable
threshold:

  fast-track  -- at the FT_CHECK-th item, if the mastery estimate is already
                 past `ft_thr` AND the student is not leaning on hints
                 (hint rate <= `ft_hint_cap`), ACE advances them past the
                 remaining practice for that skill. Captures quick, genuine
                 mastery; hint-dependent "mastery" is deliberately excluded.

  scaffold    -- once past a short warm-up, if the rolling struggle signal
                 (an EWMA of recent errors) is at or above `scaf_thr`, ACE
                 drops in a scaffold, which raises the student's effective
                 learning rate for the rest of that skill.

The two thresholds are exactly what Prototype 3 calibrates. Everything here
runs per student; only aggregates ever leave `harness.run_cohort`.

Hint-seeking (a learner parameter) both helps the item (a hint raises the
effective guess and lowers the effective slip) and gates fast-track, so a
hint-heavy student is not mistaken for a master. Mastery decay feeds a
delayed retention probe at the end of each skill.
"""
from __future__ import annotations
import numpy as np

from .skills import SKILLS, MAX_OPP, MASTERY, FT_CHECK, SCAF_WARMUP, EWMA_ALPHA
from .learners import PREREQ_WEIGHT


def run_student(pop: dict, i: int, rng: np.random.Generator,
                ft_thr: float = 0.90, scaf_thr: float = 0.55,
                ft_hint_cap: float = 0.34) -> dict:
    """Run learner `i` through the whole skill sequence. Returns that
    student's private record (mastery vector, retention vector, trigger
    counts, opportunities used). The harness keeps only aggregates of these.
    """
    S = len(SKILLS)
    mastery = np.zeros(S)
    retention = np.zeros(S)
    ft_fired = 0
    scaf_fired = 0
    opportunities = 0

    prior = pop["prior"][i]
    learn_mult = pop["learn_mult"][i]
    slip_mult = pop["slip_mult"][i]
    guess_mult = pop["guess_mult"][i] if "guess_mult" in pop else 1.0
    hint_prop = pop["hint"][i]
    decay = pop["decay"][i]

    prev_mastery = None  # the previous skill's final mastery, for the prereq boost

    for s, (_name, p) in enumerate(SKILLS):
        guess = min(0.45, p["guess"] * guess_mult)
        slip = min(0.45, p["slip"] * slip_mult)
        learn = min(0.60, p["learn"] * learn_mult)

        # Cumulative knowledge: a mastered prerequisite raises the effective
        # prior on this skill; a shaky one lowers it.
        if prev_mastery is None:
            eff_prior = prior
        else:
            eff_prior = min(0.95, max(0.02, prior + PREREQ_WEIGHT * (prev_mastery - 0.5)))

        known = rng.random() < eff_prior    # true latent knowledge state
        pL = eff_prior                       # ACE's BKT mastery estimate
        struggle = 0.0                       # EWMA of recent errors
        hints = 0
        last_err = 0
        scaffolded = False

        for opp in range(1, MAX_OPP + 1):
            opportunities += 1

            # Hint-seeking: more likely right after an error.
            p_hint = min(0.95, hint_prop * (1.6 if last_err else 1.0))
            used_hint = rng.random() < p_hint
            hints += int(used_hint)
            eff_guess = min(0.90, guess + 0.35) if used_hint else guess
            eff_slip = max(0.02, slip - 0.04) if used_hint else slip

            # Generate the response from the true latent state.
            if known:
                correct = rng.random() > eff_slip
            else:
                correct = rng.random() < eff_guess
            last_err = 0 if correct else 1
            struggle = EWMA_ALPHA * last_err + (1 - EWMA_ALPHA) * struggle

            # Bayesian Knowledge Tracing update of the mastery estimate.
            p_correct = pL * (1 - eff_slip) + (1 - pL) * eff_guess
            if correct:
                num = pL * (1 - eff_slip)
                den = p_correct
            else:
                num = pL * eff_slip
                den = 1 - p_correct
            pL = (num / den) if den > 0 else pL
            pL = pL + (1 - pL) * learn            # acquisition transition

            if not known and rng.random() < learn:
                known = True

            hint_rate = hints / opp

            # fast-track: quick mastery that is not hint-propped.
            if opp == FT_CHECK and pL >= ft_thr and hint_rate <= ft_hint_cap \
                    and not scaffolded:
                ft_fired += 1
                break

            # scaffold: sustained struggle.
            if opp >= SCAF_WARMUP and not scaffolded and struggle >= scaf_thr:
                scaffolded = True
                scaf_fired += 1
                learn = min(0.60, learn * 1.7)   # the scaffold helps

            if pL >= MASTERY and opp >= FT_CHECK:
                break

        mastery[s] = pL
        # Delayed retention probe: mastery decays between acquisition and recall.
        retention[s] = pL * float(np.exp(-decay))
        prev_mastery = pL  # carry forward for the next skill's prerequisite boost

    return {
        "mastery": mastery,
        "retention": retention,
        "ft_fired": ft_fired,
        "scaf_fired": scaf_fired,
        "opportunities": opportunities,
    }
