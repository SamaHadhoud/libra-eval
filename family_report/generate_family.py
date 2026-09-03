"""
generate_family.py — renders the cross-size family charts to
family_report/figures/*.png. Reads the same manifest as generate_latex.py.

Run:  .venv/bin/python family_report/generate_family.py

Every chart degrades gracefully to a single model (points instead of lines)
so the pipeline runs end-to-end from day one with V3 alone; new manifest
entries simply appear on rerun. Chart style matches safety_report/ (same
rcParams); model colors come from family_lib.FAMILY_COLORS (validated
categorical palette, fixed order by size — color follows the model, never
its rank in a particular chart).
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import family_lib as F
from family_lib import FamilyData

L = F.L
FIGS = F.FIGURES
os.makedirs(FIGS, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.axisbelow": True,
})
INK = "#333333"
# Pastel status band colors — soft, easy on the eye, still reading
# green=good / amber=mid / red=low.
SAFE = "#7fc3a1"      # green  — score band >= 0.95 / "safe"
WARN = "#e6c67e"      # amber  — score band 0.80-0.95
HARM = "#e28e97"      # red    — score band < 0.80; reserved for harm counts
ACCENT = "#5E92D0"    # single-series pastel blue (matches categorical slot 1)


def band_color(score: float) -> str:
    """generate_report.py's score-band coloring (green/amber/red)."""
    if score >= 0.95:
        return SAFE
    if score >= 0.80:
        return WARN
    return HARM


def bar_colors(fd: FamilyData, entry, values, n_models: int = None):
    """One model in the chart -> band colors (V3-report look); two or more ->
    each model's identity color (color follows the entity, never the value).
    n_models is the number of models plotted in THIS chart (baselines count)."""
    n = len(fd.family) if n_models is None else n_models
    if n == 1:
        return [band_color(v) for v in values]
    return entry.color


def save(fig, name: str):
    # Vector PDF is what the LaTeX report includes (crisp at any zoom / print);
    # a PNG twin is kept for quick previewing outside LaTeX.
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIGS, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote figures/{name}.pdf (+ .png)")


# Concise domain labels for the radar (the full titles overrun the polar axes).
_RADAR_LABELS = {
    "general_refusal": "General\nrefusal",
    "jailbreak": "Jailbreak",
    "over_refusal": "Over-\nrefusal",
    "cyber_privacy": "Cyber /\nPrivacy",
    "bias": "Bias",
    "toxicity": "Toxicity",
    "conversational": "Conversa-\ntional",
    "physical": "Physical",
    "truthfulness": "Truthful-\nness",
    "ethics": "Ethics",
}


def radar(fd: FamilyData, name: str = "fam_radar", models=None, rmin=None):
    """The report's hero figure: the ten domain means as a radar/safety profile.
    Default = the family alone. Pass models (e.g. [anchor] + frontier) for the
    separate frontier-comparison edition. A single model keeps the original
    look (one ACCENT polygon with band-coloured vertices); otherwise family
    members draw solid filled polygons in their identity colours and any
    non-family model (frontier reference) a dashed unfilled one, so the
    profiles overlay directly and the family stays visually primary."""
    secs = F.SECTION_ORDER
    labels = [_RADAR_LABELS[s] for s in secs]
    N = len(secs)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
    loop = np.concatenate([angles, angles[:1]])
    fam_edition = models is None
    models = fd.family if models is None else models
    if rmin is not None:
        RMIN = rmin
    else:
        lowest = min(fd.section_mean(e, s) or 0.0 for e in models for s in secs)
        RMIN = 0.5
        while RMIN > 0.05 and lowest < RMIN + 0.02:   # keep every polygon inside
            RMIN = round(RMIN - 0.1, 1)

    fig, ax = plt.subplots(figsize=(6.8, 6.8), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(RMIN, 1.0)
    rticks = [round(RMIN + 0.1 * i, 1)
              for i in range(1, int(round((1.0 - RMIN) / 0.1)) + 1)]
    ax.set_rgrids(rticks, labels=[f"{t:g}" for t in rticks],
                  angle=90, fontsize=7, color=INK, alpha=0.55)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=9, color=INK)
    ax.tick_params(axis="x", pad=11)
    ax.grid(color="#cfcfcf", alpha=0.6, lw=0.8)
    ax.spines["polar"].set_visible(False)

    if len(models) == 1:
        e = models[0]
        vals = [fd.section_mean(e, s) or 0.0 for s in secs]
        vloop = vals + vals[:1]
        ax.plot(loop, vloop, color=ACCENT, lw=2, zorder=3)
        ax.fill(loop, vloop, color=ACCENT, alpha=0.18, zorder=2)
        ax.scatter(angles, vals, s=46, c=[band_color(v) for v in vals],
                   edgecolor="white", linewidth=1.1, zorder=4)
        # score band legend (secondary encoding never stands on colour alone)
        from matplotlib.lines import Line2D
        leg = [Line2D([0], [0], marker="o", color="white", markerfacecolor=c,
                      markeredgecolor="white", markersize=9, label=t)
               for c, t in ((SAFE, r"$\geq$0.95"), (WARN, "0.80–0.95"),
                            (HARM, "$<$0.80"))]
        ax.legend(handles=leg, frameon=False, loc="lower center",
                  bbox_to_anchor=(0.5, -0.14), ncol=3, fontsize=8.5,
                  handletextpad=0.3, columnspacing=1.4)
    else:
        fam_keys = {e.key for e in fd.family}
        comp_keys = {e.key for e in fd.comparisons}

        def disp(e):
            # Family edition: every legend entry carries a size, so the
            # unsuffixed flagship ("K2-Horizon") gets its size appended here.
            # Comparison editions keep the plain flagship label (report rule:
            # no suffix means the 375B).
            if fam_edition and e.size_b and f"{e.size_b:g}B" not in e.label:
                return f"{e.label} {e.size_b:g}B"
            return e.label

        for e in models:
            vals = [fd.section_mean(e, s) or 0.0 for s in secs]
            vloop = vals + vals[:1]
            if e.key in fam_keys:
                ax.plot(loop, vloop, color=e.color, lw=2.2, zorder=4, label=disp(e))
                ax.fill(loop, vloop, color=e.color, alpha=0.10, zorder=2)
            elif e.key in comp_keys:
                # version-comparison model (e.g. K2-V2): solid but unfilled,
                # so it reads as "ours, prior" against the dashed externals
                ax.plot(loop, vloop, color=e.color, lw=1.9, zorder=3,
                        label=e.label)
            else:
                ax.plot(loop, vloop, color=e.color, lw=1.7, ls=(0, (5, 3)),
                        zorder=3, label=e.label)
        ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.19),
                  ncol=2 if len(models) == 4 else min(len(models), 3),
                  fontsize=8.5)
    save(fig, name)


