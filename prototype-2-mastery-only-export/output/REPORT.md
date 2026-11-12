# Prototype 2 — Mastery-Only Export: results

_Generated 2026-11-12 by `run.py`. No real student data used._

A side-by-side harness replays the same logged sessions through two models:

- **server** — the current design: the full raw event trail (correctness,
  response latency, hint usage and timing) is used to make adaptation decisions;
- **on-device** — the proposed design: only the per-skill **mastery vector**
  (from correctness) is used, so that is all that needs to leave the device.

## Pre-registered decision rule

Set **before** running: the on-device model must diverge from the server model
on **fewer than 5%** of scaffold and fast-track triggers.

## Result

| metric | value |
|---|---|
| logged sessions | 1400 |
| decision points replayed | 9607 |
| **every adaptation decision** that diverges | **1.00%** (≈99.0% identical) |
| **scaffold + fast-track triggers** that diverge | **8.21% ± 0.77%** |
| — fast-track triggers | 6.97% (26/373) |
| — scaffold triggers | 7.45% (70/939) |
| vs the 5% threshold | **EXCEEDS threshold (does not hold)** |

Read it two ways, both true:

- **Almost all adaptation survives.** About 99.0% of
  every adaptation decision is identical whether ACE uses the full raw trail or
  only the mastery vector. The data that must *leave* the device reproduces the
  overwhelming majority of what ACE does.
- **But the triggers carry a measurable, nameable cost.** 8.2%
  of scaffold and fast-track triggers differ — above the 5% bar — and
  that residual is not spread evenly. It traces to exactly two signals.

## Which signals the server model was using

| divergent decisions | caused by |
|---|---|
| 26 | **response latency** — a fast correct answer the server reads as a lucky guess and withholds from fast-track |
| 56 | **hint timing** — an early hint the server reads as struggle and scaffolds on |
| 14 | downstream / timing of the same two |

This is the write-up's "if it does not hold" branch working as intended: the
test **names the signals** the server model depends on. They are precisely the
fields Prototype 1's **Standard** and **Minimal** levels drop — so the two
prototypes agree, from opposite directions, on what a district gives up when it
turns response latency and hint timing off.

## What leaves the device

| design | leaves the device |
|---|---|
| current (raw trail to server) | 631.1 KB across 9607 logged events |
| proposed (mastery vector only) | 34.2 KB |

Only **5.42%** of the raw trail ever leaves — a 18× reduction —
and what leaves is a handful of mastery numbers, not the clickstream. COPPA and
FERPA care about exactly this: what leaves the student's machine, not what the
model computes locally.

## How to read the verdict

Exceeding the threshold is **not** the prototype failing — it is the prototype
doing its job. It quantifies the differentiator's dependence on the data
districts fear (8% of triggers), shows the rest is
free to move on-device (~99% of decisions), and hands
Prototype 1 the exact tradeoff language for the Standard and Minimal levels.
The real numbers depend on ACE's true signal weights, which come from the
engineering team; this harness is the instrument, run here on synthetic
sessions (which Prototype 3 can supply).

## Sources

- Bayesian Knowledge Tracing: Corbett & Anderson (1995).
- The two-stream architecture and the mastery-vector export: the project write-up.
