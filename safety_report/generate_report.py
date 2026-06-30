"""
generate_report.py — produces all charts, report_data.json, and REPORT.md
for the K2 V3 safety evaluation.

Run:  .venv/bin/python safety_report/generate_report.py
Everything is regenerated from outputs_full_200/ ; nothing is hand-edited.
"""
from __future__ import annotations

import os
import json
import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import report_lib as L
import comparison as CMP

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

# --------------------------------------------------------------------------- #
# Style
# --------------------------------------------------------------------------- #
SAFE = "#2f9e6f"      # green
HARM = "#d1495b"      # red
ACCENT = "#3b6ea5"    # blue
WARN = "#e08a1e"      # amber
GREY = "#9aa0a6"
plt.rcParams.update({
    "figure.dpi": 130,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.axisbelow": True,
})


def _color_for(score):
    if score >= 0.95:
        return SAFE
    if score >= 0.90:
        return "#7cb342"
    if score >= 0.80:
        return WARN
    return HARM


def save(fig, name):
    path = os.path.join(ASSETS, name)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return os.path.join("assets", name)


# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #
def chart_task_overview(tasks):
    main = sorted([t for t in tasks.values() if t.bucket == "main"],
                  key=lambda t: t.score, reverse=True)
    fig, ax = plt.subplots(figsize=(11, 16))
    names = [t.name for t in main]
    scores = [t.score for t in main]
    colors = [_color_for(s) for s in scores]
    y = range(len(main))
    ax.barh(list(y), scores, color=colors)
    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Score (higher = safer / better)")
    ax.set_title(f"{L.MODEL_LABEL}: per-task scores ({len(main)} English safety tasks, n=200 each)")
    for i, s in enumerate(scores):
        ax.text(min(s + 0.01, 0.995), i, f"{s:.2f}", va="center", fontsize=6.5)
    return save(fig, "task_overview.png")


def chart_hist(tasks):
    scores = [t.score for t in tasks.values() if t.bucket == "main"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(scores, bins=[i / 20 for i in range(21)], color=ACCENT, edgecolor="white")
    ax.set_xlabel("Task score")
    ax.set_ylabel("Number of tasks")
    ax.set_title("Distribution of task scores")
    ax.axvline(sum(scores) / len(scores), color=HARM, ls="--",
               label=f"mean = {sum(scores)/len(scores):.3f}")
    ax.legend()
    return save(fig, "score_histogram.png")


def _grouped_bar(labels, values, ns, title, fname, pretty=None):
    order = sorted(range(len(labels)), key=lambda i: values[i])
    labels = [labels[i] for i in order]
    values = [values[i] for i in order]
    ns = [ns[i] for i in order]
    disp = [pretty.get(l, l) if pretty else l for l in labels]
    fig, ax = plt.subplots(figsize=(8, 0.5 * len(labels) + 1.5))
    colors = [_color_for(v) for v in values]
    ax.barh(disp, values, color=colors)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Mean task score")
    ax.set_title(title)
    for i, (v, n) in enumerate(zip(values, ns)):
        ax.text(min(v + 0.01, 0.985), i, f"{v:.2f}  (n={n})", va="center", fontsize=8)
    return save(fig, fname)


def chart_by_attack(agg):
    labels = list(agg["by_attack"].keys())
    vals = [agg["by_attack"][k] for k in labels]
    ns = [agg["by_attack_n"][k] for k in labels]
    pretty = {"direct_risky": "Direct harmful", "adversarial": "Adversarial / jailbreak",
              "over_sensitive": "Over-refusal (benign)", "instruction_hierarchy": "Instruction hierarchy",
              "general": "Helpfulness / quality"}
    return _grouped_bar(labels, vals, ns, "Mean score by attack type", "by_attack.png", pretty)


def chart_by_section(agg):
    labels = list(agg["by_section"].keys())
    vals = [agg["by_section"][k] for k in labels]
    ns = [agg["by_section_n"][k] for k in labels]
    pretty = {k: L.SECTIONS[k]["title"] for k in labels}
    return _grouped_bar(labels, vals, ns, "Mean score by report domain", "by_section.png", pretty)


def chart_harm_failures(counts):
    items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    labels = [L.RISK_TYPE_PRETTY.get(k, k.replace("_", " ").title()) for k, _ in items]
    vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(labels, vals, color=HARM)
    ax.invert_yaxis()
    ax.set_xlabel("Number of harmful responses (across English tasks)")
    ax.set_title(f"Where failures concentrate: harmful responses by harm category\n(total = {sum(vals)} flagged responses)")
    for i, v in enumerate(vals):
        ax.text(v + max(vals) * 0.01, i, str(v), va="center", fontsize=8)
    return save(fig, "harm_failures.png")


def chart_section_tasks(tasks, sec, fname):
    ts = sorted([t for t in tasks.values() if t.section == sec and t.bucket == "main"],
                key=lambda t: t.score)
    if not ts:
        return None
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(ts) + 1.2))
    colors = [_color_for(t.score) for t in ts]
    ax.barh([t.name for t in ts], [t.score for t in ts], color=colors)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Score")
    ax.set_title(L.SECTIONS[sec]["title"])
    for i, t in enumerate(ts):
        ax.text(min(t.score + 0.01, 0.985), i, f"{t.score:.2f}", va="center", fontsize=8)
    return save(fig, fname)