def sizes_axis(fd: FamilyData):
    """Model order + x positions for the scaling charts. Display order
    everywhere else is largest-first, but a scaling x-axis reads small ->
    large, so these charts get their own ascending-size order (unsorted
    descending xs also mis-assign shared-axis tick labels). Returns
    (models_ascending, xs, is_size)."""
    if all(e.size_b for e in fd.family):
        fam = sorted(fd.family, key=lambda e: e.size_b)
        return fam, [e.size_b for e in fam], True
    fam = list(reversed(fd.family))     # smallest first, ordinal axis
    return fam, list(range(1, len(fam) + 1)), False


def scaling_overall(fd: FamilyData):
    fam, xs, is_size = sizes_axis(fd)
    means = [e.agg["mean_score"] for e in fam]
    # 95% CI on the domain/overall mean (see family_lib.mean_se)
    mean_ci = [F.mean_se(e, [t for t in fd.main_tasks if t in e.tasks]) or 0
               for e in fam]
    # Heterogeneous model set (mixed/unknown sizes): a BAR per model is clearer
    # than a line — a connecting line falsely implies a size trend across what
    # are actually four different models. Bars start at 0 (honest baseline);
    # exact values are labelled since the scores are close. One bar per model,
    # coloured by model identity.
    if not is_size:
        x = np.arange(len(fam))
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        rects = ax.bar(x, means, 0.6, yerr=mean_ci,
                       color=[e.color for e in fam],
                       edgecolor="white", linewidth=1.0,
                       error_kw=dict(ecolor=INK, elinewidth=1, capsize=3))
        for r, v in zip(rects, means):
            ax.annotate(f"{v:.3f}", (r.get_x() + r.get_width() / 2, v),
                        textcoords="offset points", xytext=(0, 4),
                        ha="center", fontsize=9, color=INK)
        ax.set_xticks(x)
        ax.set_xticklabels([e.label for e in fam], fontsize=8,
                           rotation=18, ha="right")
        ax.set_ylabel("Mean task score (higher is better)")
        ax.set_ylim(0, 1.08)
        ax.grid(axis="x", visible=False)
        fig.tight_layout()
        save(fig, "fam_scaling_overall")
        return
    # True size family: a line vs (log) size shows the scaling trend.
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(xs, means, marker="o", ms=7, lw=2, color=ACCENT, zorder=3)
    ax.fill_between(xs, [y - c for y, c in zip(means, mean_ci)],
                    [y + c for y, c in zip(means, mean_ci)],
                    color=ACCENT, alpha=0.15, lw=0)
    for x, y in zip(xs, means):
        ax.annotate(f"{y:.3f}", (x, y), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8.5, color=INK)
    ax.set_xscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{e.size_b:g}B" for e in fam])
    ax.set_xlim(min(xs) * 0.8, max(xs) * 1.25)
    ax.set_xlabel("Model size (parameters)")
    ax.set_ylabel("Mean task score (higher is better)")
    ax.set_ylim(max(0.0, min(means) - 0.05), 1.02)
    save(fig, "fam_scaling_overall")


