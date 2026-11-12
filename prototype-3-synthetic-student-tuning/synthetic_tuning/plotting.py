"""Figures for Prototype 3: calibration curves and the validation story.

matplotlib is imported lazily so the core harness has no hard plotting
dependency. Every figure is written to the given directory as a PNG.
"""
from __future__ import annotations
import os
import numpy as np

# Colourblind-safe, restrained palette.
SYN_C = "#2f6fb0"     # synthetic -> blue
REAL_C = "#d98c2b"    # real      -> amber
GOOD_C = "#2e8b64"    # pass / target -> green
MUTED = "#6b7280"
GRID = "#d9dde3"


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })
    return plt


def _save(plt, path):
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def plot_population(syn, real, path):
    from .learners import PARAMS
    plt = _mpl()
    titles = {
        "prior": "Prior knowledge  P(L0)",
        "learn_mult": "Learning-rate multiplier",
        "slip_mult": "Slip multiplier (errors)",
        "hint": "Hint-seeking propensity",
        "decay": "Forgetting rate",
    }
    fig, axes = plt.subplots(2, 3, figsize=(11, 6))
    axes = axes.ravel()
    for ax, p in zip(axes, PARAMS):
        lo = min(syn[p].min(), real[p].min())
        hi = max(syn[p].max(), real[p].max())
        bins = np.linspace(lo, hi, 22)
        ax.hist(syn[p], bins=bins, color=SYN_C, alpha=0.65, label="synthetic")
        ax.hist(real[p], bins=bins, color=REAL_C, alpha=0.55, label="real (stand-in)")
        ax.set_title(titles[p])
        ax.set_yticks([])
    axes[-1].axis("off")
    h, l = axes[0].get_legend_handles_labels()
    axes[-1].legend(h, l, loc="center", frameon=False, fontsize=12)
    fig.suptitle("Synthetic learner population vs. the stand-in real cohort",
                 fontsize=14, fontweight="bold")
    return _save(plt, path)


def plot_calibration(curve, target, chosen, title, path, xlabel):
    plt = _mpl()
    g = np.array(curve["grid"])
    m = np.array(curve["rate_mean"])
    sd = np.array(curve["rate_std"])
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.fill_between(g, m - sd, m + sd, color=SYN_C, alpha=0.15)
    ax.plot(g, m, "-o", color=SYN_C, lw=2, ms=5, label="firing rate (cohort)")
    ax.axhline(target, color=GOOD_C, ls="--", lw=1.5, label=f"design target = {target:.2f}")
    ci = list(curve["grid"]).index(chosen)
    ax.plot([chosen], [m[ci]], "o", color=GOOD_C, ms=12, mfc="none", mew=2.2,
            label=f"chosen threshold = {chosen:.2f}")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("share of skill encounters that fire")
    ax.set_ylim(0, max(m) * 1.15 + 0.02)
    ax.set_title(title)
    ax.legend(frameon=False)
    return _save(plt, path)


def plot_within_range(res, tol, path):
    plt = _mpl()
    # Two panels so the 0-1 mastery outcomes and the ~11 "opportunities"
    # outcome each get their own axis (never one shared scale).
    left_keys = ["mean_mastery", "bottom_quartile_mastery", "retention"]
    left_labels = ["mean\nmastery", "bottom-quartile\nmastery", "retention"]
    w = 0.38
    fig, (axL, axR) = plt.subplots(
        1, 2, figsize=(10.5, 5.4), gridspec_kw={"width_ratios": [3, 1]})

    def draw(ax, keys, labels, ymax):
        x = np.arange(len(keys))
        syn = [res["eval_syn"][k] for k in keys]
        real = [res["eval_real"][k] for k in keys]
        ax.bar(x - w/2, syn, w, color=SYN_C, label="synthetic-tuned ACE")
        ax.bar(x + w/2, real, w, color=REAL_C, label="real-tuned ACE")
        for i, k in enumerate(keys):
            ok = res["passed"][k]
            top = max(syn[i], real[i])
            ax.text(i, top + ymax*0.03,
                    f"Δ={res['deltas'][k]:.3f}\n"
                    f"{'within ±%g ✓' % tol[k] if ok else 'OUT ✗'}",
                    ha="center", va="bottom", fontsize=9,
                    color=GOOD_C if ok else "#b23b3b")
        ax.set_xticks(x); ax.set_xticklabels(labels)
        ax.set_ylim(0, ymax)

    draw(axL, left_keys, left_labels, 1.0)
    axL.set_ylabel("mastery / retention (0–1)")
    axL.legend(frameon=False, loc="lower center", ncol=2)
    draw(axR, ["opportunities_per_skill"], ["opportunities\nper skill"], 14)
    axR.set_ylabel("items per skill")
    fig.suptitle("Both engines evaluated on the real cohort — "
                 "synthetic-tuned stays within range on every aggregate outcome",
                 fontsize=13, fontweight="bold")
    return _save(plt, path)