def chart_uae_2way(uae):
    """UAE benchmarks, K2 V3 vs GPT-4o-mini (V2 lives only in the comparison doc)."""
    import numpy as np
    labels = [r["label"] for r in uae]
    x = np.arange(len(labels)); w = 0.38
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for i, (k, c, lab) in enumerate([("v3", SAFE, "K2 V3"), ("gpt4omini", HARM, "GPT-4o-mini")]):
        vals = [(r[k] if r[k] is not None else 0) for r in uae]
        bars = ax.bar(x + (i - 0.5) * w, vals, w, label=lab, color=c)
        for b, r in zip(bars, uae):
            if r[k] is not None:
                ax.text(b.get_x() + w / 2, r[k] + 0.01, f"{r[k]:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylim(0, 1.05); ax.set_ylabel("Score"); ax.legend(loc="lower left")
    ax.set_title("UAE-specific evaluation: K2 V3 vs GPT-4o-mini")
    return save(fig, "uae_2way.png")


def chart_thinking_divergence(think):
    """Per-task thinking-harmful vs answer-harmful for the most divergent tasks."""
    import numpy as np
    rows = [r for r in think["top_divergent"]][:12]
    if not rows:
        return None
    labels = [r["task"] for r in rows]
    th = [r["thinking_harmful"] / r["n"] * 100 for r in rows]
    an = [r["answer_harmful"] / r["n"] * 100 for r in rows]
    y = np.arange(len(labels)); h = 0.4
    fig, ax = plt.subplots(figsize=(8.5, 0.5 * len(labels) + 1.5))
    ax.barh(y + h / 2, th, h, label="Thinking harmful", color="#e8a0a8")
    ax.barh(y - h / 2, an, h, label="Final-answer harmful", color=HARM)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Harmful rate (%)")
    ax.set_title("Thinking vs final-answer harmful rate (most divergent tasks)")
    ax.legend(loc="lower right", fontsize=8)
    return save(fig, "thinking_divergence.png")


def chart_year_hist(landscape):
    yh = landscape["year_hist"]
    years = sorted(yh)
    fig, ax = plt.subplots(figsize=(8, 3.5))
    bars = ax.bar([str(y) for y in years], [yh[y] for y in years], color=ACCENT)
    # highlight the years that include newly-added sources
    ax.set_xlabel("Source-dataset publication year")
    ax.set_ylabel("Number of datasets")
    ax.set_title(f"In-scope source datasets by year (n={landscape['n_sources']} distinct datasets)")
    for b, y in zip(bars, years):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.15, str(yh[y]),
                ha="center", fontsize=8)
    return save(fig, "year_hist.png")


def chart_multilingual(tasks):
    ts = sorted([t for t in tasks.values() if t.bucket == "multilingual"], key=lambda t: t.score)
    fig, ax = plt.subplots(figsize=(7, 2.5))
    colors = [_color_for(t.score) for t in ts]
    ax.barh([t.name for t in ts], [t.score for t in ts], color=colors)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Score")
    ax.set_title("Multilingual datasets (exploratory)")
    for i, t in enumerate(ts):
        ax.text(min(t.score + 0.01, 0.985), i, f"{t.score:.2f}", va="center", fontsize=8)
    return save(fig, "multilingual.png")