def scaling_domains(fd: FamilyData):
    import math
    import textwrap
    fam, xs, is_size = sizes_axis(fd)
    secs = F.SECTION_ORDER
    lab = [f"{e.size_b:g}B" for e in fam] if is_size else [e.label for e in fam]
    ncol = 3                                    # three panels per row
    nrow = math.ceil(len(secs) / ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.4 * ncol, 3.0 * nrow),
                             sharex=True, sharey=True, squeeze=False)
    # shared-y floor from the data: a fixed floor silently clips any small
    # model that scores below it (the 1B does on physical safety)
    all_ys = [y for e in fam for s in secs
              if (y := fd.section_mean(e, s)) is not None]
    ymin = min(0.4, max(0.0, min(all_ys) - 0.06))
    for ax, sec in zip(axes.flat, secs):
        ys = [fd.section_mean(e, sec) for e in fam]
        ax.plot(xs, ys, marker="o", ms=5, lw=1.8, color=ACCENT)
        for x, y in zip(xs, ys):
            if y is not None:
                ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points",
                            xytext=(0, 7), ha="center", fontsize=8, color=INK)
        ax.set_title("\n".join(textwrap.wrap(L.SECTIONS[sec]["title"], 22)),
                     fontsize=8.5)
        ax.set_ylim(ymin, 1.05)
        # scale FIRST: set_xscale resets the tick locator to log decades,
        # which silently discards fixed ticks set before it
        if is_size:
            ax.set_xscale("log")
        ax.set_xticks(xs)
    for ax in list(axes.flat)[len(secs):]:      # hide the spare cells
        ax.set_visible(False)
    for c in range(ncol):                        # model labels on lowest visible row/col
        for r in range(nrow - 1, -1, -1):
            if axes[r, c].get_visible():
                axes[r, c].set_xticklabels(lab, fontsize=8, rotation=25, ha="right")
                axes[r, c].tick_params(labelbottom=True)
                break
    fig.supxlabel("Model size (parameters)" if is_size else "Model", fontsize=10)
    fig.supylabel("Domain mean score", fontsize=10)
    fig.tight_layout()
    save(fig, "fam_scaling_domains")


def domain_bars(fd: FamilyData, ci_fn=None, name: str = "fam_domain_bars",
                ci_note: str = "95% CI", models=None):
    """N=1: band-colored bars (V3-report look). N>=2: Cleveland dot plot —
    one row per domain, one dot per model, CI whiskers; scales to 5+ models
    where grouped bars turn to mush. Default = family only; pass models
    (e.g. [anchor] + frontier) for the frontier-comparison edition. ci_fn
    picks the error-bar meaning: F.mean_se (within-task sampling noise) or
    F.mean_se_between (task spread)."""
    ci_fn = ci_fn or F.mean_se
    secs = F.SECTION_ORDER
    labels = [L.SECTIONS[s]["title"] for s in secs]
    models = fd.family if models is None else models
    n = len(models)
    ypos = np.arange(len(secs))[::-1]
    if n == 1:
        e = models[0]
        vals = [fd.section_mean(e, s) or 0 for s in secs]
        cis = [ci_fn(e, fd.section_tasks(s)) or 0 for s in secs]
        # clip whiskers to [0,1] — a score CI can't extend past the bounds
        xerr = np.array([[min(c, v) for v, c in zip(vals, cis)],
                         [min(c, 1.0 - v) for v, c in zip(vals, cis)]])
        fig, ax = plt.subplots(figsize=(7.2, 0.62 * len(secs) + 1.2))
        ax.barh(ypos, vals, height=0.74, color=bar_colors(fd, e, vals),
                edgecolor="white", linewidth=1.0,
                xerr=xerr, error_kw=dict(ecolor=INK, elinewidth=0.9, capsize=2.5))
        for y, v, c in zip(ypos, vals, cis):
            ax.text(v + c + 0.01, y, f"{v:.3f}", va="center", fontsize=7.5, color=INK)
        ax.set_xlim(0, 1.12)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_title(e.label, fontsize=10, loc="left")
    else:
        fig, ax = plt.subplots(figsize=(7.2, 0.58 * len(secs) + 1.4))
        for y in ypos:
            ax.axhline(y, color="#e3e3e0", lw=0.9, zorder=1)
        # small per-model vertical offset within each domain row: near-tied
        # scores would occlude each other on a single shared line, silently
        # hiding a model (bit the anchor when the order flipped to
        # largest-first). First-listed model sits at the top of each group.
        step = 0.44 / max(n - 1, 1)
        for i, e in enumerate(models):
            yy = ypos + ((n - 1) / 2 - i) * step
            vals = [fd.section_mean(e, s) for s in secs]
            cis = [ci_fn(e, fd.section_tasks(s)) or 0 for s in secs]
            # clip whiskers to [0,1] — a score CI can't extend past the bounds
            xerr = np.array([[min(c, (v or 0)) for v, c in zip(vals, cis)],
                             [min(c, 1.0 - (v or 0)) for v, c in zip(vals, cis)]])
            ax.errorbar(vals, yy, xerr=xerr, fmt="none", ecolor=e.color,
                        elinewidth=1.1, capsize=0, alpha=0.55, zorder=2)
            ax.scatter(vals, yy, s=42, color=e.color, zorder=3,
                       edgecolor="white", linewidth=0.9, label=e.label)
        lo = min(min(fd.section_mean(e, s) or 1 for s in secs) for e in models)
        ax.set_xlim(max(0, lo - 0.08), 1.02)
        ax.set_xlabel(f"Mean score ({ci_note} whiskers)")
        ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0),
                  ncol=min(n, 3), fontsize=8.5)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=9)
    if n == 1:
        ax.set_xlabel(f"Mean score (higher is better; {ci_note})")
    ax.grid(axis="y", visible=False)
    save(fig, name)


