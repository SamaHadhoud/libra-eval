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
SAFE = "#2f9e6f"      # green  — score band >= 0.95 / "safe"
WARN = "#e08a1e"      # amber  — score band 0.80-0.95
HARM = "#d1495b"      # red    — score band < 0.80; reserved for harm counts
ACCENT = "#3b6ea5"


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
    p = os.path.join(FIGS, f"{name}.png")
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote figures/{name}.png")


def sizes_axis(fd: FamilyData):
    """x positions: true sizes when all known (log scale), else ordinal."""
    if all(e.size_b for e in fd.family):
        return [e.size_b for e in fd.family], True
    return list(range(1, len(fd.family) + 1)), False


def scaling_overall(fd: FamilyData):
    xs, is_size = sizes_axis(fd)
    means = [e.agg["mean_score"] for e in fd.family]
    safety = [e.agg["weighted_safety"] for e in fd.family]
    # 95% uncertainty: SEM across tasks for the mean; Wilson for the pooled rate
    mean_ci = [F.mean_se(e, [t for t in fd.main_tasks if t in e.tasks]) or 0
               for e in fd.family]
    saf_ci = [F.wilson_halfwidth(e.agg["weighted_safety"], e.agg["weighted_total"])
              for e in fd.family]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for ys, cis, label, color, mk in [
            (means, mean_ci, "Mean task score", "#3b6ea5", "o"),
            (safety, saf_ci, "Sample-weighted safety rate", SAFE, "s")]:
        ax.plot(xs, ys, marker=mk, ms=7, lw=2, color=color, label=label, zorder=3)
        if len(xs) > 1:
            ax.fill_between(xs, [y - c for y, c in zip(ys, cis)],
                            [y + c for y, c in zip(ys, cis)],
                            color=color, alpha=0.15, lw=0)
        else:
            ax.errorbar(xs, ys, yerr=cis, fmt="none", ecolor=color,
                        elinewidth=1.2, capsize=4)
        for x, y in zip(xs, ys):
            ax.annotate(f"{y:.3f}", (x, y), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=8.5, color=INK)
    if is_size:
        ax.set_xscale("log")
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{e.size_b:g}B" for e in fd.family])
    else:
        ax.set_xticks(xs)
        ax.set_xticklabels([e.label for e in fd.family], fontsize=8)
    ax.set_xlabel("Model size (parameters)")
    ax.set_ylabel("Score (higher is better)")
    lo = min(min(means), min(safety))
    ax.set_ylim(max(0.0, lo - 0.05), 1.02)
    ax.legend(frameon=False, loc="lower right")
    save(fig, "fam_scaling_overall")


def scaling_domains(fd: FamilyData):
    xs, is_size = sizes_axis(fd)
    secs = F.SECTION_ORDER
    fig, axes = plt.subplots(2, 5, figsize=(13, 5.2), sharex=True, sharey=True)
    for ax, sec in zip(axes.flat, secs):
        ys = [fd.section_mean(e, sec) for e in fd.family]
        ax.plot(xs, ys, marker="o", ms=5, lw=1.8, color="#3b6ea5")
        for x, y in zip(xs, ys):
            if y is not None:
                ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points",
                            xytext=(0, 7), ha="center", fontsize=7.5, color=INK)
        ax.set_title(L.SECTIONS[sec]["title"], fontsize=8.5)
        ax.set_ylim(0.4, 1.05)
        if is_size:
            ax.set_xscale("log")
            ax.set_xticks(xs)
            ax.set_xticklabels([f"{e.size_b:g}B" for e in fd.family], fontsize=7.5)
        else:
            ax.set_xticks(xs)
            ax.set_xticklabels([e.label for e in fd.family],
                               fontsize=6.5, rotation=30, ha="right")
    fig.supxlabel("Model size (parameters)", fontsize=10)
    fig.supylabel("Domain mean score", fontsize=10)
    fig.tight_layout()
    save(fig, "fam_scaling_domains")


