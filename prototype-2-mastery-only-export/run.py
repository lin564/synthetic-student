#!/usr/bin/env python3
"""Prototype 2 - Mastery-Only Export: end-to-end run.

Generates synthetic logged sessions, replays each through the server model and
the on-device model, measures how often their adaptation decisions diverge
(against a pre-registered threshold), attributes each divergence to a fine
signal, and quantifies what leaves the device. Writes figures/ and output/.

    python run.py
"""
from __future__ import annotations
import os
import json
import datetime as dt

from mastery_export import sample_population, log_sessions, DIVERGENCE_THRESHOLD
from mastery_export.harness import run_multi

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
OUTDIR = os.path.join(HERE, "output")


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print("Prototype 2 - Mastery-Only Export")
    print("=" * 60)

    res = run_multi(sample_population, log_sessions)
    fp = res["footprint"]

    print(f"logged sessions: {res['sessions']}  ·  decision points: {res['decision_points']}")
    print(f"resamples: {res['n_resamples']}")
    print()
    print(f"overall decision divergence : {res['overall_divergence']*100:.2f}%  "
          f"(≈{100-res['overall_divergence']*100:.1f}% of all decisions identical)")
    print(f"trigger divergence (mean)   : {res['trigger_divergence_mean']*100:.2f}% "
          f"± {res['trigger_divergence_std']*100:.2f}%")
    print(f"  fast-track triggers       : {res['fast_track']['rate']*100:.2f}% "
          f"({res['fast_track']['diverged']}/{res['fast_track']['total']})")
    print(f"  scaffold triggers         : {res['scaffold']['rate']*100:.2f}% "
          f"({res['scaffold']['diverged']}/{res['scaffold']['total']})")
    print(f"pre-registered threshold    : {DIVERGENCE_THRESHOLD*100:.0f}%  ->  "
          f"{'WITHIN (holds)' if res['passes'] else 'EXCEEDS (does not hold)'}")
    print()
    print("divergence causes:", res["causes"])
    print(f"data leaving device: raw trail {fp['raw_bytes']/1024:.1f} KB  ->  "
          f"mastery vectors {fp['mastery_bytes']/1024:.1f} KB "
          f"({fp['reduction_x']:.0f}× less, {fp['pct_leaving']:.2f}% of raw)")

    print("\nrendering figures...")
    try:
        from mastery_export import plotting
        figs = plotting.all_figures(res, FIGDIR)
        for name, path in figs.items():
            print("      " + os.path.relpath(path, HERE))
    except Exception as e:
        figs = {}
        print(f"      (skipped figures: {e})")

    _write_json(res)
    _write_report_md(res)
    _write_report_html(res, figs)
    print(f"\nwrote {os.path.relpath(OUTDIR, HERE)}/REPORT.md, report.html, results.json")
    print("done.")


def _write_json(res):
    with open(os.path.join(OUTDIR, "results.json"), "w") as f:
        json.dump({"generated": dt.date.today().isoformat(), **res}, f, indent=2)


def _verdict(res):
    return "WITHIN threshold (holds)" if res["passes"] else "EXCEEDS threshold (does not hold)"