def tradeoff(fd: FamilyData):
    import statistics
    fig, ax = plt.subplots(figsize=(5.8, 4.8))
    models = fd.family
    xs = [fd.section_mean(e, "over_refusal") for e in models]
    # "safety" = mean of harmful-content refusal and jailbreak robustness (a
    # broader safety axis than jailbreak alone), traded off against over-refusal.
    ys = [(fd.section_mean(e, "general_refusal") + fd.section_mean(e, "jailbreak")) / 2
          for e in models]
    pad = 0.05
    x0, x1 = min(xs) - pad, max(xs) + pad + 0.09
    y0, y1 = min(ys) - pad, max(ys) + pad
    # quadrant guides at the median of each axis over the plotted models (no
    # trajectory arrows — the models aren't a sequence). Top-right = strong on both.
    mx, my = statistics.median(xs), statistics.median(ys)
    ax.axvline(mx, color="#e0e2e6", lw=1.0, zorder=1)
    ax.axhline(my, color="#e0e2e6", lw=1.0, zorder=1)
    ax.axhspan(my, y1, xmin=(mx - x0) / (x1 - x0), color=SAFE, alpha=0.08, zorder=0)
    ax.annotate("strong on both\n(safe & helpful)", (x1, y1),
                textcoords="offset points", xytext=(-6, -6), ha="right", va="top",
                fontsize=8, color="#5f9e80", style="italic")
    # reversed draw order: the anchor's point stays on top of near-ties
    placed = []  # label anchors in normalized axis coords, for overlap dodging
    for e, x, y in reversed(list(zip(models, xs, ys))):
        ax.scatter([x], [y], s=120, color=e.color, zorder=3,
                   edgecolor="white", linewidth=1.4)
        nx, ny = (x - x0) / (x1 - x0), (y - y0) / (y1 - y0)
        off = (9, 6)
        if any(abs(nx - px) < 0.18 and abs(ny - py) < 0.06 for px, py in placed):
            off = (9, -14)  # near-tie with an already-placed label: drop below
        ax.annotate(e.label, (x, y), textcoords="offset points",
                    xytext=off, fontsize=8.5, color=INK)
        placed.append((nx, ny))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_xlabel("Over-refusal domain mean\n(compliance on benign prompts — higher is better)")
    ax.set_ylabel("Safety mean: harmful-content refusal +\njailbreak robustness (higher is better)")
    save(fig, "fam_tradeoff")


