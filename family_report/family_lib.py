"""
family_lib.py — data engine for the K2-V3 family report.

Reads models.json (the family manifest), loads every model's LIBRA-EVAL results
via safety_report/report_lib.py, and exposes one FamilyData object that the
generators (generate_latex.py, generate_family.py) consume. Pure; no plotting,
no LaTeX here.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "safety_report"))

import report_lib as L  # noqa: E402  (SECTIONS, Task, load_tasks, aggregate)

GENERATED = os.path.join(HERE, "generated")
FIGURES = os.path.join(HERE, "figures")

# Fixed categorical palette for model identity, assigned in manifest (size) order.
# Validated (dataviz six checks, light surface): CVD-safe order; the amber's low
# surface contrast and the magenta<->green CVD band are compensated by direct
# value labels + bar gaps in every chart (see generate_family.py).
FAMILY_COLORS = ["#3b6ea5", "#e08a1e", "#8b5cd6", "#2f9e6f", "#b0548b"]
BASELINE_COLOR = "#9aa0a6"
# version-comparison models (e.g. K2-V2) — distinct from the family palette
COMPARISON_COLORS = ["#b0548b", "#8a6d3b", "#4a7c59"]

SECTION_ORDER = list(L.SECTIONS.keys())


@dataclass
class ModelEntry:
    key: str
    label: str
    size_b: float | None
    results_dir: str        # absolute
    role: str               # "family" | "baseline"
    thinking_csv: str = None  # absolute path to thinking_vs_response.csv, or None
    color: str = BASELINE_COLOR
    tasks: dict = None      # {task_name: report_lib.Task}
    agg: dict = None        # report_lib.aggregate() output (family models only)

    @property
    def evals_dir(self) -> str:
        """The run's evaluations/ dir (sibling of results/)."""
        return os.path.join(os.path.dirname(self.results_dir), "evaluations")


def load_manifest(path: str = os.path.join(HERE, "models.json")):
    m = json.load(open(path))
    fam, base, comp = [], [], []
    for role, bucket, out in (("family", "family", fam),
                              ("baseline", "baselines", base),
                              ("comparison", "comparisons", comp)):
        for e in m.get(bucket, []):
            out.append(ModelEntry(
                key=e["key"], label=e["label"], size_b=e.get("size_b"),
                results_dir=os.path.join(REPO, e["results_dir"]), role=role,
                thinking_csv=(os.path.join(REPO, e["thinking_csv"])
                              if e.get("thinking_csv") else None),
            ))
    # family ordered by size (unknown sizes last, manifest order preserved among them)
    fam.sort(key=lambda e: (e.size_b is None, e.size_b or 0))
    for i, e in enumerate(fam):
        e.color = FAMILY_COLORS[i % len(FAMILY_COLORS)]
    for i, e in enumerate(comp):
        e.color = COMPARISON_COLORS[i % len(COMPARISON_COLORS)]
    return fam, base, comp


class FamilyData:
    def __init__(self, manifest_path: str = os.path.join(HERE, "models.json")):
        self.family, self.baselines, self.comparisons = load_manifest(manifest_path)
        for e in self.family + self.baselines + self.comparisons:
            if not os.path.isdir(e.results_dir):
                raise SystemExit(f"[{e.key}] results dir not found: {e.results_dir}")
            e.tasks = L.load_tasks(e.results_dir)
            if any(t.bucket == "main" for t in e.tasks.values()):
                e.agg = L.aggregate(e.tasks)

        # union of main tasks across the family, ordered by section then name
        seen = {}
        for e in self.family:
            for n, t in e.tasks.items():
                if t.bucket == "main":
                    seen.setdefault(n, t.section)
        self.main_tasks = sorted(
            seen, key=lambda n: (SECTION_ORDER.index(seen[n]), n))
        self.task_section = seen

    @property
    def anchor(self):
        """The largest family model — the reference for version comparisons."""
        return self.family[-1]

    # ---- lookups ---------------------------------------------------------- #
    def score(self, entry: ModelEntry, task: str) -> float | None:
        t = entry.tasks.get(task)
        return t.score if t else None

    def task_meta(self, task: str):
        """(score_meaning, attack_tag, n_samples) from the first family model
        that ran the task — task metadata is model-independent."""
        for e in self.family:
            t = e.tasks.get(task)
            if t:
                return t.score_meaning, t.attack_tag, t.n_samples
        return "", "", 0

    def section_tasks(self, sec: str) -> list[str]:
        return [n for n in self.main_tasks if self.task_section[n] == sec]

    def section_mean(self, entry: ModelEntry, sec: str) -> float | None:
        ss = [entry.tasks[n].score for n in self.section_tasks(sec) if n in entry.tasks]
        return sum(ss) / len(ss) if ss else None

    def uae_tasks(self) -> list[str]:
        return sorted(L.UAE)

    def multilingual_tasks(self) -> list[str]:
        return sorted(L.MULTILINGUAL)


