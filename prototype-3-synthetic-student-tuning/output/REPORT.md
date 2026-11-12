# Prototype 3 — Synthetic Student Tuning: results

_Generated 2026-11-12 by `run.py`. No real student data used._

ACE is developed and calibrated on **simulated** middle schoolers. Real student
data would be needed only for low-volume **aggregate** validation, never for
model development. Each learner is an agent with **six** literature-grounded
parameters (prior knowledge, learning rate, slip, guessing, hint-seeking,
forgetting), and the skill sequence is cumulative — a mastered prerequisite
raises the effective prior on the next skill.

## Pre-registered "within range" criterion

Set **before** running. Synthetic-tuned ACE, evaluated on the real cohort, must
match real-tuned ACE on every aggregate outcome to within:

| outcome | tolerance |
|---|---|
| mean_mastery | ±0.03 |
| bottom_quartile_mastery | ±0.05 |
| retention | ±0.03 |
| opportunities_per_skill | ±1 |

## Test 1 — Within range  →  **PASS**

Both engines tuned to the same design-intent firing rates, both evaluated on the
real cohort over 12 resamples (the ± is the resample band).

- Synthetic-tuned: fast-track **0.92**, scaffold **0.75**
- Real-tuned: fast-track **0.70**, scaffold **0.80**

| Aggregate outcome | synthetic-tuned | real-tuned | Δ (± resample) | tolerance | within range |
|---|---|---|---|---|---|
| mean_mastery | 0.743 | 0.731 | 0.012 ± 0.007 | ±0.03 | ✅ |
| bottom_quartile_mastery | 0.630 | 0.620 | 0.010 ± 0.016 | ±0.05 | ✅ |
| retention | 0.557 | 0.548 | 0.009 ± 0.006 | ±0.03 | ✅ |
| opportunities_per_skill | 10.832 | 10.634 | 0.198 ± 0.095 | ±1 | ✅ |

## Test 2 — Transfer

A scaffold improvement found purely on synthetic data moved
**0.75** → **0.70**:

| cohort | bottom-quartile (tuned) | (improved) | gain |
|---|---|---|---|
| synthetic | 0.882 | 0.890 | +0.008 |
| real | 0.644 | 0.663 | +0.019 |

No individual record left the district to find it. Transfers: **True**.

## Test 3 — Aggregate-only feedback

One number — the real cohort's fast-track firing rate = **0.051** —
re-grounds the synthetic population's difficulty to a shift of
**0.60** against a true **0.60** (match error
0.003). The synthetic prior re-grounds itself from a single aggregate.

## Rigor 1 — Parameter recovery

Does the aggregate-only loop really identify a cohort's difficulty, or just fit
noise? Recovering a range of **known** shifts from one number each:

| true shift | recovered |
|---|---|
| 0.0 | 0.00 ± 0.00 |
| 0.3 | 0.28 ± 0.06 |
| 0.6 | 0.58 ± 0.05 |
| 0.9 | 0.87 ± 0.02 |

**Mean absolute error = 0.017.** The one-number loop recovers true
difficulty across the range — it is measuring something real.

## Rigor 2 — Scenario sweep

The core demo uses one stand-in real cohort. Reality comes in more shapes, so
the whole test is re-run against five:

| scenario | kind | within-range | recovered shift | retention gap |
|---|---|---|---|---|
| uniform_harder | in family | ✅ PASS | 0.65 | 0.028 |
| forgetting_tail | mis-specified | ✅ PASS | 0.60 | 0.014 |
| bimodal | mis-specified | ✅ PASS | 0.30 | 0.076 |
| high_gaming | mis-specified | ✅ PASS | 0.80 | 0.108 |
| slow_acquisition | in family | ✅ PASS | 0.25 | 0.027 |

**Synthetic tuning holds on the immediate aggregate outcomes for every shape.**
The individual-level blind spot (retention gap) varies with the shape and is
largest for **high_gaming** (0.108) — a mis-specified cohort the
unimodal synthetic priors cannot express. This is the caveat, quantified across
scenarios: matching the aggregate is not being right about individuals.

## Rigor 3 — Sensitivity

One-at-a-time sweeps of the (unknown) real-cohort assumptions. The within-range
result is robust; the quantity that moves is the retention gap, which ranges
**0.000–0.108** across everything tried. The
conclusions depend on the forgetting-tail assumption, not on cohort hardness —
which is exactly the thing a real pilot would pin down.

## Rigor 4 — Bootstrap confidence intervals

Over 12 real-cohort resamples (95% intervals):

- recovered shift: **0.57**  [0.50, 0.64]
- retention gap: **0.032**  [0.004, 0.059]

## Caveat (state this in class)

A synthetic population tuned to match real aggregates can still be wrong about
individuals in ways that only show up in real classrooms. The scenario sweep
makes this concrete: tuning holds on immediate outcomes everywhere, but the
retention gap — invisible to the aggregate the feedback loop used — is real and
largest for the mis-specified cohorts. That is why the two streams validate each
other rather than one replacing the other.

## Live-data hook

The aggregate-only feedback loop can read a real cohort's one number from a
district file (`synthetic_tuning/real_data.py`, with worked examples in
`examples/`). It enforces a minimum cohort size and refuses any file carrying a
per-student field, so only an aggregate is ever consumed. Run:
`python run.py --real-aggregate examples/real_aggregate.json`.

## Sources

- Bayesian Knowledge Tracing: Corbett & Anderson (1995).
- Power law of practice: Newell & Rosenbloom (1981).
- Gaming / guessing: Baker, Corbett, Roll & Koedinger (2008).
- Help-seeking: Aleven, McLaren, Roll & Koedinger (2006).
- Memory decay: Ebbinghaus (1885); Pavlik & Anderson (2005).
