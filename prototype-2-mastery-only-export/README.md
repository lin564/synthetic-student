# Prototype 2 — Mastery-Only Export

> From **"Wicked Problem Prototypes: Personalization Without the Data Districts
> Can't Defend"** (Linda Bernard, Nov 2026).

A technical proof that ACE can adapt **on the device** and export only a
per-skill **mastery vector** to the district's Drive folder, so the raw
clickstream never leaves the browser.

## What it is

One level of Pythagoras Quest, instrumented two ways, and a side-by-side
harness that replays the **same logged sessions** through both:

- **server** (current design) — the full raw event trail (correctness,
  response latency, hint usage and timing) goes to a server-side learner model
  that makes the adaptation decisions;
- **on-device** (proposed design) — the learner model runs client-side; the raw
  trail lives in browser memory for the session; at session end the only thing
  that leaves is the per-skill mastery vector.

The harness records every adaptation decision each model makes and reports the
share that diverge.

## The test (pre-registered)

Set **before** running: the on-device model must diverge from the server model
on **fewer than 5%** of scaffold and fast-track triggers. (Threshold lives in
`mastery_export/skills.py` as `DIVERGENCE_THRESHOLD`.)

## Result (latest run — see `output/REPORT.md`)

- **~99% of every adaptation decision is identical** whether ACE uses the full
  raw trail or only the mastery vector. Almost all adaptation survives moving
  on-device.
- **~8% of scaffold and fast-track triggers diverge** — above the 5% bar — and
  the residual traces to exactly two signals: **response latency** (catching a
  fast lucky guess before fast-tracking) and **hint timing** (scaffolding a
  student who reaches for a hint early).
- **~18× less data leaves the device** — only a handful of mastery numbers, not
  the clickstream.

Exceeding the threshold is the prototype **doing its job**, not failing: the
write-up says that if the bar does not hold, "the result tells you which signals
the server model was using that the on-device model cannot keep, which feeds
Prototype 1's tradeoff language." Those two signals are precisely the fields
Prototype 1's **Standard** and **Minimal** levels drop — so the two prototypes
agree, from opposite directions, on what a district gives up.

## Run it

```bash
cd prototype-2-mastery-only-export
pip install -r requirements.txt
python run.py
```

Deterministic (~5s). Writes `figures/` (four PNGs), `output/REPORT.md`,
`output/report.html`, and `output/results.json`.

## Layout

```
.
├── run.py                   # replay + divergence + footprint + figures + report
├── mastery_export/
│   ├── skills.py            # skill sequence, thresholds, pre-registered criterion
│   ├── sessions.py          # synthetic logged sessions (raw event trails) + footprint
│   ├── models.py            # on-device (mastery only) vs server (adds latency + hint timing)
│   ├── harness.py           # replay both, measure divergence, attribute, aggregate
│   └── plotting.py          # figures (matplotlib, lazily imported)
├── figures/                 # generated PNGs (committed)
└── output/                  # generated REPORT.md, report.html, results.json
```

## Honest caveats

The logged sessions are **synthetic** — in the integrated story they come from
Prototype 3's synthetic learners, so no real clickstream is needed to run the
comparison. The exact divergence depends on ACE's true signal weights, which
come from the engineering team; this harness is the instrument. The server and
on-device decision rules here are illustrative stand-ins for ACE's real logic.