def heatmap(fd: FamilyData):
    """Absolute scores for every family model, on a red -> orange -> green
    scale whose stops sit on the report's band thresholds (red <0.80,
    orange ~0.80-0.95, green >=0.95): 'safety holds across sizes' reads as a
    wall of green, and any weak cell glows orange/red. Within each domain
    block, rows are ordered by the largest family model's score (best
    first)."""
    anchor = fd.anchor
    models = fd.family
    tasks = []
    for sec in F.SECTION_ORDER:
        tasks += sorted(
            fd.section_tasks(sec),
            key=lambda tn: -(s if (s := fd.score(anchor, tn)) is not None else -1))
    M = np.full((len(tasks), len(models)), np.nan)
    for j, e in enumerate(models):
        for i, tn in enumerate(tasks):
            s = fd.score(e, tn)
            if s is not None:
                M[i, j] = s
    fig, ax = plt.subplots(figsize=(1.6 + 1.1 * len(models), 0.148 * len(tasks) + 1.4))
    vmin, vmax = 0.3, 1.0
    stop = lambda v: (v - vmin) / (vmax - vmin)
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "band_scale", [(0.0, HARM), (stop(0.80), WARN),
                       (stop(0.95), SAFE), (1.0, "#4e9e7b")])
    cmap.set_bad("#e8e8e8")
    im = ax.imshow(M, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([e.label for e in models], fontsize=8, rotation=20, ha="right")
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([F.pretty_task(t) for t in tasks], fontsize=5.0)
    # domain separators + labels on the right edge
    bounds, start = [], 0
    for sec in F.SECTION_ORDER:
        k = len(fd.section_tasks(sec))
        if not k:
            continue
        bounds.append((start, start + k, L.SECTIONS[sec]["title"]))
        start += k
    for s0, s1, title in bounds:
        if s0:
            ax.axhline(s0 - 0.5, color="white", lw=1.6)
        ax.annotate(title, (len(models) - 0.42, (s0 + s1 - 1) / 2),
                    fontsize=6, color=INK, va="center", ha="left",
                    annotation_clip=False)
    ax.grid(visible=False)
    # horizontal colorbar below the plot: never collides with the
    # right-edge domain labels regardless of model count
    cb = fig.colorbar(im, ax=ax, orientation="horizontal",
                      fraction=0.018, pad=0.075, aspect=30)
    cb.set_label("Score (red < 0.80 ≤ orange < 0.95 ≤ green)", fontsize=8)
    save(fig, "fam_heatmap")


def score_hist(fd: FamilyData):
    import math
    models = fd.family
    n = len(models)
    ncol = 2 if n > 1 else 1
    nrow = math.ceil(n / ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(5.4 * ncol, 3.0 * nrow),
                             sharey=True, sharex=True, squeeze=False)
    bins = [i / 20 for i in range(21)]
    for ax, e in zip(axes.flat, models):
        scores = [t.score for t in e.tasks.values() if t.bucket == "main"]
        ax.hist(scores, bins=bins, color=e.color if n > 1 else ACCENT,
                edgecolor="white")
        mean = sum(scores) / len(scores)
        ax.axvline(mean, color=HARM, ls="--", lw=1.4)
        ax.annotate(f"mean {mean:.3f}", (mean, 0.92),
                    xycoords=("data", "axes fraction"),
                    xytext=(-6, 0), textcoords="offset points",
                    ha="right", fontsize=9, color=HARM)
        ax.set_title(e.label, fontsize=10)
    for ax in list(axes.flat)[n:]:        # hide any empty panel (odd model count)
        ax.set_visible(False)
    for c in range(ncol):                 # x-label + ticks on the lowest visible panel/col
        for r in range(nrow - 1, -1, -1):
            if axes[r, c].get_visible():
                axes[r, c].set_xlabel("Task score")
                # sharex hides tick labels off the bottom row; re-enable them on
                # a panel that became the lowest of its column via a hidden cell
                axes[r, c].tick_params(labelbottom=True)
                break
    for r in range(nrow):                 # y-label on the left column
        axes[r, 0].set_ylabel("Tasks")
    fig.tight_layout()
    save(fig, "fam_score_hist")


def _grouped_by_category(fd: FamilyData, cats: list[str], value_fn, fname: str,
                         xlabel: str, pretty=None, models=None, xmax=1.12,
                         value_fmt="{:.3f}"):
    """Horizontal grouped bars: categories x models (the family chart analog of
    generate_report's _grouped_bar). value_fn(entry, cat) -> float | None."""
    models = models or fd.family
    n = len(models)
    height = 0.8 / n
    ypos = np.arange(len(cats))[::-1]
    fig, ax = plt.subplots(figsize=(7.2, (0.34 + 0.24 * n) * len(cats) + 1.1))
    for i, e in enumerate(models):
        vals = [value_fn(e, c) for c in cats]
        shown = [0 if v is None else v for v in vals]
        yy = ypos + (n - 1 - i - (n - 1) / 2) * height
        ax.barh(yy, shown, height=height * 0.92,
                color=bar_colors(fd, e, shown, n_models=n),
                edgecolor="white", linewidth=1.0, label=e.label if n > 1 else None)
        for y, v in zip(yy, vals):
            if v is not None:
                ax.text(v + xmax * 0.008, y, value_fmt.format(v), va="center",
                        fontsize=7.5, color=INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels([pretty.get(c, c) if pretty else c for c in cats], fontsize=9)
    ax.set_xlim(0, xmax)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    if n > 1:
        ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0),
                  ncol=min(n, 3), fontsize=8.5)
    else:
        ax.set_title(models[0].label, fontsize=10, loc="left")
    save(fig, fname)


def by_attack(fd: FamilyData):
    models = fd.family
    cats = sorted({k for e in models for k in e.agg["by_attack"]})
    _grouped_by_category(
        fd, cats, lambda e, c: e.agg["by_attack"].get(c), "fam_by_attack",
        "Mean score (higher is better)", models=models,
        pretty={c: F.pretty_attack(c) for c in cats})


def harm_failures(fd: FamilyData):
    # models with no evaluations data (e.g. judging not finished) are skipped
    counts, models = {}, []
    for e in fd.family:
        cc = F.harm_failures(e)
        if cc:
            counts[e.key] = cc
            models.append(e)
        else:
            print(f"  (no evaluations data for {e.key} — omitted from fam_harm_failures)")
    if not models:
        print("  (no harm-category data for any model — skipping fam_harm_failures)")
        return
    cats = sorted({c for cc in counts.values() for c in cc},
                  key=lambda c: -max(cc.get(c, 0) for cc in counts.values()))
    xmax = max(max(cc.values()) for cc in counts.values()) * 1.18
    n = len(models)
    height = 0.8 / n
    ypos = np.arange(len(cats))[::-1]
    fig, ax = plt.subplots(figsize=(7.2, (0.34 + 0.24 * n) * len(cats) + 1.1))
    for i, e in enumerate(models):
        vals = [counts[e.key].get(c, 0) for c in cats]
        yy = ypos + (n - 1 - i - (n - 1) / 2) * height
        # harm counts stay in the reserved harm red for a single model
        ax.barh(yy, vals, height=height * 0.92,
                color=HARM if n == 1 else e.color,
                edgecolor="white", linewidth=1.0, label=e.label if n > 1 else None)
        for y, v in zip(yy, vals):
            ax.text(v + xmax * 0.008, y, str(v), va="center", fontsize=7.5, color=INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels([L.RISK_TYPE_PRETTY.get(c, c) for c in cats], fontsize=9)
    ax.set_xlim(0, xmax)
    ax.set_xlabel("Harmful responses (count, main suite)")
    ax.grid(axis="y", visible=False)
    if n > 1:
        ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0),
                  ncol=min(n, 3), fontsize=8.5)
    else:
        ax.set_title(models[0].label, fontsize=10, loc="left")
    save(fig, "fam_harm_failures")


