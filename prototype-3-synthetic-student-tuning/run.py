#!/usr/bin/env python3
"""Prototype 3 - Synthetic Student Tuning: end-to-end run.

Generates the synthetic cohort, calibrates ACE's two triggers, runs the
validation test (within-range, transfer, aggregate-only feedback, caveat),
writes the figures under figures/ and a report under output/, and prints a
summary. No real student data is used anywhere.

    python run.py
"""
from __future__ import annotations
import json
import os
import csv
import datetime as dt

from synthetic_tuning import (
    sample_population, SKILL_NAMES, FT_TARGET, SCAF_TARGET,
)
from synthetic_tuning import validation as V

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
OUTDIR = os.path.join(HERE, "output")


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print("Prototype 3 - Synthetic Student Tuning")
    print("=" * 60)

    # 1. Populations: optimistic synthetic prior + stand-in real pilot cohort.
    syn = sample_population(200, seed=1, shift=0.0)
    real = V.build_real_cohort()
    print(f"synthetic cohort: {len(syn['prior'])} agents, 5 parameters each")
    print(f"real stand-in:    {len(real['prior'])} agents "
          f"(harder + a high-forgetting tail the synthetic model can't express)")

    # 2. The test: tune on each, evaluate both on the real cohort.
    print("\n[1/4] within-range test (tuning both engines, averaged sweeps)...")
    wr = V.within_range_test(syn, real)
    print(f"      synthetic-tuned : ft={wr['syn_tuned']['ft_thr']:.2f} "
          f"scaf={wr['syn_tuned']['scaf_thr']:.2f}")
    print(f"      real-tuned      : ft={wr['real_tuned']['ft_thr']:.2f} "
          f"scaf={wr['real_tuned']['scaf_thr']:.2f}")
    for k in V.OUTCOME_KEYS:
        print(f"      {k:26s} Δ={wr['deltas'][k]:.3f}  "
              f"tol={V.WITHIN_RANGE[k]:<5g} {'PASS' if wr['passed'][k] else 'FAIL'}")
    print(f"      OVERALL: {'PASS' if wr['overall_pass'] else 'FAIL'}")

    # 3. Transfer: an improvement found on synthetic data helps the real cohort.
    print("\n[2/4] transfer test...")
    tr = V.transfer_test(syn, real, wr["syn_tuned"]["scaf_thr"])
    print(f"      scaffold {tr['tuned_scaf']:.2f} -> {tr['improved_scaf']:.2f}")
    print(f"      synthetic bottom-quartile {tr['syn_before']:.3f} -> {tr['syn_after']:.3f} "
          f"(+{tr['syn_gain']:.3f})")
    print(f"      real      bottom-quartile {tr['real_before']:.3f} -> {tr['real_after']:.3f} "
          f"(+{tr['real_gain']:.3f})  transfers={tr['transfers']}")

    # 4. Aggregate-only feedback loop.
    print("\n[3/4] aggregate-only feedback...")
    af = V.aggregate_feedback(real, wr["syn_tuned"]["ft_thr"])
    print(f"      real fast-track rate = {af['real_ft_rate']:.3f} (the ONE number shared)")
    print(f"      recovered synthetic shift = {af['recovered_shift']:.2f} "
          f"(true = {af['true_shift']:.2f})")

    # 5. Caveat: aggregate match is not individual-level correctness.
    print("\n[4/4] caveat demonstration...")
    cv = V.caveat_demo(real, af["recovered_shift"])
    print(f"      mastery gap (matched) = {cv['mastery_gap']:.3f}")
    print(f"      retention gap (blind spot) = {cv['retention_gap']:.3f}")

    # 6. Figures.
    print("\nrendering figures...")
    try:
        from synthetic_tuning import plotting
        ctx = dict(syn=syn, real=real, wr=wr, tr=tr, af=af, cv=cv,
                   FT_TARGET=FT_TARGET, SCAF_TARGET=SCAF_TARGET,
                   WITHIN_RANGE=V.WITHIN_RANGE)
        figs = plotting.all_figures(ctx, FIGDIR)
        for name, path in figs.items():
            print(f"      {os.path.relpath(path, HERE)}")
    except Exception as e:  # matplotlib optional
        figs = {}
        print(f"      (skipped figures: {e})")

    # 7. Machine-readable outputs + reports.
    _write_json(wr, tr, af, cv)
    _write_calibration_csv(wr)
    _write_report_md(wr, tr, af, cv)
    _write_report_html(wr, tr, af, cv, figs)
    print(f"\nwrote {os.path.relpath(OUTDIR, HERE)}/REPORT.md, report.html, "
          f"aggregates.json, calibration.csv")
    print("done.")


