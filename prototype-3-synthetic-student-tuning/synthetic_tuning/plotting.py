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
        "guess_mult": "Guess multiplier (gaming)",
        "hint": "Hint-seeking propensity",
        "decay": "Forgetting rate",
    }
    n_params = len(PARAMS)
    ncols = 3
    nrows = (n_params + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 3 * nrows))
    axes = axes.ravel()
    for ax, p in zip(axes, PARAMS):
        lo = min(syn[p].min(), real[p].min())
        hi = max(syn[p].max(), real[p].max())
        bins = np.linspace(lo, hi, 22)
        ax.hist(syn[p], bins=bins, color=SYN_C, alpha=0.65, label="synthetic")
        ax.hist(real[p], bins=bins, color=REAL_C, alpha=0.55, label="real (stand-in)")
        ax.set_title(titles.get(p, p))
        ax.set_yticks([])
    for ax in axes[n_params:]:  # blank any unused panels
        ax.axis("off")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", frameon=False, fontsize=11, ncol=2,
               bbox_to_anchor=(0.5, 0.055))
    fig.suptitle("Synthetic learner population vs. the stand-in real cohort "
                 "(six grounded parameters)", fontsize=14, fontweight="bold")
    fig.subplots_adjust(bottom=0.12)
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

    dstd = res.get("delta_std", {})

    def draw(ax, keys, labels, ymax):
        x = np.arange(len(keys))
        syn = [res["eval_syn"][k] for k in keys]
        real = [res["eval_real"][k] for k in keys]
        errs = [dstd.get(k, 0) for k in keys]
        ax.bar(x - w/2, syn, w, color=SYN_C, label="synthetic-tuned ACE",
               yerr=errs, capsize=4, error_kw={"elinewidth": 1, "ecolor": "#6b7280"})
        ax.bar(x + w/2, real, w, color=REAL_C, label="real-tuned ACE",
               yerr=errs, capsize=4, error_kw={"elinewidth": 1, "ecolor": "#6b7280"})
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


def plot_parameter_recovery(recovery, path):
    plt = _mpl()
    rows = recovery["rows"]
    true = [r["true"] for r in rows]
    rec = [r["recovered_mean"] for r in rows]
    err = [r["recovered_std"] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 5.2))
    hi = max(max(true), max(rec)) + 0.15
    ax.plot([0, hi], [0, hi], ls="--", color=MUTED, lw=1.4, label="perfect recovery")
    ax.errorbar(true, rec, yerr=err, fmt="o-", color=SYN_C, lw=2, ms=7, capsize=5,
                label="recovered from one aggregate")
    ax.set_xlabel("true cohort difficulty shift")
    ax.set_ylabel("recovered shift")
    ax.set_xlim(-0.05, hi); ax.set_ylim(-0.05, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(f"The aggregate-only loop recovers true difficulty\n"
                 f"mean absolute error = {recovery['mae']:.3f} over one number per cohort")
    ax.legend(frameon=False, loc="upper left")
    return _save(plt, path)


def plot_scenarios(scenarios, path):
    plt = _mpl()
    names = list(scenarios.keys())
    gaps = [scenarios[n]["retention_gap"] for n in names]
    in_fam = [scenarios[n]["in_family"] for n in names]
    passes = [scenarios[n]["overall_pass"] for n in names]
    colors = [SYN_C if f else REAL_C for f in in_fam]
    order = np.argsort(gaps)
    names = [names[i] for i in order]; gaps = [gaps[i] for i in order]
    colors = [colors[i] for i in order]; passes = [passes[i] for i in order]
    fig, ax = plt.subplots(figsize=(8.5, 5))
    bars = ax.barh(names, gaps, color=colors)
    for b, g, ok in zip(bars, gaps, passes):
        ax.text(g + 0.002, b.get_y() + b.get_height()/2,
                f"{g:.3f}   within-range: {'PASS ✓' if ok else 'FAIL ✗'}",
                va="center", fontsize=9.5,
                color=GOOD_C if ok else "#b23b3b")
    ax.set_xlabel("retention gap (the individual-level blind spot)")
    ax.set_xlim(0, max(gaps) * 1.5)
    import matplotlib.patches as mpatches
    ax.legend(handles=[mpatches.Patch(color=SYN_C, label="inside synthetic family"),
                       mpatches.Patch(color=REAL_C, label="mis-specified shape")],
              frameon=False, loc="lower right")
    ax.set_title("Across every cohort shape, synthetic tuning holds on immediate\n"
                 "outcomes — but the retention blind spot varies with the shape")
    return _save(plt, path)


def plot_sensitivity(sens, path):
    plt = _mpl()
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.6))
    sh = sens["sweeps"]["real_shift"]
    axL.plot([r["value"] for r in sh], [r["retention_gap"] for r in sh],
             "o-", color=SYN_C, lw=2, ms=6, label="retention gap")
    axL.plot([r["value"] for r in sh], [r["recovered_shift"] for r in sh],
             "s--", color=REAL_C, lw=1.8, ms=6, label="recovered shift")
    axL.plot([0.3, 0.9], [0.3, 0.9], ls=":", color=MUTED, lw=1, label="true shift")
    axL.set_xlabel("real cohort difficulty shift"); axL.set_title("Sensitivity to cohort hardness")
    axL.legend(frameon=False, fontsize=9)
    tf = sens["sweeps"]["tail_fraction"]
    axR.plot([r["value"] for r in tf], [r["retention_gap"] for r in tf],
             "o-", color="#8a5cd0", lw=2, ms=6)
    axR.set_xlabel("high-forgetting tail fraction")
    axR.set_ylabel("retention gap")
    axR.set_title("Sensitivity to the forgetting tail")
    fig.suptitle("The within-range result is robust; the retention gap is what moves",
                 fontsize=13, fontweight="bold")
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
    if "recovery" in ctx:
        paths["recovery"] = plot_parameter_recovery(ctx["recovery"], p("08_parameter_recovery.png"))
    if "scenarios" in ctx:
        paths["scenarios"] = plot_scenarios(ctx["scenarios"], p("09_scenarios.png"))
    if "sensitivity" in ctx:
        paths["sensitivity"] = plot_sensitivity(ctx["sensitivity"], p("10_sensitivity.png"))
    return paths