def domain_bars(fd: FamilyData):
    """N=1: band-colored bars (V3-report look). N>=2: Cleveland dot plot —
    one row per domain, one dot per model, CI whiskers; scales to 5+ models
    where grouped bars turn to mush."""
    secs = F.SECTION_ORDER
    labels = [L.SECTIONS[s]["title"] for s in secs]
    n = len(fd.family)
    ypos = np.arange(len(secs))[::-1]
    if n == 1:
        e = fd.family[0]
        vals = [fd.section_mean(e, s) or 0 for s in secs]
        cis = [F.mean_se(e, fd.section_tasks(s)) or 0 for s in secs]
        fig, ax = plt.subplots(figsize=(7.2, 0.62 * len(secs) + 1.2))
        ax.barh(ypos, vals, height=0.74, color=bar_colors(fd, e, vals),
                edgecolor="white", linewidth=1.0,
                xerr=cis, error_kw=dict(ecolor=INK, elinewidth=0.9, capsize=2.5))
        for y, v, c in zip(ypos, vals, cis):
            ax.text(v + c + 0.01, y, f"{v:.3f}", va="center", fontsize=7.5, color=INK)
        ax.set_xlim(0, 1.12)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_title(e.label, fontsize=10, loc="left")
    else:
        fig, ax = plt.subplots(figsize=(7.2, 0.52 * len(secs) + 1.4))
        for y in ypos:
            ax.axhline(y, color="#e3e3e0", lw=0.9, zorder=1)
        for e in fd.family:
            vals = [fd.section_mean(e, s) for s in secs]
            cis = [F.mean_se(e, fd.section_tasks(s)) or 0 for s in secs]
            ax.errorbar(vals, ypos, xerr=cis, fmt="none", ecolor=e.color,
                        elinewidth=1.1, capsize=0, alpha=0.55, zorder=2)
            ax.scatter(vals, ypos, s=58, color=e.color, zorder=3,
                       edgecolor="white", linewidth=1.0, label=e.label)
        lo = min(min(fd.section_mean(e, s) or 1 for s in secs) for e in fd.family)
        ax.set_xlim(max(0, lo - 0.08), 1.02)
        ax.set_xlabel("Mean score (95% CI whiskers)")
        ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0),
                  ncol=min(n, 3), fontsize=8.5)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=9)
    if n == 1:
        ax.set_xlabel("Mean score (higher is better; 95% CI)")
    ax.grid(axis="y", visible=False)
    save(fig, "fam_domain_bars")


def tradeoff(fd: FamilyData):
    fig, ax = plt.subplots(figsize=(5.4, 4.4))
    xs = [fd.section_mean(e, "over_refusal") for e in fd.family]
    ys = [fd.section_mean(e, "jailbreak") for e in fd.family]
    # trajectory in size order: does scale buy robustness, helpfulness, or both?
    for (x0, y0), (x1, y1) in zip(list(zip(xs, ys))[:-1], list(zip(xs, ys))[1:]):
        ax.annotate("", (x1, y1), (x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color="#9aa0a6",
                                    lw=1.4, shrinkA=8, shrinkB=8))
    for e, x, y in zip(fd.family, xs, ys):
        ax.scatter([x], [y], s=90, color=e.color, zorder=3,
                   edgecolor="white", linewidth=1.2)
        ax.annotate(e.label, (x, y), textcoords="offset points",
                    xytext=(8, 6), fontsize=8.5, color=INK)
    pad = 0.04
    ax.set_xlim(min(xs) - pad, max(xs) + pad + 0.06)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)
    ax.set_xlabel("Over-refusal domain mean\n(compliance on benign prompts — higher is better)")
    ax.set_ylabel("Jailbreak-robustness domain mean")
    save(fig, "fam_tradeoff")