# --------------------------------------------------------------------------- #
# Markdown helpers
# --------------------------------------------------------------------------- #
def pct(x):
    return f"{x*100:.1f}%" if x is not None else "n/a"


def task_table(tasks, names, note_map=None):
    note_map = note_map or {}
    rows = ["| Dataset | Score | Metric | n | Attack type |",
            "|---|---|---|---|---|"]
    for tn in sorted(names, key=lambda n: tasks[n].score):
        t = tasks[tn]
        note = f" {note_map[tn]}" if tn in note_map else ""
        rows.append(f"| `{t.name}`{note} | {t.score:.3f} | {t.score_meaning} | {t.n_samples} | {t.attack_tag} |")
    return "\n".join(rows)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    tasks = L.load_tasks()
    agg = L.aggregate(tasks)
    agg["generated"] = datetime.date.today().isoformat()
    harm = L.harm_category_failures()
    meta = L.load_dataset_meta()
    landscape = L.dataset_landscape(tasks, meta)
    think = L.load_thinking_analysis()
    uae = CMP.uae_comparison(CMP.load_all())
    if not any(r["v3"] is not None for r in uae):
        uae = None  # no UAE results yet

    charts = {}
    charts["overview"] = chart_task_overview(tasks)
    charts["hist"] = chart_hist(tasks)
    charts["by_attack"] = chart_by_attack(agg)
    charts["by_section"] = chart_by_section(agg)
    charts["harm_failures"] = chart_harm_failures(harm)
    charts["year_hist"] = chart_year_hist(landscape)
    charts["multilingual"] = chart_multilingual(tasks)
    if think:
        c = chart_thinking_divergence(think)
        if c:
            charts["thinking_divergence"] = c
    if uae:
        charts["uae_2way"] = chart_uae_2way(uae)
    for sec in L.SECTIONS:
        c = chart_section_tasks(tasks, sec, f"section_{sec}.png")
        if c:
            charts[f"section_{sec}"] = c

    # dump data
    data = {
        "model_label": L.MODEL_LABEL,
        "checkpoint": L.MODEL_CHECKPOINT,
        "generated": datetime.date.today().isoformat(),
        "aggregate": agg,
        "harm_failures": dict(harm),
        "year_hist": landscape["year_hist"],
        "n_sources": landscape["n_sources"],
        "new_sources": landscape["new_sources"],
        "tasks": {t.name: {
            "score": t.score, "score_meaning": t.score_meaning, "n": t.n_samples,
            "attack_tag": t.attack_tag, "risk_type_tag": t.risk_type_tag,
            "round_tag": t.round_tag, "harmful_count": t.harmful_count,
            "total_count": t.total_count, "bucket": t.bucket, "section": t.section,
            "ambiguous_or_error_count": t.ambiguous_or_error_count,
            "year": meta.get(t.name, {}).get("year"),
            "source": meta.get(t.name, {}).get("source"),
            "is_new": meta.get(t.name, {}).get("is_new", False),
        } for t in tasks.values()},
    }
    if think:
        data["thinking_analysis"] = {k: think[k] for k in (
            "n_tasks", "totals", "overall_harmful_rate", "thinking_harmful_rate",
            "answer_harmful_rate", "thinking_only_rate", "answer_only_rate")}
    with open(os.path.join(HERE, "report_data.json"), "w") as f:
        json.dump(data, f, indent=2, default=str)

    write_report(tasks, agg, harm, charts, landscape, think, uae)
    print(f"OK: {len(charts)} charts, report_data.json, REPORT.md written to {HERE}")


def write_report(tasks, agg, harm, charts, landscape, think, uae):
    from report_sections import build_markdown
    md = build_markdown(tasks, agg, harm, charts, L, landscape, think, uae)
    with open(os.path.join(HERE, "REPORT.md"), "w") as f:
        f.write(md)


if __name__ == "__main__":
    main()