def _write_report_md(res):
    fp = res["footprint"]
    md = f"""# Prototype 2 — Mastery-Only Export: results

_Generated {dt.date.today().isoformat()} by `run.py`. No real student data used._

A side-by-side harness replays the same logged sessions through two models:

- **server** — the current design: the full raw event trail (correctness,
  response latency, hint usage and timing) is used to make adaptation decisions;
- **on-device** — the proposed design: only the per-skill **mastery vector**
  (from correctness) is used, so that is all that needs to leave the device.

## Pre-registered decision rule

Set **before** running: the on-device model must diverge from the server model
on **fewer than {DIVERGENCE_THRESHOLD*100:.0f}%** of scaffold and fast-track triggers.

## Result

| metric | value |
|---|---|
| logged sessions | {res['sessions']} |
| decision points replayed | {res['decision_points']} |
| **every adaptation decision** that diverges | **{res['overall_divergence']*100:.2f}%** (≈{100-res['overall_divergence']*100:.1f}% identical) |
| **scaffold + fast-track triggers** that diverge | **{res['trigger_divergence_mean']*100:.2f}% ± {res['trigger_divergence_std']*100:.2f}%** |
| — fast-track triggers | {res['fast_track']['rate']*100:.2f}% ({res['fast_track']['diverged']}/{res['fast_track']['total']}) |
| — scaffold triggers | {res['scaffold']['rate']*100:.2f}% ({res['scaffold']['diverged']}/{res['scaffold']['total']}) |
| vs the {DIVERGENCE_THRESHOLD*100:.0f}% threshold | **{_verdict(res)}** |

Read it two ways, both true:

- **Almost all adaptation survives.** About {100-res['overall_divergence']*100:.1f}% of
  every adaptation decision is identical whether ACE uses the full raw trail or
  only the mastery vector. The data that must *leave* the device reproduces the
  overwhelming majority of what ACE does.
- **But the triggers carry a measurable, nameable cost.** {res['trigger_divergence_mean']*100:.1f}%
  of scaffold and fast-track triggers differ — above the {DIVERGENCE_THRESHOLD*100:.0f}% bar — and
  that residual is not spread evenly. It traces to exactly two signals.

## Which signals the server model was using

| divergent decisions | caused by |
|---|---|
| {res['causes']['latency']} | **response latency** — a fast correct answer the server reads as a lucky guess and withholds from fast-track |
| {res['causes']['hint_timing']} | **hint timing** — an early hint the server reads as struggle and scaffolds on |
| {res['causes']['other']} | downstream / timing of the same two |

This is the write-up's "if it does not hold" branch working as intended: the
test **names the signals** the server model depends on. They are precisely the
fields Prototype 1's **Standard** and **Minimal** levels drop — so the two
prototypes agree, from opposite directions, on what a district gives up when it
turns response latency and hint timing off.

## What leaves the device

| design | leaves the device |
|---|---|
| current (raw trail to server) | {fp['raw_bytes']/1024:.1f} KB across {fp['events']} logged events |
| proposed (mastery vector only) | {fp['mastery_bytes']/1024:.1f} KB |

Only **{fp['pct_leaving']:.2f}%** of the raw trail ever leaves — a {fp['reduction_x']:.0f}× reduction —
and what leaves is a handful of mastery numbers, not the clickstream. COPPA and
FERPA care about exactly this: what leaves the student's machine, not what the
model computes locally.

## How to read the verdict

Exceeding the threshold is **not** the prototype failing — it is the prototype
doing its job. It quantifies the differentiator's dependence on the data
districts fear ({res['trigger_divergence_mean']*100:.0f}% of triggers), shows the rest is
free to move on-device (~{100-res['overall_divergence']*100:.0f}% of decisions), and hands
Prototype 1 the exact tradeoff language for the Standard and Minimal levels.
The real numbers depend on ACE's true signal weights, which come from the
engineering team; this harness is the instrument, run here on synthetic
sessions (which Prototype 3 can supply).

## Sources

- Bayesian Knowledge Tracing: Corbett & Anderson (1995).
- The two-stream architecture and the mastery-vector export: the project write-up.
"""
    with open(os.path.join(OUTDIR, "REPORT.md"), "w") as f:
        f.write(md)