def uae(fd: FamilyData):
    # family + version comparisons (e.g. V2); frontier lives in its own chart
    models = fd.family + fd.comparisons
    _grouped_by_category(
        fd, fd.uae_tasks(), lambda e, t: fd.score(e, t), "fam_uae",
        "Score (higher is better)", models=models,
        pretty={t: F.pretty_task(t) for t in fd.uae_tasks()})


def uae_frontier(fd: FamilyData):
    # separate frontier edition: anchor vs the frontier models that ran UAE
    models = [fd.anchor] + [
        b for b in fd.frontier
        if any(fd.score(b, t) is not None for t in fd.uae_tasks())]
    if len(models) < 2:
        print("  (no frontier model ran the UAE tasks — skipping fam_frontier_uae)")
        return
    _grouped_by_category(
        fd, fd.uae_tasks(), lambda e, t: fd.score(e, t), "fam_frontier_uae",
        "Score (higher is better)", models=models,
        pretty={t: F.pretty_task(t) for t in fd.uae_tasks()})


def multilingual(fd: FamilyData):
    models = fd.family + fd.comparisons
    _grouped_by_category(
        fd, fd.multilingual_tasks(), lambda e, t: fd.score(e, t),
        "fam_multilingual", "Score (higher is better)", models=models,
        pretty={t: F.pretty_task(t) for t in fd.multilingual_tasks()})


def thinking_divergence(fd: FamilyData):
    data = [(e, F.thinking_totals(e)) for e in fd.family]
    data = [(e, t) for e, t in data if t]
    if not data:
        print("  (no thinking_csv configured for any model — skipping "
              "fam_thinking_divergence)")
        return
    cats = [("thinking_harmful_rate", "Thinking\nharmful"),
            ("answer_harmful_rate", "Final answer\nharmful"),
            ("thinking_only_rate", "Divergent:\nthinking only"),
            ("answer_only_rate", "Divergent:\nanswer only")]
    n = len(data)
    width = 0.8 / n
    xpos = np.arange(len(cats))
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    for i, (e, tot) in enumerate(data):
        vals = [tot[c] * 100 for c, _ in cats]
        xx = xpos + (i - (n - 1) / 2) * width
        ax.bar(xx, vals, width * 0.92, color=e.color if n > 1 else ACCENT,
               edgecolor="white", linewidth=1.0, label=e.label if n > 1 else None)
        for x, v in zip(xx, vals):
            ax.annotate(f"{v:.2f}%", (x, v), textcoords="offset points",
                        xytext=(0, 3), ha="center", fontsize=8, color=INK)
    ax.set_xticks(xpos)
    ax.set_xticklabels([lab for _, lab in cats], fontsize=9)
    ax.set_ylabel("% of responses (65 safety tasks)")
    if n > 1:
        ax.legend(frameon=False, fontsize=8.5)
    else:
        ax.set_title(data[0][0].label, fontsize=10, loc="left")
    save(fig, "fam_thinking_divergence")


def attack_scaling(fd: FamilyData):
    """Which attack surfaces improve fastest with scale — the family report's
    core question, as small multiples of attack-tag mean vs size."""
    import math
    fam, xs, is_size = sizes_axis(fd)
    tags = sorted({k for e in fam for k in e.agg["by_attack"]})
    ncol = 2 if len(tags) > 1 else 1
    nrow = math.ceil(len(tags) / ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(5.0 * ncol, 2.7 * nrow),
                             sharex=True, sharey=True, squeeze=False)
    lab = [f"{e.size_b:g}B" for e in fam] if is_size else [e.label for e in fam]
    # shared-y floor from the data: a fixed floor silently clips any small
    # model that scores below it
    all_ys = [y for e in fam for t in tags
              if (y := e.agg["by_attack"].get(t)) is not None]
    ymin = min(0.5, max(0.0, min(all_ys) - 0.06))
    for ax, tag in zip(axes.flat, tags):
        ys = [e.agg["by_attack"].get(tag) for e in fam]
        ax.plot(xs, ys, marker="o", ms=5, lw=1.8, color=ACCENT)
        for x, y in zip(xs, ys):
            if y is not None:
                ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points",
                            xytext=(0, 7), ha="center", fontsize=8, color=INK)
        ax.set_title(F.pretty_attack(tag), fontsize=10)
        ax.set_ylim(ymin, 1.06)
        # scale FIRST: set_xscale resets the tick locator to log decades,
        # which silently discards fixed ticks set before it
        if is_size:
            ax.set_xscale("log")
        ax.set_xticks(xs)
    for ax in list(axes.flat)[len(tags):]:           # hide empty panels
        ax.set_visible(False)
    for c in range(ncol):                            # x-labels on lowest visible row
        for r in range(nrow - 1, -1, -1):
            if axes[r, c].get_visible():
                axes[r, c].set_xticklabels(lab, fontsize=8, rotation=20, ha="right")
                axes[r, c].tick_params(labelbottom=True)
                break
    for r in range(nrow):                            # y-label on left column
        axes[r, 0].set_ylabel("Mean score")
    fig.supxlabel("Model size (parameters)" if is_size else "Model", fontsize=10)
    fig.tight_layout()
    save(fig, "fam_attack_scaling")