def plot_transfer(tr, path):
    plt = _mpl()
    groups = ["Synthetic cohort", "Real cohort"]
    before = [tr["syn_before"], tr["real_before"]]
    after = [tr["syn_after"], tr["real_after"]]
    x = np.arange(len(groups))
    w = 0.38
    fig, ax = plt.subplots(figsize=(7.5, 5))
    b1 = ax.bar(x - w/2, before, w, color=MUTED,
                label=f"tuned scaffold = {tr['tuned_scaf']:.2f}")
    b2 = ax.bar(x + w/2, after, w, color=GOOD_C,
                label=f"improved scaffold = {tr['improved_scaf']:.2f}")
    ax.bar_label(b1, fmt="%.3f", padding=2, fontsize=9)
    ax.bar_label(b2, fmt="%.3f", padding=2, fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(groups)
    ax.set_ylabel("bottom-quartile mastery")
    ax.set_title("A scaffold improvement found on synthetic data\n"
                 "transfers to the real cohort — no individual record leaves")
    ax.legend(frameon=False, loc="lower right")
    ax.set_ylim(0, max(after) * 1.25)
    return _save(plt, path)


def plot_feedback(af, path):
    plt = _mpl()
    shifts = [s for s, _ in af["trace"]]
    rates = [r for _, r in af["trace"]]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.plot(shifts, rates, "-o", color=SYN_C, lw=2, ms=5,
            label="synthetic fast-track rate")
    ax.axhline(af["real_ft_rate"], color=REAL_C, ls="--", lw=1.8,
               label=f"real cohort = {af['real_ft_rate']:.3f}  (the one number shared)")
    ax.axvline(af["recovered_shift"], color=GOOD_C, ls=":", lw=1.8,
               label=f"recovered shift = {af['recovered_shift']:.2f}  (true = {af['true_shift']:.2f})")
    ax.set_xlabel("synthetic difficulty shift")
    ax.set_ylabel("fast-track firing rate")
    ax.set_title("Aggregate-only feedback: one cohort number\n"
                 "re-grounds the synthetic population")
    ax.legend(frameon=False)
    return _save(plt, path)


def plot_caveat(cv, path):
    plt = _mpl()
    cats = ["mean mastery\n(matched aggregate)", "retention\n(the blind spot)"]
    syn = [cv["syn_mean_mastery"], cv["syn_retention"]]
    real = [cv["real_mean_mastery"], cv["real_retention"]]
    x = np.arange(2); w = 0.38
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.bar(x - w/2, syn, w, color=SYN_C, label="synthetic (aggregate-matched)")
    ax.bar(x + w/2, real, w, color=REAL_C, label="real cohort")
    for i, (gap, lo) in enumerate([(cv["mastery_gap"], min(syn[0], real[0])),
                                   (cv["retention_gap"], min(syn[1], real[1]))]):
        ax.text(i, max(syn[i], real[i]) + 0.02, f"gap = {gap:.3f}",
                ha="center", fontsize=10, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(cats)
    ax.set_ylim(0, 1.05)
    ax.set_title("Matching the aggregate is not being right about individuals\n"
                 "the forgetting tail shows up only in retention")
    ax.legend(frameon=False, loc="lower left")
    return _save(plt, path)


def all_figures(ctx, outdir):
    os.makedirs(outdir, exist_ok=True)
    p = lambda f: os.path.join(outdir, f)
    paths = {}
    paths["population"] = plot_population(ctx["syn"], ctx["real"], p("01_population.png"))
    paths["calib_ft"] = plot_calibration(
        ctx["wr"]["curves"]["syn"]["ft_curve"], ctx["FT_TARGET"],
        ctx["wr"]["syn_tuned"]["ft_thr"],
        "Fast-track calibration curve (synthetic cohort)", p("02_calibration_fasttrack.png"),
        "fast-track mastery threshold")
    paths["calib_scaf"] = plot_calibration(
        ctx["wr"]["curves"]["syn"]["scaf_curve"], ctx["SCAF_TARGET"],
        ctx["wr"]["syn_tuned"]["scaf_thr"],
        "Scaffold calibration curve (synthetic cohort)", p("03_calibration_scaffold.png"),
        "scaffold struggle threshold")
    paths["within_range"] = plot_within_range(ctx["wr"], ctx["WITHIN_RANGE"],
                                              p("04_within_range.png"))
    paths["transfer"] = plot_transfer(ctx["tr"], p("05_transfer.png"))
    paths["feedback"] = plot_feedback(ctx["af"], p("06_aggregate_feedback.png"))
    paths["caveat"] = plot_caveat(ctx["cv"], p("07_caveat_retention.png"))
    return paths