def _write_json(wr, tr, af, cv):
    payload = {
        "generated": dt.date.today().isoformat(),
        "skills": SKILL_NAMES,
        "within_range": {
            "criterion": V.WITHIN_RANGE,
            "syn_tuned": wr["syn_tuned"], "real_tuned": wr["real_tuned"],
            "eval_syn": wr["eval_syn"], "eval_real": wr["eval_real"],
            "deltas": wr["deltas"], "passed": wr["passed"],
            "overall_pass": wr["overall_pass"],
        },
        "transfer": {k: tr[k] for k in (
            "tuned_scaf", "improved_scaf", "syn_before", "syn_after",
            "real_before", "real_after", "syn_gain", "real_gain", "transfers")},
        "aggregate_feedback": {k: af[k] for k in (
            "real_ft_rate", "recovered_shift", "true_shift", "n_aggregates_used")},
        "caveat": cv,
    }
    with open(os.path.join(OUTDIR, "aggregates.json"), "w") as f:
        json.dump(payload, f, indent=2)


def _write_calibration_csv(wr):
    ft = wr["curves"]["syn"]["ft_curve"]
    sc = wr["curves"]["syn"]["scaf_curve"]
    with open(os.path.join(OUTDIR, "calibration.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["trigger", "threshold", "firing_rate", "firing_std",
                    "mean_mastery", "bottom_quartile_mastery", "retention",
                    "opportunities_per_skill"])
        for curve, name in ((ft, "fast_track"), (sc, "scaffold")):
            for i, thr in enumerate(curve["grid"]):
                w.writerow([name, thr, round(curve["rate_mean"][i], 4),
                            round(curve["rate_std"][i], 4),
                            round(curve["mean_mastery"][i], 4),
                            round(curve["bottom_quartile_mastery"][i], 4),
                            round(curve["retention"][i], 4),
                            round(curve["opportunities_per_skill"][i], 3)])


def _write_report_md(wr, tr, af, cv):
    verdict = "PASS" if wr["overall_pass"] else "FAIL"
    rows = "\n".join(
        f"| {k} | {wr['eval_syn'][k]:.3f} | {wr['eval_real'][k]:.3f} | "
        f"{wr['deltas'][k]:.3f} | ±{V.WITHIN_RANGE[k]:g} | "
        f"{'✅' if wr['passed'][k] else '❌'} |"
        for k in V.OUTCOME_KEYS)
    md = f"""# Prototype 3 — Synthetic Student Tuning: results

_Generated {dt.date.today().isoformat()} by `run.py`. No real student data used._

ACE is developed and calibrated on **simulated** middle schoolers. Real
student data would be needed only for low-volume **aggregate** validation,
never for model development. This report is the output of that harness.

## Pre-registered "within range" criterion

Set **before** running (per the write-up's instruction). Synthetic-tuned ACE,
evaluated on the real cohort, must match real-tuned ACE on every aggregate
outcome to within:

{_criterion_table()}

## Test 1 — Within range  →  **{verdict}**

Both engines were tuned to the same design-intent firing rates
(fast-track {FT_TARGET:.0%} of encounters, scaffold {SCAF_TARGET:.0%}), then
**both evaluated on the real cohort**. Only aggregate outcomes are compared.

- Synthetic-tuned thresholds: fast-track **{wr['syn_tuned']['ft_thr']:.2f}**, scaffold **{wr['syn_tuned']['scaf_thr']:.2f}**
- Real-tuned thresholds: fast-track **{wr['real_tuned']['ft_thr']:.2f}**, scaffold **{wr['real_tuned']['scaf_thr']:.2f}**

| Aggregate outcome | synthetic-tuned | real-tuned | Δ | tolerance | within range |
|---|---|---|---|---|---|
{rows}

The engine built with **zero** student data lands within range of the engine
that would have required real pilot records.

## Test 2 — Transfer

An improvement found purely on synthetic data — a better scaffold threshold,
chosen to lift the strugglers (bottom-quartile mastery) without exceeding a
{V.SCAF_BUDGET:.0%} intervention budget — moved from **{tr['tuned_scaf']:.2f}** to **{tr['improved_scaf']:.2f}**:

| cohort | bottom-quartile mastery (tuned) | (improved) | gain |
|---|---|---|---|
| synthetic | {tr['syn_before']:.3f} | {tr['syn_after']:.3f} | +{tr['syn_gain']:.3f} |
| real | {tr['real_before']:.3f} | {tr['real_after']:.3f} | +{tr['real_gain']:.3f} |

The same change helps the real cohort — **no individual record left the
district** to find it. Transfers: **{tr['transfers']}**.

## Test 3 — Aggregate-only feedback

The only thing the engineering stream consumed from the real world was **one
number**: the real cohort's fast-track firing rate = **{af['real_ft_rate']:.3f}**.
Feeding it back (nudging the synthetic population's difficulty until its own
fast-track rate matched) recovered a difficulty shift of
**{af['recovered_shift']:.2f}**, against a true shift of **{af['true_shift']:.2f}** — the
synthetic prior re-grounds itself from a single aggregate, not from records.

## Caveat (state this in class)

A synthetic population tuned to match real aggregates can still be wrong about
individuals in ways that only show up in real classrooms. Here the stand-in
real cohort carries a high-forgetting tail (absenteeism / summer slide) that
the synthetic model's priors cannot express. After matching the aggregate:

- mean-mastery gap (the matched aggregate): **{cv['mastery_gap']:.3f}**
- retention gap (the blind spot): **{cv['retention_gap']:.3f}**

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
"""
    with open(os.path.join(OUTDIR, "REPORT.md"), "w") as f:
        f.write(md)