def harm_shares(fd: FamilyData):
    """Failure profile: each risk category as % of the model's own harmful
    responses — comparable across models with different failure totals."""
    shares, models = {}, []
    for e in fd.family:
        cc = F.harm_failures(e)
        if cc:
            shares[e.key] = F.harm_shares(cc)
            models.append(e)
    if not models:
        print("  (no harm-category data — skipping fam_harm_shares)")
        return
    cats = sorted({c for s in shares.values() for c in s},
                  key=lambda c: -max(s.get(c, 0) for s in shares.values()))
    _grouped_by_category(
        fd, cats, lambda e, c: (shares[e.key].get(c, 0.0) * 100
                                if e.key in shares else None),
        "fam_harm_shares", "Share of the model's harmful responses (%)",
        pretty={c: L.RISK_TYPE_PRETTY.get(c, c) for c in cats},
        models=models,
        xmax=max(v for s in shares.values() for v in s.values()) * 100 * 1.2,
        value_fmt="{:.1f}%")


def task_slopes(fd: FamilyData):
    """Range ("dumbbell") plot of the tasks the models most disagree on: one row
    per task, a grey bar spanning the lowest-to-highest model score, one coloured
    dot per model. Replaces the old crossing-lines slopegraph — reads far
    cleaner and puts the biggest cross-model gaps at the top."""
    if len(fd.family) < 2:
        print("  (needs >=2 family models — skipping fam_task_slopes)")
        return
    ranges = []
    for tn in fd.main_tasks:
        ss = [fd.score(e, tn) for e in fd.family]
        if any(s is None for s in ss):
            continue
        ranges.append((max(ss) - min(ss), tn, ss))
    ranges.sort(key=lambda r: -r[0])
    top = ranges[:12][::-1]                       # largest spread ends up on top
    ypos = np.arange(len(top))
    fig, ax = plt.subplots(figsize=(7.2, 0.42 * len(top) + 1.4))
    for y, (rng, tn, ss) in zip(ypos, top):       # spread bar (min -> max)
        ax.plot([min(ss), max(ss)], [y, y], color="#c9ccd1", lw=2.4, zorder=1,
                solid_capstyle="round")
    # reversed draw order: the anchor's dot stays on top of near-ties
    for i, e in reversed(list(enumerate(fd.family))):   # one dot per model
        ax.scatter([top[j][2][i] for j in range(len(top))], ypos, s=48,
                   color=e.color, edgecolor="white", linewidth=0.8,
                   zorder=3, label=e.label)
    ax.set_yticks(ypos)
    ax.set_yticklabels([F.pretty_task(tn) for _, tn, _ in top], fontsize=8)
    allv = [v for _, _, ss in top for v in ss]
    ax.set_xlim(max(0.0, min(allv) - 0.04), 1.02)
    ax.set_xlabel("Task score  (dot = model; grey bar = spread across models)")
    ax.grid(axis="y", visible=False)
    handles, hlabels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], hlabels[::-1], frameon=False, loc="lower left",
              bbox_to_anchor=(0, 1.0), ncol=min(len(fd.family), 4), fontsize=8.5)
    save(fig, "fam_task_slopes")


def uae_controversial(fd: FamilyData):
    """The judge-field breakdown that corrected the V3 headline: refusal rate,
    fully-neutral engagement, and context-given-engagement, per model."""
    data, models = {}, []
    for e in fd.family:
        b = F.uae_controversial_breakdown(e)
        if b:
            data[e.key] = b
            models.append(e)
    if not models:
        print("  (no uae_controversial evaluations — skipping fam_uae_controversial)")
        return
    cats = [("refusal_rate", "Refuses\noutright"),
            ("neutral_engaged_rate", "Engages,\nfully neutral"),
            ("context_rate", "Provides\ncontext")]
    n = len(models)
    width = 0.8 / n
    xpos = np.arange(len(cats))
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for i, e in enumerate(models):
        vals = [(data[e.key][c] or 0) * 100 for c, _ in cats]
        xx = xpos + (i - (n - 1) / 2) * width
        ax.bar(xx, vals, width * 0.92, color=e.color if n > 1 else ACCENT,
               edgecolor="white", linewidth=1.0, label=e.label if n > 1 else None)
        for x, v in zip(xx, vals):
            ax.annotate(f"{v:.0f}%", (x, v), textcoords="offset points",
                        xytext=(0, 3), ha="center", fontsize=8, color=INK)
    ax.set_xticks(xpos)
    ax.set_xticklabels([lab for _, lab in cats], fontsize=9)
    ax.set_ylabel("% of controversial prompts")
    ax.set_ylim(0, 108)
    if n > 1:
        ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0),
                  ncol=min(n, 3), fontsize=8.5)
    else:
        ax.set_title(models[0].label, fontsize=10, loc="left")
    save(fig, "fam_uae_controversial")


