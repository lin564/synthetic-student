# Prototype 3 — Synthetic Student Tuning: results

_Generated 2026-11-11 by `run.py`. No real student data used._

ACE is developed and calibrated on **simulated** middle schoolers. Real
student data would be needed only for low-volume **aggregate** validation,
never for model development. This report is the output of that harness.

## Pre-registered "within range" criterion

Set **before** running (per the write-up's instruction). Synthetic-tuned ACE,
evaluated on the real cohort, must match real-tuned ACE on every aggregate
outcome to within:

| outcome | tolerance |
|---|---|
| mean_mastery | ±0.03 |
| bottom_quartile_mastery | ±0.05 |
| retention | ±0.03 |
| opportunities_per_skill | ±1 |

## Test 1 — Within range  →  **PASS**

Both engines were tuned to the same design-intent firing rates
(fast-track 15% of encounters, scaffold 35%), then
**both evaluated on the real cohort**. Only aggregate outcomes are compared.

- Synthetic-tuned thresholds: fast-track **0.92**, scaffold **0.75**
- Real-tuned thresholds: fast-track **0.70**, scaffold **0.80**

| Aggregate outcome | synthetic-tuned | real-tuned | Δ | tolerance | within range |
|---|---|---|---|---|---|
| mean_mastery | 0.741 | 0.744 | 0.003 | ±0.03 | ✅ |
| bottom_quartile_mastery | 0.622 | 0.636 | 0.014 | ±0.05 | ✅ |
| retention | 0.550 | 0.552 | 0.002 | ±0.03 | ✅ |
| opportunities_per_skill | 10.801 | 10.652 | 0.149 | ±1 | ✅ |

The engine built with **zero** student data lands within range of the engine
that would have required real pilot records.

## Test 2 — Transfer

An improvement found purely on synthetic data — a better scaffold threshold,
chosen to lift the strugglers (bottom-quartile mastery) without exceeding a
40% intervention budget — moved from **0.75** to **0.70**:

| cohort | bottom-quartile mastery (tuned) | (improved) | gain |
|---|---|---|---|
| synthetic | 0.877 | 0.890 | +0.013 |
| real | 0.630 | 0.641 | +0.011 |

The same change helps the real cohort — **no individual record left the
district** to find it. Transfers: **True**.

## Test 3 — Aggregate-only feedback

The only thing the engineering stream consumed from the real world was **one
number**: the real cohort's fast-track firing rate = **0.046**.
Feeding it back (nudging the synthetic population's difficulty until its own
fast-track rate matched) recovered a difficulty shift of
**0.55**, against a true shift of **0.60** — the
synthetic prior re-grounds itself from a single aggregate, not from records.

## Caveat (state this in class)

A synthetic population tuned to match real aggregates can still be wrong about
individuals in ways that only show up in real classrooms. Here the stand-in
real cohort carries a high-forgetting tail (absenteeism / summer slide) that
the synthetic model's priors cannot express. After matching the aggregate:

- mean-mastery gap (the matched aggregate): **0.020**
- retention gap (the blind spot): **0.041**

The retention gap is the larger one, and it is invisible to the aggregate the
feedback loop used. That is exactly why the two streams validate each other
rather than one replacing the other.

## What this answers

The obvious objection to the two-stream model — *if QuestSim never gets
student data, how does the product get better?* — has a concrete answer: the
brain is built and tuned in simulation; real students only ever confirm, in
aggregate, that it works.

## Sources (grounding for the agent parameters)

- Corbett & Anderson (1995), *Knowledge tracing* — BKT: prior, learn, slip, guess, the 0.95 mastery threshold.
- Newell & Rosenbloom (1981), *Mechanisms of skill acquisition and the power law of practice* — the learning-rate parameter.
- Aleven, McLaren, Roll & Koedinger (2006), *help-seeking and help-avoidance* — the hint-seeking parameter.
- Ebbinghaus (1885) / Pavlik & Anderson (2005), *memory decay and spacing* — the forgetting-rate parameter.

See `output/aggregates.json` and `output/calibration.csv` for the raw numbers,
and `figures/` for the plots.