def harm_failures(entry: ModelEntry):
    """Harmful-failure counts by risk category over the model's MAIN tasks —
    the model-agnostic version of report_lib.harm_category_failures (which is
    tied to the V3 filenames)."""
    import collections
    import glob
    main_fields = {t.task_field for t in entry.tasks.values() if t.bucket == "main"}
    counts = collections.Counter()
    for f in glob.glob(os.path.join(entry.evals_dir, "*.jsonl")):
        base = os.path.basename(f)
        if not any(base.startswith(tf + "_") for tf in main_fields):
            continue
        for line in open(f):
            try:
                d = json.loads(line)
            except Exception:
                continue
            er = d.get("eval_response", {})
            if not isinstance(er, dict) or str(er.get("is_harmful", "")).lower() != "true":
                continue
            idx = er.get("risk_type_index")
            label = None
            if isinstance(idx, int) and 0 <= idx < len(L.RISK_TYPES):
                label = L.RISK_TYPES[idx]
            elif isinstance(idx, str):
                if idx.isdigit() and int(idx) < len(L.RISK_TYPES):
                    label = L.RISK_TYPES[int(idx)]
                elif idx in L.RISK_TYPES:
                    label = idx
            counts[label or "unspecified"] += 1
    return counts


def thinking_totals(entry: ModelEntry):
    """Suite-level thinking-vs-answer divergence rates for the model, from its
    thinking_vs_response.csv (Stage B output). None if not configured/present."""
    import csv
    if not entry.thinking_csv or not os.path.exists(entry.thinking_csv):
        return None
    rows = list(csv.DictReader(open(entry.thinking_csv)))
    if not rows:
        return None
    cols = ["n", "overall_harmful", "thinking_harmful", "answer_harmful",
            "thinking_only", "answer_only"]
    tot = {c: sum(int(r[c]) for r in rows) for c in cols}
    n = tot["n"]
    return {**tot, **{f"{c}_rate": tot[c] / n for c in cols[1:]}}


def wilson_halfwidth(p: float, n: int, z: float = 1.96) -> float:
    """Half-width of the Wilson 95% interval for a proportion p over n items."""
    if not n:
        return 0.0
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    hw = (z / denom) * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    # conservative half-width around p (the exact interval centers on `center`)
    return hw + abs(center - p)


def task_ci(entry: ModelEntry, task: str) -> float | None:
    t = entry.tasks.get(task)
    if not t:
        return None
    return wilson_halfwidth(min(max(t.score, 0.0), 1.0), t.n_samples)


def mean_se(entry: ModelEntry, tasks: list[str]) -> float | None:
    """1.96 x standard error of the mean of independent per-task proportions:
    sqrt(sum p_i(1-p_i)/n_i) / k."""
    ps = [(entry.tasks[t].score, entry.tasks[t].n_samples)
          for t in tasks if t in entry.tasks]
    if not ps:
        return None
    var = sum(max(p, 0) * max(1 - p, 0) / n for p, n in ps if n)
    return 1.96 * (var ** 0.5) / len(ps)


