"""Figures for Prototype 2. matplotlib is imported lazily."""
from __future__ import annotations
import os

SERVER_C = "#d98c2b"   # server (full raw trail) -> amber
DEVICE_C = "#2f6fb0"   # on-device (mastery only) -> blue
LAT_C = "#b23b3b"
HINT_C = "#8a5cd0"
OTHER_C = "#9aa3b2"
GOOD_C = "#2e8b64"
GRID = "#d9dde3"


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 150, "font.size": 11,
        "axes.titlesize": 13, "axes.titleweight": "bold",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
        "axes.axisbelow": True, "figure.facecolor": "white", "axes.facecolor": "white",
    })
    return plt


def _save(plt, path):
    plt.tight_layout(); plt.savefig(path, bbox_inches="tight"); plt.close()
    return path


def plot_summary(res, path):
    plt = _mpl()
    thr = res["threshold"]
    labels = ["every adaptation\ndecision", "scaffold + fast-track\ntriggers"]
    vals = [res["overall_divergence"] * 100, res["trigger_divergence_mean"] * 100]
    errs = [0, res.get("trigger_divergence_std", 0) * 100]
    colors = [DEVICE_C, SERVER_C]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    bars = ax.bar(labels, vals, yerr=errs, color=colors, width=0.55, capsize=5)
    ax.axhline(thr * 100, color=GOOD_C, ls="--", lw=1.6,
               label=f"pre-registered threshold = {thr*100:.0f}%")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, v + 0.3, f"{v:.1f}%",
                ha="center", va="bottom", fontweight="bold")
    ax.set_ylabel("share that diverges (on-device vs server)")
    ax.set_ylim(0, max(vals) * 1.35 + 1)
    ax.set_title("How often mastery-only decisions differ from full-trail decisions")
    ax.legend(frameon=False, loc="upper left")
    return _save(plt, path)


def plot_by_trigger(res, path):
    plt = _mpl()
    import numpy as np
    cats = ["fast-track\ntriggers", "scaffold\ntriggers"]
    rates = [res["fast_track"]["rate"] * 100, res["scaffold"]["rate"] * 100]
    x = np.arange(len(cats))
    fig, ax = plt.subplots(figsize=(7.5, 5))
    bars = ax.bar(x, rates, width=0.5, color=[LAT_C, HINT_C])
    for b, v, n, d in zip(bars, rates,
                          [res["fast_track"]["total"], res["scaffold"]["total"]],
                          [res["fast_track"]["diverged"], res["scaffold"]["diverged"]]):
        ax.text(b.get_x()+b.get_width()/2, v+0.2, f"{v:.1f}%\n({d}/{n})",
                ha="center", va="bottom", fontsize=9.5)
    ax.axhline(res["threshold"]*100, color=GOOD_C, ls="--", lw=1.5,
               label=f"threshold = {res['threshold']*100:.0f}%")
    ax.set_xticks(x); ax.set_xticklabels(cats)
    ax.set_ylabel("share of this trigger that diverges")
    ax.set_ylim(0, max(rates)*1.35+1)
    ax.set_title("Divergence is concentrated in two signals\n"
                 "fast-track ← response latency · scaffold ← hint timing")
    ax.legend(frameon=False)
    return _save(plt, path)


def plot_causes(res, path):
    plt = _mpl()
    c = res["causes"]
    labels = ["response latency\n(lucky-guess on fast-track)",
              "hint timing\n(early-hint scaffold)", "other / downstream"]
    vals = [c["latency"], c["hint_timing"], c["other"]]
    colors = [LAT_C, HINT_C, OTHER_C]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    bars = ax.barh(labels, vals, color=colors)
    for b, v in zip(bars, vals):
        ax.text(v + max(vals)*0.01, b.get_y()+b.get_height()/2, str(v),
                va="center", fontsize=10, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel("number of divergent decisions")
    ax.set_title("Which fine-grained signal each divergence traces to\n"
                 "exactly the fields Prototype 1's Standard / Minimal levels drop")
    return _save(plt, path)


def plot_footprint(res, path):
    plt = _mpl()
    fp = res["footprint"]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    vals = [fp["raw_bytes"]/1024, fp["mastery_bytes"]/1024]
    bars = ax.bar(["raw event trail\n(current: sent to server)",
                   "mastery vector\n(proposed: all that leaves)"],
                  vals, color=[SERVER_C, DEVICE_C], width=0.5)
    ax.set_yscale("log")
    ax.set_ylabel("kilobytes leaving the device (log scale)")
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v*1.1, f"{v:.1f} KB",
                ha="center", va="bottom", fontweight="bold")
    ax.set_title(f"What leaves the student's device\n"
                 f"{fp['reduction_x']:.0f}× less data — only {fp['pct_leaving']:.2f}% of the raw trail")
    return _save(plt, path)


def all_figures(res, outdir):
    os.makedirs(outdir, exist_ok=True)
    p = lambda f: os.path.join(outdir, f)
    return {
        "summary": plot_summary(res, p("01_divergence_summary.png")),
        "by_trigger": plot_by_trigger(res, p("02_divergence_by_trigger.png")),
        "causes": plot_causes(res, p("03_divergence_causes.png")),
        "footprint": plot_footprint(res, p("04_data_footprint.png")),
    }