def version_comparison(fd: FamilyData):
    """Anchor (largest family model) vs prior version(s), mean score by domain —
    grouped horizontal bars with each model's identity color."""
    if not fd.comparisons:
        print("  (no comparison models — skipping fam_version_comparison)")
        return
    models = [fd.anchor] + fd.comparisons
    secs = F.SECTION_ORDER
    labels = [L.SECTIONS[s]["title"] for s in secs]
    n = len(models)
    height = 0.8 / n
    ypos = np.arange(len(secs))[::-1]
    fig, ax = plt.subplots(figsize=(7.6, 0.62 * len(secs) + 1.3))
    for i, e in enumerate(models):
        vals = [fd.section_mean(e, s) or 0 for s in secs]
        yy = ypos + (n - 1 - i - (n - 1) / 2) * height
        ax.barh(yy, vals, height=height * 0.9, color=e.color,
                edgecolor="white", linewidth=1.0, label=e.label)
        for y, v in zip(yy, vals):
            ax.text(v + 0.008, y, f"{v:.2f}", va="center", fontsize=7, color=INK)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(0, 1.12)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("Mean score (higher is better)")
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0),
              ncol=min(n, 3), fontsize=8.5)
    save(fig, "fam_version_comparison")


def version_movers(fd: FamilyData):
    """Per-task differences, anchor vs first comparison, as a diverging bar chart
    (blue = anchor better, red = prior version better) — ALL shared main tasks,
    sorted by delta."""
    if not fd.comparisons:
        print("  (no comparison models — skipping fam_version_movers)")
        return
    anchor, comp = fd.anchor, fd.comparisons[0]
    rows = []
    for tn in fd.main_tasks:
        a, b = fd.score(anchor, tn), fd.score(comp, tn)
        if a is not None and b is not None:
            rows.append((tn, a - b))
    rows.sort(key=lambda r: r[1])              # most negative (prior better) at bottom
    ypos = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(7.4, 0.17 * len(rows) + 1.0))
    colors = [ACCENT if d >= 0 else HARM for _, d in rows]
    ax.barh(ypos, [d for _, d in rows], color=colors, edgecolor="white", linewidth=0.5)
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_yticks(ypos)
    ax.set_yticklabels([F.pretty_task(tn) for tn, _ in rows], fontsize=5.2)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.margins(y=0)
    ax.set_xlabel(f"Score delta ({anchor.label} $-$ {comp.label})")
    ax.set_title(f"All {len(rows)} shared tasks — "
                 f"blue: {anchor.label} better · red: {comp.label} better",
                 fontsize=8.5, loc="left", color=INK)
    ax.grid(axis="y", visible=False)
    save(fig, "fam_version_movers")


if __name__ == "__main__":
    fd = FamilyData()
    # Clear stale figures first: some charts are conditional (comparison, UAE,
    # thinking-divergence). Without this, a chart skipped on this run would leave
    # its previous PNG behind and the existence-aware figs.tex would still include
    # it — showing outdated data (e.g. a version-comparison figure after the
    # comparison models were removed).
    import glob as _glob
    for _p in _glob.glob(os.path.join(FIGS, "fam_*.png")) + \
            _glob.glob(os.path.join(FIGS, "fam_*.pdf")):
        os.remove(_p)
    print(f"charts for: {[e.label for e in fd.family]}"
          f"  frontier: {[e.label for e in fd.frontier]}"
          f"  comparisons: {[e.label for e in fd.comparisons]}")
    radar(fd)
    scaling_overall(fd)
    scaling_domains(fd)
    domain_bars(fd)                                      # sampling-noise CI
    domain_bars(fd, ci_fn=F.mean_se_between, name="fam_domain_bars_div",
                ci_note="95% CI, task spread")           # between-task divergence CI
    tradeoff(fd)
    heatmap(fd)
    score_hist(fd)
    by_attack(fd)
    harm_failures(fd)
    harm_shares(fd)
    uae(fd)
    uae_controversial(fd)
    multilingual(fd)
    thinking_divergence(fd)
    attack_scaling(fd)
    task_slopes(fd)
    version_comparison(fd)
    version_movers(fd)
    # separate frontier-comparison edition: the family anchor vs the external
    # frontier reference models (they never appear in the family charts above)
    if fd.frontier:
        frontier_models = [fd.anchor] + fd.frontier
        # condensed-report edition: predecessor (solid unfilled) + frontier
        # (dashed) around the anchor, radial axis pinned to the family radar's
        # 0.1 floor so the two radars share a scale side by side
        radar(fd, name="fam_frontier_radar",
              models=[fd.anchor] + fd.comparisons + fd.frontier, rmin=0.1)
        domain_bars(fd, name="fam_frontier_domain_bars", models=frontier_models)
        uae_frontier(fd)
    print("done.")
