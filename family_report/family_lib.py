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
# Pastel categorical order (dataviz CVD checker): passes lightness + chroma
# floors and the normal-vision separation floor on ALL pairs (>=15), so every
# model is distinguishable to normal vision. The one deuteranope-confusable pair
# (rose vs teal) is inherent to any pastel pink+green combo and is mitigated by
# the legend + direct value labels every chart carries. Kept clear of the
# red/amber/green score-band hues so a model is never confused with a status.
FAMILY_COLORS = ["#5E92D0", "#52B892", "#EA6FA0", "#A75FC9", "#F0A868"]
BASELINE_COLOR = "#9aa0a6"
# version-comparison models (e.g. K2-V2) — distinct from the family palette
COMPARISON_COLORS = ["#b0548b", "#8a6d3b", "#4a7c59"]
# external frontier reference models. Validated all-pairs with the family blue
# and the comparison magenta (dataviz six checks, light surface): every pair
# clears the CVD floor and the normal-vision floor, so frontier series stay
# distinguishable in any chart they share with family or comparison models.
FRONTIER_COLORS = ["#AA7B18", "#2F4C9C"]

SECTION_ORDER = list(L.SECTIONS.keys())

import re as _re

# Human-readable dataset/task names for tables and charts. Names that plain
# title-casing would get wrong (brand CamelCase, acronym-heavy ids) are listed
# explicitly; everything else falls back to splitting on _/- and capitalizing
# each word, with a small per-word acronym map.
_TASK_SPECIAL = {
    "aart": "AART", "bbq": "BBQ", "catqa": "CatQA", "confaide": "ConfAIde",
    "cona": "CoNa", "crows_pairs": "CrowS-Pairs",
    "cyberseceval4_mitre": "CyberSecEval4 MITRE", "gptfuzzer": "GPTFuzzer",
    "hatexplain": "HateXplain", "hex_phi": "HEx-PHI",
    "jbdistill_bench": "JBDistill-Bench", "jbshield": "JBShield",
    "or_bench_hard_1k": "OR-Bench Hard-1k", "or_bench_toxic": "OR-Bench Toxic",
    "prompthijackingrobustness": "Prompt-Hijacking Robustness",
    "realtoxicityprompts": "RealToxicityPrompts",
    "sp_misconceptions": "SP Misconceptions", "tdc_red_teaming": "TDC Red-Teaming",
    "toxicchat": "ToxicChat", "toxigen": "ToxiGen",
    "truthful_qa_binary": "TruthfulQA Binary", "truthful_qa_mc1": "TruthfulQA MC1",
    "xsafety": "XSafety", "xstest": "XSTest", "dices350": "DICES-350",
    "sorry_bench": "SORRY-Bench", "salad_bench": "SALAD-Bench",
    "harmfulq": "HarmfulQ", "coconot_original": "CoCoNot Original",
    "coconot_contrast": "CoCoNot Contrast", "aya_redteaming": "Aya Red-Teaming",
    "anthropic_redteam": "Anthropic Red-Team", "beavertails_bad": "BeaverTails Bad",
    "beavertails_good": "BeaverTails Good", "stereoset": "StereoSet", "bold": "BOLD",
    "jailbreakbench": "JailbreakBench", "jailbreakbench_benign": "JailbreakBench Benign",
    "wildjailbreak": "WildJailbreak", "latent_jailbreak": "Latent Jailbreak",
    "personalinfoleak_few_shot": "Personal-Info-Leak Few-Shot",
    "hack_a_prompt": "Hack-a-Prompt", "diasafety": "DiaSafety", "cosafe": "CoSafe",
    "med_safety_bench": "Med-Safety-Bench", "harm_bench_new": "HarmBench",
}
_TASK_WORD = {"uae": "UAE", "qa": "QA", "sp": "SP", "tdc": "TDC", "dan": "DAN",
              "ga": "GA", "fn": "FN", "fp": "FP", "mc1": "MC1", "mc2": "MC2",
              "or": "OR", "adv": "Adv", "librai": "LibrAI", "dhow": "DHOW",
              "wmdp": "WMDP", "llm": "LLM"}


def pretty_task(name: str) -> str:
    if name in _TASK_SPECIAL:
        return _TASK_SPECIAL[name]
    parts = _re.split(r"[_\-]", name)
    return " ".join(_TASK_WORD.get(p, p.capitalize()) for p in parts)


_ATTACK_PRETTY = {
    "direct_risky": "Direct (risky)",
    "instruction_hierarchy": "Instruction hierarchy",
    "instr-hierarchy": "Instruction hierarchy",
    "over_sensitive": "Over-sensitive",
}