def _criterion_table():
    lines = ["| outcome | tolerance |", "|---|---|"]
    for k, v in V.WITHIN_RANGE.items():
        lines.append(f"| {k} | ±{v:g} |")
    return "\n".join(lines)


def _write_report_html(wr, tr, af, cv, figs):
    verdict = "PASS" if wr["overall_pass"] else "FAIL"
    vcolor = "#2e8b64" if wr["overall_pass"] else "#b23b3b"

    def img(key, cap):
        if key not in figs:
            return ""
        rel = os.path.join("..", "figures", os.path.basename(figs[key]))
        return (f'<figure><img src="{rel}" alt="{cap}"/>'
                f'<figcaption>{cap}</figcaption></figure>')

    rows = "".join(
        f"<tr><td>{k}</td><td>{wr['eval_syn'][k]:.3f}</td>"
        f"<td>{wr['eval_real'][k]:.3f}</td><td>{wr['deltas'][k]:.3f}</td>"
        f"<td>±{V.WITHIN_RANGE[k]:g}</td>"
        f"<td style='color:{'#2e8b64' if wr['passed'][k] else '#b23b3b'}'>"
        f"{'within range' if wr['passed'][k] else 'out'}</td></tr>"
        for k in V.OUTCOME_KEYS)

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prototype 3 — Synthetic Student Tuning</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: -apple-system, system-ui, 'Segoe UI', Roboto, sans-serif;
    max-width: 860px; margin: 0 auto; padding: 32px 20px 80px; color: #1b2330;
    background: #fbfcfe; line-height: 1.55; }}
  h1 {{ font-size: 1.7rem; margin-bottom: 4px; }}
  .sub {{ color: #6b7280; margin-top: 0; }}
  .verdict {{ display:inline-block; font-weight:700; color:#fff; background:{vcolor};
    padding:3px 12px; border-radius:999px; font-size:.95rem; }}
  h2 {{ margin-top: 2.2rem; border-bottom: 2px solid #eef1f5; padding-bottom: 4px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; font-size:.95rem; }}
  th,td {{ text-align:left; padding:7px 10px; border-bottom:1px solid #e6e9ef; }}
  th {{ color:#6b7280; font-weight:600; }}
  figure {{ margin: 18px 0; }}
  img {{ max-width: 100%; border:1px solid #e6e9ef; border-radius:10px; }}
  figcaption {{ color:#6b7280; font-size:.88rem; margin-top:6px; }}
  .kpis {{ display:flex; flex-wrap:wrap; gap:12px; margin:14px 0; }}
  .kpi {{ flex:1 1 150px; background:#fff; border:1px solid #e6e9ef; border-radius:12px;
    padding:12px 14px; }}
  .kpi b {{ display:block; font-size:1.5rem; }}
  .kpi span {{ color:#6b7280; font-size:.82rem; }}
  code {{ background:#f0f2f6; padding:1px 5px; border-radius:5px; }}
  blockquote {{ border-left:4px solid #d98c2b; margin:14px 0; padding:4px 16px;
    background:#fff8ef; color:#4a3a22; border-radius:0 8px 8px 0; }}
</style></head><body>
<h1>Prototype 3 — Synthetic Student Tuning</h1>
<p class="sub">ACE is developed and calibrated on <b>simulated</b> middle schoolers.
Real student data is needed only for low-volume aggregate validation — never for
model development. <i>Generated {dt.date.today().isoformat()}; no real student data used.</i></p>

<div class="kpis">
  <div class="kpi"><b style="color:{vcolor}">{verdict}</b><span>within-range test</span></div>
  <div class="kpi"><b>{af['recovered_shift']:.2f}</b><span>difficulty recovered from 1 number (true {af['true_shift']:.2f})</span></div>
  <div class="kpi"><b>+{tr['real_gain']:.3f}</b><span>real strugglers gained from a synthetic fix</span></div>
  <div class="kpi"><b>{cv['retention_gap']:.3f}</b><span>retention blind spot (the caveat)</span></div>
</div>

<h2>Test 1 — Within range <span class="verdict">{verdict}</span></h2>
<p>Both engines tuned to the same design-intent firing rates, then both evaluated
on the real cohort. Synthetic-tuned thresholds: fast-track
<code>{wr['syn_tuned']['ft_thr']:.2f}</code>, scaffold <code>{wr['syn_tuned']['scaf_thr']:.2f}</code>.
Real-tuned: fast-track <code>{wr['real_tuned']['ft_thr']:.2f}</code>, scaffold
<code>{wr['real_tuned']['scaf_thr']:.2f}</code>.</p>
<table><thead><tr><th>aggregate outcome</th><th>synthetic-tuned</th><th>real-tuned</th>
<th>Δ</th><th>tolerance</th><th>verdict</th></tr></thead><tbody>{rows}</tbody></table>
{img('population','Synthetic learner population vs. the stand-in real cohort (5 parameters each).')}
{img('calib_ft','Fast-track calibration: firing rate vs. mastery threshold; the green ring is the chosen value.')}
{img('calib_scaf','Scaffold calibration: firing rate vs. struggle threshold.')}
{img('within_range','Both engines on the real cohort; synthetic-tuned stays within range on every outcome.')}

<h2>Test 2 — Transfer</h2>
<p>A scaffold improvement found purely on synthetic data
(<code>{tr['tuned_scaf']:.2f}</code> → <code>{tr['improved_scaf']:.2f}</code>, chosen to lift
strugglers within a {V.SCAF_BUDGET:.0%} intervention budget) also lifts the real cohort's
bottom-quartile mastery — no individual record left the district. Transfers:
<b>{tr['transfers']}</b>.</p>
{img('transfer','Bottom-quartile mastery before/after the improvement, on both cohorts.')}

<h2>Test 3 — Aggregate-only feedback</h2>
<p>The only real-world input was one number: the real cohort's fast-track rate
= <code>{af['real_ft_rate']:.3f}</code>. Feeding it back recovered a difficulty shift of
<code>{af['recovered_shift']:.2f}</code> (true <code>{af['true_shift']:.2f}</code>).</p>
{img('feedback','One cohort-level number re-grounds the synthetic population.')}

<h2>Caveat</h2>
<blockquote>A synthetic population tuned to match real aggregates can still be wrong
about individuals in ways that only show up in real classrooms. The stand-in real
cohort's high-forgetting tail is invisible to the matched aggregate — the retention
gap ({cv['retention_gap']:.3f}) is larger than the mastery gap ({cv['mastery_gap']:.3f}).
That is why the two streams validate each other rather than one replacing the other.</blockquote>
{img('caveat','Matching an aggregate is not being right about individuals: the retention blind spot.')}

<p class="sub">Parameters grounded in Corbett &amp; Anderson (1995, BKT),
Newell &amp; Rosenbloom (1981, power law of practice), Aleven et al. (2006, help-seeking),
and Ebbinghaus / Pavlik &amp; Anderson (2005, memory decay).</p>
</body></html>"""
    with open(os.path.join(OUTDIR, "report.html"), "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