def heatmap(fd: FamilyData):
    """Absolute scores for every model, on a red -> orange -> green scale whose
    stops sit on the report's band thresholds (red <0.80, orange ~0.80-0.95,
    green >=0.95): 'safety holds across sizes' reads as a wall of green, and
    any weak cell glows orange/red. Within each domain block, rows are ordered
    by the largest model's score (best first), so blocks fade green -> orange
    and each domain's weak tasks collect at its block bottom."""
    anchor = fd.family[-1]
    tasks = []
    for sec in F.SECTION_ORDER:
        tasks += sorted(
            fd.section_tasks(sec),
            key=lambda tn: -(s if (s := fd.score(anchor, tn)) is not None else -1))
    M = np.full((len(tasks), len(fd.family)), np.nan)
    for j, e in enumerate(fd.family):
        for i, tn in enumerate(tasks):
            s = fd.score(e, tn)
            if s is not None:
                M[i, j] = s
    fig, ax = plt.subplots(figsize=(1.6 + 1.1 * len(fd.family), 0.148 * len(tasks) + 1.4))
    vmin, vmax = 0.3, 1.0
    stop = lambda v: (v - vmin) / (vmax - vmin)
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "band_scale", [(0.0, HARM), (stop(0.80), WARN),
                       (stop(0.95), SAFE), (1.0, "#1e6b4a")])
    cmap.set_bad("#e8e8e8")
    im = ax.imshow(M, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(fd.family)))
    ax.set_xticklabels([e.label for e in fd.family], fontsize=8, rotation=20, ha="right")
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels(tasks, fontsize=4.6, family="monospace")
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
        ax.annotate(title, (len(fd.family) - 0.42, (s0 + s1 - 1) / 2),
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
    n = len(fd.family)
    fig, axes = plt.subplots(1, n, figsize=(4.6 * n, 3.2), sharey=True, squeeze=False)
    bins = [i / 20 for i in range(21)]
    for ax, e in zip(axes.flat, fd.family):
        scores = [t.score for t in e.tasks.values() if t.bucket == "main"]
        ax.hist(scores, bins=bins, color=e.color if n > 1 else ACCENT,
                edgecolor="white")
        mean = sum(scores) / len(scores)
        ax.axvline(mean, color=HARM, ls="--", lw=1.4)
        ax.annotate(f"mean {mean:.3f}", (mean, ax.get_ylim()[1] * 0.92),
                    xytext=(-6, 0), textcoords="offset points",
                    ha="right", fontsize=8.5, color=HARM)
        ax.set_title(e.label, fontsize=9.5)
        ax.set_xlabel("Task score")
    axes.flat[0].set_ylabel("Tasks")
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
    cats = sorted({k for e in fd.family for k in e.agg["by_attack"]})
    _grouped_by_category(
        fd, cats, lambda e, c: e.agg["by_attack"].get(c), "fam_by_attack",
        "Mean score (higher is better)",
        pretty={c: c.replace("_", " ") for c in cats})


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
    # family + version comparisons (e.g. V2) + baselines that ran UAE
    models = fd.family + fd.comparisons + [
        b for b in fd.baselines
        if any(fd.score(b, t) is not None for t in fd.uae_tasks())]
    _grouped_by_category(
        fd, fd.uae_tasks(), lambda e, t: fd.score(e, t), "fam_uae",
        "Score (higher is better)", models=models)


def multilingual(fd: FamilyData):
    models = fd.family + fd.comparisons
    _grouped_by_category(
        fd, fd.multilingual_tasks(), lambda e, t: fd.score(e, t),
        "fam_multilingual", "Score (higher is better)", models=models)


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
    xs, is_size = sizes_axis(fd)
    tags = sorted({k for e in fd.family for k in e.agg["by_attack"]})
    fig, axes = plt.subplots(1, len(tags), figsize=(2.6 * len(tags), 2.9),
                             sharex=True, sharey=True, squeeze=False)
    for ax, tag in zip(axes.flat, tags):
        ys = [e.agg["by_attack"].get(tag) for e in fd.family]
        ax.plot(xs, ys, marker="o", ms=5, lw=1.8, color=ACCENT)
        for x, y in zip(xs, ys):
            if y is not None:
                ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points",
                            xytext=(0, 7), ha="center", fontsize=7.5, color=INK)
        ax.set_title(tag.replace("_", " "), fontsize=9)
        ax.set_ylim(0.5, 1.06)
        if is_size:
            ax.set_xscale("log")
            ax.set_xticks(xs)
            ax.set_xticklabels([f"{e.size_b:g}B" for e in fd.family], fontsize=7.5)
        else:
            ax.set_xticks(xs)
            ax.set_xticklabels([e.label for e in fd.family],
                               fontsize=6.5, rotation=30, ha="right")
    axes.flat[0].set_ylabel("Mean score")
    fig.supxlabel("Model size (parameters)", fontsize=10)
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
    """Slopegraph of the ~15 most size-sensitive tasks: score vs size, one line
    per task. Shows the non-monotonic behavior an endpoint delta hides."""
    if len(fd.family) < 2:
        print("  (needs >=2 family models — skipping fam_task_slopes)")
        return
    xs, is_size = sizes_axis(fd)
    ranges = []
    for tn in fd.main_tasks:
        ss = [fd.score(e, tn) for e in fd.family]
        if any(s is None for s in ss):
            continue
        ranges.append((max(ss) - min(ss), tn, ss))
    ranges.sort(key=lambda r: -r[0])
    top = ranges[:15]
    fig, ax = plt.subplots(figsize=(7.0, 5.6))
    # dodge right-edge labels: enforce a minimum vertical gap in data coords
    ends = sorted(range(len(top)), key=lambda k: top[k][2][-1])
    ys_lab, min_gap = {}, 0.016
    prev = -1e9
    for k in ends:
        y = max(top[k][2][-1], prev + min_gap)
        ys_lab[k] = y
        prev = y
    for k, (rng, tn, ss) in enumerate(top):
        emph = k < 5
        ax.plot(xs, ss, marker="o", ms=4 if emph else 3,
                lw=1.9 if emph else 1.1,
                color=ACCENT if emph else "#9fb2c9",
                alpha=1.0 if emph else 0.8, zorder=3 if emph else 2)
        ax.annotate(tn, (xs[-1], ss[-1]), xytext=(xs[-1] * 1.14, ys_lab[k]),
                    fontsize=6.8, va="center",
                    color=INK if emph else "#6b7482", family="monospace",
                    arrowprops=dict(arrowstyle="-", color="#d5d9df", lw=0.6,
                                    shrinkA=0, shrinkB=2))
    if is_size:
        ax.set_xscale("log")
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{e.size_b:g}B" for e in fd.family])
    else:
        ax.set_xticks(xs)
        ax.set_xticklabels([e.label for e in fd.family], fontsize=8)
    ax.set_xlim(min(xs) * 0.8, max(xs) * 3.2)  # room for right-edge labels
    ax.set_ylim(top=max(1.02, max(ys_lab.values()) + 0.02))  # dodged labels fit
    ax.set_xlabel("Model size (parameters)")
    ax.set_ylabel("Task score")
    ax.set_title("Most size-sensitive tasks (top 5 emphasized)",
                 fontsize=10, loc="left")
    save(fig, "fam_task_slopes")


def uae_controversial(fd: FamilyData):
    """The judge-field breakdown that corrected the V3 headline: refusal rate,
    fully-neutral engagement, and context-given-engagement, per model."""
    data, models = {}, []
    for e in fd.family + fd.baselines:
        b = F.uae_controversial_breakdown(e)
        if b:
            data[e.key] = b
            models.append(e)
    if not models:
        print("  (no uae_controversial evaluations — skipping fam_uae_controversial)")
        return
    cats = [("refusal_rate", "Refuses\noutright"),
            ("neutral_engaged_rate", "Engages,\nfully neutral"),
            ("context_given_engaged", "Provides context\n(of engaged)")]
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
    ax.set_yticklabels([tn for tn, _ in rows], fontsize=5.2, family="monospace")
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
    print(f"charts for: {[e.label for e in fd.family]}"
          f"  comparisons: {[e.label for e in fd.comparisons]}")
    scaling_overall(fd)
    scaling_domains(fd)
    domain_bars(fd)
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
    print("done.")