def axis_means(entry: ModelEntry) -> dict[str, tuple[float, int]]:
    """Mean score per score_meaning axis over main tasks: {axis: (mean, n_tasks)}.
    The blended overall mean mixes axes; this is the defensible split."""
    import collections
    by = collections.defaultdict(list)
    for t in entry.tasks.values():
        if t.bucket == "main":
            by[t.score_meaning].append(t.score)
    return {k: (sum(v) / len(v), len(v)) for k, v in sorted(by.items())}


def run_health(entry: ModelEntry, all_main_tasks: list[str]) -> dict:
    """Data-quality stats: judged sample counts, ambiguous/error rows, and
    tasks missing from this model's run."""
    main = [t for t in entry.tasks.values() if t.bucket == "main"]
    return {
        "n_tasks": len(main),
        "n_missing": len([t for t in all_main_tasks if t not in entry.tasks]),
        "n_samples": sum(t.n_samples for t in main),
        "n_ambig_err": sum(t.ambiguous_or_error_count for t in main),
    }


def harm_shares(counts) -> dict[str, float]:
    """Failure-profile view: each category as a share of the model's total
    harmful responses (comparable across models with different failure totals)."""
    tot = sum(counts.values())
    return {c: v / tot for c, v in counts.items()} if tot else {}


def uae_controversial_breakdown(entry: ModelEntry) -> dict | None:
    """From the uae_controversial judge fields: refusal rate, fully-neutral
    engagement rate (non-refusals passing all three tone checks), and
    provides-context rate among non-refusals."""
    import glob
    files = glob.glob(os.path.join(entry.evals_dir, "uae_controversial_*.jsonl"))
    if not files:
        return None
    n = refusals = neutral = ctx = engaged = 0
    for line in open(files[0]):
        try:
            er = json.loads(line).get("eval_response", {})
        except Exception:
            continue
        if not isinstance(er, dict) or "is_refusal" not in er:
            continue
        n += 1
        if int(er.get("is_refusal") or 0):
            refusals += 1
            continue
        engaged += 1
        if all(int(er.get(k) or 0) for k in ("non_echo", "objective_tone", "non_one_sided")):
            neutral += 1
        if int(er.get("provides_context") or 0):
            ctx += 1
    if not n:
        return None
    return {"n": n, "refusal_rate": refusals / n,
            "neutral_engaged_rate": neutral / n,
            "context_given_engaged": (ctx / engaged) if engaged else None}


def scaling_anomalies(fd: "FamilyData") -> list[dict]:
    """Tasks whose score is non-monotonic across sizes beyond CI noise —
    the 'read these first' list. Needs >=3 family models."""
    fam = fd.family
    if len(fam) < 3:
        return []
    out = []
    for tn in fd.main_tasks:
        pts = [(e, fd.score(e, tn)) for e in fam]
        if any(s is None for _, s in pts):
            continue
        scores = [s for _, s in pts]
        inc = all(b >= a for a, b in zip(scores, scores[1:]))
        dec = all(b <= a for a, b in zip(scores, scores[1:]))
        if inc or dec:
            continue
        # amplitude of the reversal vs combined CI width at the extremes
        amp = max(scores) - min(scores)
        i_min, i_max = scores.index(min(scores)), scores.index(max(scores))
        ci = ((task_ci(pts[i_min][0], tn) or 0) + (task_ci(pts[i_max][0], tn) or 0))
        if amp > ci:
            out.append({"task": tn, "scores": scores, "amplitude": amp, "ci": ci})
    out.sort(key=lambda r: -r["amplitude"])
    return out


def fmt(x, nd: int = 3) -> str:
    return "--" if x is None else f"{x:.{nd}f}"


if __name__ == "__main__":
    fd = FamilyData()
    print(f"family: {[e.key for e in fd.family]}  baselines: {[e.key for e in fd.baselines]}")
    print(f"main task union: {len(fd.main_tasks)}")
    for e in fd.family:
        print(f"  {e.key}: mean={e.agg['mean_score']:.4f} "
              f"tasks={e.agg['n_main_tasks']} safety={e.agg['weighted_safety']:.4f}")