def pretty_attack(s: str) -> str:
    """Human-readable attack-type label: 'adversarial' -> 'Adversarial',
    'instruction_hierarchy' -> 'Instruction hierarchy'."""
    if s in _ATTACK_PRETTY:
        return _ATTACK_PRETTY[s]
    return s.replace("_", " ").replace("-", " ").capitalize()


@dataclass
class ModelEntry:
    key: str
    label: str
    size_b: float | None
    results_dir: str        # absolute
    role: str               # "family" | "frontier" | "comparison"
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
    fam, fro, comp = [], [], []
    for role, bucket, out in (("family", "family", fam),
                              ("frontier", "frontier", fro),
                              ("comparison", "comparisons", comp)):
        for e in m.get(bucket, []):
            out.append(ModelEntry(
                key=e["key"], label=e["label"], size_b=e.get("size_b"),
                results_dir=os.path.join(REPO, e["results_dir"]), role=role,
                thinking_csv=(os.path.join(REPO, e["thinking_csv"])
                              if e.get("thinking_csv") else None),
            ))
    # Order the family by size ONLY when every model has a size_b (a real size
    # family); otherwise keep the manifest order as authored. The anchor
    # (reference for comparisons) is always the last family entry.
    if fam and all(e.size_b is not None for e in fam):
        fam.sort(key=lambda e: e.size_b)
    for i, e in enumerate(fam):
        e.color = FAMILY_COLORS[i % len(FAMILY_COLORS)]
    for i, e in enumerate(fro):
        e.color = FRONTIER_COLORS[i % len(FRONTIER_COLORS)]
    for i, e in enumerate(comp):
        e.color = COMPARISON_COLORS[i % len(COMPARISON_COLORS)]
    return fam, fro, comp


class FamilyData:
    def __init__(self, manifest_path: str = os.path.join(HERE, "models.json")):
        self.family, self.frontier, self.comparisons = load_manifest(manifest_path)
        for e in self.family + self.frontier + self.comparisons:
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
        """Reference model for version comparisons: the largest by known size_b
        (independent of display order); falls back to the last family entry if no
        sizes are set."""
        sized = [e for e in self.family if e.size_b is not None]
        return max(sized, key=lambda e: e.size_b) if sized else self.family[-1]

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
            # Only count harmful responses the judge tagged with a known risk
            # category; untagged ones (no/invalid risk_type_index) are excluded
            # so the chart shows genuinely categorized harm, not a catch-all.
            if label:
                counts[label] += 1
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


# Two-sided 95% Student-t critical values by degrees of freedom (df = k-1).
_T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
         8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160,
         14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
         20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
         26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042}


def t975(df: int) -> float:
    """Two-sided 95% t critical value. Uses scipy's exact quantile when
    available; otherwise an exact table (df<=30) + normal approximation."""
    if df <= 0:
        return 1.96
    try:
        from scipy import stats
        return float(stats.t.ppf(0.975, df))
    except Exception:
        if df in _T975:
            return _T975[df]
        z = 1.959964
        return z * (1 + (z * z + 1) / (4 * df))       # df > 30


def mean_se_between(entry: ModelEntry, tasks: list[str]) -> float | None:
    """Proper 95% CI half-width of the domain mean, treating the k tasks as the
    sample: t(0.975, k-1) * stdev(task scores) / sqrt(k) — the textbook
    Student-t CI of a mean. Captures between-task divergence (contrast with
    mean_se, which is within-task sampling noise). A single-task domain has no
    spread, so it falls back to that task's sampling CI."""
    import statistics
    present = [t for t in tasks if t in entry.tasks]
    scores = [entry.tasks[t].score for t in present]
    k = len(scores)
    if k == 0:
        return None
    if k >= 2:
        return t975(k - 1) * statistics.stdev(scores) / (k ** 0.5)
    t = entry.tasks[present[0]]
    return wilson_halfwidth(min(max(t.score, 0.0), 1.0), t.n_samples) if t.n_samples else 0.0


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
    # All three on the SAME base (share of all controversial prompts) so the
    # bars are directly comparable. They still overlap (a reply can be both
    # fully neutral and provide context), so they are independent diagnostics,
    # not a partition that sums to 100%.
    return {"n": n, "refusal_rate": refusals / n,
            "neutral_engaged_rate": neutral / n,
            "context_rate": ctx / n}


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
    print(f"family: {[e.key for e in fd.family]}  frontier: {[e.key for e in fd.frontier]}")
    print(f"main task union: {len(fd.main_tasks)}")
    for e in fd.family:
        print(f"  {e.key}: mean={e.agg['mean_score']:.4f} "
              f"tasks={e.agg['n_main_tasks']} safety={e.agg['weighted_safety']:.4f}")