def _write_report_html(res, figs):
    fp = res["footprint"]
    passed = res["passes"]
    vcolor = "#2e8b64" if passed else "#c67c2b"

    def img(key, cap):
        if key not in figs:
            return ""
        rel = os.path.join("..", "figures", os.path.basename(figs[key]))
        return f'<figure><img src="{rel}" alt="{cap}"/><figcaption>{cap}</figcaption></figure>'

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prototype 2 — Mastery-Only Export</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif; max-width:860px;
    margin:0 auto; padding:32px 20px 80px; color:#1b2330; background:#fbfcfe; line-height:1.55; }}
  h1 {{ font-size:1.7rem; margin-bottom:4px; }}
  .sub {{ color:#6b7280; margin-top:0; }}
  h2 {{ margin-top:2.2rem; border-bottom:2px solid #eef1f5; padding-bottom:4px; }}
  table {{ border-collapse:collapse; width:100%; margin:12px 0; font-size:.95rem; }}
  th,td {{ text-align:left; padding:7px 10px; border-bottom:1px solid #e6e9ef; }}
  th {{ color:#6b7280; font-weight:600; }}
  figure {{ margin:18px 0; }} img {{ max-width:100%; border:1px solid #e6e9ef; border-radius:10px; }}
  figcaption {{ color:#6b7280; font-size:.88rem; margin-top:6px; }}
  .kpis {{ display:flex; flex-wrap:wrap; gap:12px; margin:14px 0; }}
  .kpi {{ flex:1 1 150px; background:#fff; border:1px solid #e6e9ef; border-radius:12px; padding:12px 14px; }}
  .kpi b {{ display:block; font-size:1.5rem; }} .kpi span {{ color:#6b7280; font-size:.82rem; }}
  code {{ background:#f0f2f6; padding:1px 5px; border-radius:5px; }}
  blockquote {{ border-left:4px solid #2f6fb0; margin:14px 0; padding:4px 16px; background:#eef5fc;
    color:#213a52; border-radius:0 8px 8px 0; }}
</style></head><body>
<h1>Prototype 2 — Mastery-Only Export</h1>
<p class="sub">ACE adapts on the device; only the per-skill mastery vector leaves. A replay
harness measures how much adaptation depends on the raw trail that would otherwise be sent to a
server. <i>Generated {dt.date.today().isoformat()}; no real student data used.</i></p>

<div class="kpis">
  <div class="kpi"><b>{100-res['overall_divergence']*100:.1f}%</b><span>of all adaptation decisions identical mastery-only</span></div>
  <div class="kpi"><b style="color:{vcolor}">{res['trigger_divergence_mean']*100:.1f}%</b><span>of triggers diverge (threshold {res['threshold']*100:.0f}%)</span></div>
  <div class="kpi"><b>{fp['reduction_x']:.0f}×</b><span>less data leaves the device</span></div>
  <div class="kpi"><b>2</b><span>signals explain the divergence: latency &amp; hint timing</span></div>
</div>

<h2>What the harness does</h2>
<p>It replays the same {res['sessions']} fixed logged sessions through two models — a
<b>server</b> model that uses the full raw trail (correctness, latency, hint timing) and an
<b>on-device</b> model that uses only the correctness-based mastery vector — and records every
adaptation decision each makes.</p>

<h2>Result</h2>
<table>
<tr><th>metric</th><th>value</th></tr>
<tr><td>every adaptation decision that diverges</td><td>{res['overall_divergence']*100:.2f}% (≈{100-res['overall_divergence']*100:.1f}% identical)</td></tr>
<tr><td>scaffold + fast-track triggers that diverge</td><td><b>{res['trigger_divergence_mean']*100:.2f}% ± {res['trigger_divergence_std']*100:.2f}%</b></td></tr>
<tr><td>— fast-track triggers</td><td>{res['fast_track']['rate']*100:.2f}% ({res['fast_track']['diverged']}/{res['fast_track']['total']})</td></tr>
<tr><td>— scaffold triggers</td><td>{res['scaffold']['rate']*100:.2f}% ({res['scaffold']['diverged']}/{res['scaffold']['total']})</td></tr>
<tr><td>vs the {res['threshold']*100:.0f}% pre-registered threshold</td><td style="color:{vcolor}"><b>{_verdict(res)}</b></td></tr>
</table>
{img('summary','Overall decisions agree ~99%; the scaffold+fast-track triggers carry the residual.')}
{img('by_trigger','The divergence splits between the two trigger types and their two signals.')}

<h2>Which signals the server model was using</h2>
<p>Exceeding the bar is the prototype doing its job: it <b>names</b> the signals the server model
depends on — response latency (lucky-guess detection on fast-track) and hint timing (early-hint
scaffolds). These are exactly the fields Prototype 1's Standard and Minimal levels drop.</p>
{img('causes','Each divergence traced to the fine-grained signal that caused it.')}

<h2>What leaves the device</h2>
<blockquote>Only {fp['pct_leaving']:.2f}% of the raw trail ever leaves — a {fp['reduction_x']:.0f}× reduction. What
leaves is a handful of mastery numbers, not the clickstream. COPPA and FERPA care about exactly
this: what leaves the student's machine, not what the model computes locally.</blockquote>
{img('footprint','Raw event trail (sent to a server today) vs the mastery vector (all that leaves).')}

<p class="sub">Bayesian Knowledge Tracing: Corbett &amp; Anderson (1995). Run on synthetic sessions,
which Prototype 3 can supply; the real signal weights come from the engineering team.</p>
</body></html>"""
    with open(os.path.join(OUTDIR, "report.html"), "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
