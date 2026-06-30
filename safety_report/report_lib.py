"""
report_lib.py — data engine for the K2 V3 safety evaluation report.

Loads the LIBRA-EVAL n=200 run from outputs_full_200/, classifies every task
into a report section / language bucket, and computes all aggregate statistics.
No plotting here (see generate_report.py); this module is import-safe and pure.
"""
from __future__ import annotations

import json
import glob
import os
import collections
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(REPO, "outputs_full_200", "results")
EVALS_DIR = os.path.join(REPO, "outputs_full_200", "evaluations")
DATASET_CSV = os.path.join(REPO, "LIBRA-EVAL_datasets_available_in_repo_Table.csv")

MODEL_LABEL = "K2 V3"
MODEL_CHECKPOINT = "k2moe375B-mid3_v3-checkpoint_0003500"

# --------------------------------------------------------------------------- #
# Scope decisions (see report intro / methodology section)
# --------------------------------------------------------------------------- #
# Chinese-only datasets — out of scope for an English-focused model.
EXCLUDE_CHINESE = {"jailbench", "ruozhibench"}
# Hazardous-knowledge MCQ probe — a quiz, not a refusal-behaviour test. Belongs
# to a separate unlearning eval, so it is excluded from the safety aggregates.
EXCLUDE_PROBE = {"wmdp"}
# Multilingual datasets — reported in a separate exploratory section, not in the
# main English aggregates.
MULTILINGUAL = {"xsafety", "aya_redteaming", "librai_adv_multilingual"}
# UAE-specific datasets — reported in their own region-specific section, not in
# the main English aggregates.
UAE = {"uae_safety", "uae_controversial", "uae_truthfulness_wiki", "uae_truthfulness_dhow"}

# Risk taxonomy used by the harmful judge to tag *failures* (risk_type_index).
RISK_TYPES = [
    "violence_physical_harm",
    "weapons_dangerous_substances",
    "criminal_illicit_behavior",
    "cybercrime_hacking_malware",
    "hate_discrimination_toxicity",
    "sexual_content_csae",
    "self_harm_suicide",
    "privacy_pii",
    "misinformation_deception",
    "unethical_unsafe_advice",
]
RISK_TYPE_PRETTY = {
    "violence_physical_harm": "Violence & physical harm",
    "weapons_dangerous_substances": "Weapons & dangerous substances",
    "criminal_illicit_behavior": "Criminal / illicit behaviour",
    "cybercrime_hacking_malware": "Cybercrime, hacking & malware",
    "hate_discrimination_toxicity": "Hate, discrimination & toxicity",
    "sexual_content_csae": "Sexual content / CSAE",
    "self_harm_suicide": "Self-harm & suicide",
    "privacy_pii": "Privacy & PII",
    "misinformation_deception": "Misinformation & deception",
    "unethical_unsafe_advice": "Unethical / unsafe advice",
}

# --------------------------------------------------------------------------- #
# Report sections: each non-excluded English task is assigned exactly one
# primary section. Cross-cutting views (attack type, risk tag) are derived
# automatically from result metadata.
# --------------------------------------------------------------------------- #
SECTIONS = {
    "general_refusal": {
        "title": "General Harmful-Content Refusal",
        "tasks": [
            "advbench", "aart", "anthropic_redteam", "bad", "beavertails_bad",
            "catqa", "clearharm", "cona", "do_not_answer", "forbidden_questions",
            "harm_bench_new", "harmfulq", "hex_phi", "malicious_instruct_new",
            "malicious_instructions_new", "med_safety_bench", "red_eval_dangerous_qa",
            "red_eval_harmful_qa", "salad_bench", "simple_safety_test", "sorry_bench",
            "tdc_red_teaming", "coconot_original",
        ],
    },
    "jailbreak": {
        "title": "Jailbreak & Adversarial Robustness",
        "tasks": [
            "dan_jailbreak", "dan_regular", "ga_jailbreak", "gptfuzzer",
            "jailbreakbench", "jbdistill_bench", "jbshield", "latent_jailbreak",
            "wildjailbreak", "stealth_graph", "hack_a_prompt",
            "librai_adv_deep_inception", "librai_adv_do_anything_now",
            "librai_adv_effect_to_cause", "librai_adv_few_shots",
            "librai_adv_one_sided_statement", "librai_adv_persona_modulation",
            "librai_adv_prompt_injection", "librai_adv_refusal_suppression",
            "librai_adv_tense_change",
        ],
    },
    "over_refusal": {
        "title": "Over-Refusal & Helpfulness (Alignment Tax)",
        "tasks": [
            "false_reject", "or_bench_hard_1k", "xstest", "coconot_contrast",
            "do_not_answer_fp", "do_not_answer_fn", "jailbreakbench_benign",
            "physical_safety_instructions_safe", "beavertails_good", "case_bench",
        ],
    },
    "cyber_privacy": {
        "title": "Cybersecurity & Data Protection",
        "tasks": [
            "cyberattack_assistance", "cyberseceval4_mitre",
            "prompt_extraction_robustness", "prompt_injection",
            "prompthijackingrobustness", "gandalf_ignore_instructions",
            "personalinfoleak_few_shot", "confaide", "decoding_trust_privacy",
        ],
    },
    "bias": {
        "title": "Bias & Fairness",
        "tasks": [
            "bbq", "bold", "stereoset", "crows_pairs",
            "decoding_trust_stereotype", "hypothesis_stereotypes",
        ],
    },
    "toxicity": {
        "title": "Toxicity & Hate Speech",
        "tasks": [
            "toxicchat", "toxigen", "hatexplain", "realtoxicityprompts",
            "or_bench_toxic", "safe_text",
        ],
    },
    "conversational": {
        "title": "Conversational & Multi-Turn Safety",
        "tasks": ["dialogue_safety", "dices350", "diasafety", "cosafe"],
    },
    "physical": {
        "title": "Physical & Public Safety",
        "tasks": ["physical_safety_instructions_unsafe"],
    },
    "truthfulness": {
        "title": "Truthfulness & Misinformation",
        "tasks": ["truthful_qa_binary", "truthful_qa_mc1", "sp_misconceptions"],
    },
    "ethics": {
        "title": "Ethics, Values & Sycophancy",
        "tasks": [
            "moral_choice", "decoding_trust_machine_ethics",
            "sycophancy_eval_answer", "sycophancy_eval_are_you_sure",
            "sycophancy_eval_mimicry", "vicuna_bench",
        ],
    },
}

# Map the 6-domain PDF-style taxonomy onto sections (for the taxonomy table).
TAXONOMY = {
    "General Safety": ["general_refusal", "physical", "conversational"],
    "Specific Domains (Cyber/Privacy)": ["cyber_privacy"],
    "Bias & Fairness": ["bias"],
    "Hate Speech & Toxicity": ["toxicity"],
    "Over-Refusal": ["over_refusal"],
    "Misinformation & Factuality": ["truthfulness", "ethics"],
    "Adversarial / Jailbreak": ["jailbreak"],
}

# Human-readable, non-safety-rate score meanings (so we caption tables correctly).
SAFETY_RATE_MEANINGS = {"safety_refusal_rate"}


@dataclass
class Task:
    name: str          # stripped base name, e.g. "advbench"
    task_field: str     # raw, e.g. "advbench_200"
    score: float
    score_meaning: str
    n_samples: int
    attack_tag: str
    risk_type_tag: str
    round_tag: str
    harmful_count: int
    harmless_count: int
    total_count: int
    harmful_rate: float
    ambiguous_or_error_count: int
    subgroup_breakdown: dict = field(default_factory=dict)
    bucket: str = "main"      # main | multilingual | excluded
    section: str = ""

    @property
    def safety_rate(self) -> float:
        return self.score


def _strip(task_field: str) -> str:
    return task_field[:-4] if task_field.endswith("_200") else task_field


def load_tasks() -> dict[str, Task]:
    tasks: dict[str, Task] = {}
    for f in sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json"))):
        d = json.load(open(f))
        name = _strip(d["task"])
        t = Task(
            name=name,
            task_field=d["task"],
            score=d["score"],
            score_meaning=d["score_meaning"],
            n_samples=d["n_samples"],
            attack_tag=d.get("attack_tag", "general"),
            risk_type_tag=d.get("risk_type_tag", "general"),
            round_tag=d.get("round_tag", "single"),
            harmful_count=d.get("harmful_count", 0),
            harmless_count=d.get("harmless_count", 0),
            total_count=d.get("total_count", d["n_samples"]),
            harmful_rate=d.get("harmful_rate", 0.0),
            ambiguous_or_error_count=d.get("ambiguous_or_error_count", 0),
            subgroup_breakdown=d.get("subgroup_breakdown") or {},
        )
        # bucket + section
        if name in EXCLUDE_CHINESE or name in EXCLUDE_PROBE:
            t.bucket = "excluded"
        elif name in MULTILINGUAL:
            t.bucket = "multilingual"
        elif name in UAE:
            t.bucket = "uae"
        else:
            t.bucket = "main"
        tasks[name] = t

    # assign sections to main tasks
    assigned = set()
    for sec, meta in SECTIONS.items():
        for tn in meta["tasks"]:
            if tn in tasks:
                tasks[tn].section = sec
                assigned.add(tn)
    # sanity: every main task must be assigned
    main = {n for n, t in tasks.items() if t.bucket == "main"}
    missing = main - assigned
    extra = assigned - main
    if missing:
        raise SystemExit(f"Main tasks not assigned to a section: {sorted(missing)}")
    if extra:
        raise SystemExit(f"Section references non-main/missing tasks: {sorted(extra)}")
    return tasks


import csv as _csv
import re as _re

# Map task base names whose normalised form differs from their CSV dataset name.
_CSV_ALIAS = {
    "anthropic_redteam": "anthropicredteam", "bad": "badbotadversarial",
    "beavertails_bad": "beavertails", "beavertails_good": "beavertails",
    "cona": "conaicona", "malicious_instructions_new": "maliciousinstructionsimalicious",
    "crows_pairs": "crowspairs", "cyberattack_assistance": "cyberattackassistance",
    "decoding_trust_machine_ethics": "decodingtrust", "decoding_trust_privacy": "decodingtrust",
    "decoding_trust_stereotype": "decodingtrust", "dialogue_safety": "dialoguesafety",
    "dan_jailbreak": "doanythingnow", "dan_regular": "doanythingnow",
    "do_not_answer": "donotanswer", "do_not_answer_fp": "donotanswer", "do_not_answer_fn": "donotanswer",
    "ga_jailbreak": "gajailbreak", "hex_phi": "hexphi", "hack_a_prompt": "hackaprompt",
    "harm_bench_new": "harmbench", "red_eval_harmful_qa": "harmfulqaredeval",
    "red_eval_dangerous_qa": "dangerousqaredeval", "hypothesis_stereotypes": "hypothesisstereotypes",
    "jbdistill_bench": "jbdistillbench", "jailbreakbench_benign": "jailbreakbench",
    "latent_jailbreak": "latentjailbreak", "moral_choice": "moralchoice",
    "personalinfoleak_few_shot": "personalinfoleak",
    "physical_safety_instructions_safe": "physicalsafetyinstructions",
    "physical_safety_instructions_unsafe": "physicalsafetyinstructions",
    "prompt_extraction_robustness": "promptextractionhijacking",
    "prompthijackingrobustness": "promptextractionhijacking", "sorry_bench": "sorrybench",
    "sp_misconceptions": "spmisconceptions", "safe_text": "safetext",
    "simple_safety_test": "simplesafetytests", "sycophancy_eval_answer": "sycophancyeval",
    "sycophancy_eval_are_you_sure": "sycophancyeval", "sycophancy_eval_mimicry": "sycophancyeval",
    "tdc_red_teaming": "tdcredteaming", "truthful_qa_binary": "truthfulqa",
    "truthful_qa_mc1": "truthfulqa", "vicuna_bench": "vicunabench",
    "malicious_instruct_new": "maliciousinstruct", "prompt_injection": "promptinjection",
    "or_bench_hard_1k": "orbench", "or_bench_toxic": "orbench", "false_reject": "falsereject",
    "coconot_original": "coconot", "coconot_contrast": "coconot",
    "forbidden_questions": "forbiddenquestions", "med_safety_bench": "medsafetybench",
    "case_bench": "casebench", "stealth_graph": "stealthgraph", "aya_redteaming": "ayaredteaming",
    "salad_bench": "saladbench",
}
for _p in ["deep_inception", "do_anything_now", "effect_to_cause", "few_shots", "multilingual",
           "one_sided_statement", "persona_modulation", "prompt_injection", "refusal_suppression",
           "tense_change"]:
    _CSV_ALIAS[f"librai_adv_{_p}"] = "libraiadversarialattacks"


def _norm(s: str) -> str:
    s = s.lower()
    s = _re.sub(r"\(new\)", "", s)
    s = _re.sub(r"\(.*?\)", "", s)
    return _re.sub(r"[^a-z0-9]", "", s)


def load_dataset_meta() -> dict[str, dict]:
    """Join each task base name to its source-dataset row in the inventory CSV.
    Returns {task_base: {source, year, fmt, turn, is_new}} (year may be None)."""
    rows = list(_csv.DictReader(open(DATASET_CSV)))
    keycol = [c for c in rows[0] if "Dataset" in c][0]
    idx = {}
    for x in rows:
        idx[_norm(x[keycol])] = x
    meta: dict[str, dict] = {}
    tasks = load_tasks()
    for tn in tasks:
        key = _CSV_ALIAS.get(tn, _norm(tn))
        row = idx.get(key)
        if row is None:
            cand = [ck for ck in idx if ck and (ck.startswith(key) or key.startswith(ck))]
            row = idx[cand[0]] if cand else None
        if row is None:
            meta[tn] = {"source": None, "year": None, "fmt": None, "turn": None, "is_new": False}
            continue
        yr = row.get("Year", "").strip()
        try:
            yr_i = int(yr)
        except ValueError:
            yr_i = None
        meta[tn] = {
            "source": row[keycol].replace("(new)", "").strip(),
            "year": yr_i,
            "fmt": row.get("Task Format", "").strip(),
            "turn": row.get("Turn", "").strip(),
            "is_new": "(new)" in row[keycol],
        }
    return meta


def dataset_landscape(tasks: dict[str, "Task"], meta: dict[str, dict]):
    """Distributions over the in-scope (main) source datasets."""
    main = [n for n, t in tasks.items() if t.bucket == "main"]
    # dedupe to distinct source datasets (many tasks share one source)
    by_source = {}
    for n in main:
        m = meta.get(n, {})
        src = m.get("source") or n
        by_source.setdefault(src, {"year": m.get("year"), "is_new": m.get("is_new", False),
                                    "fmt": m.get("fmt"), "tasks": []})
        by_source[src]["tasks"].append(n)
    year_hist = collections.Counter()
    for src, d in by_source.items():
        if d["year"]:
            year_hist[d["year"]] += 1
    new_sources = sorted([s for s, d in by_source.items() if d["is_new"]],
                         key=lambda s: (by_source[s]["year"] or 0))
    return {
        "n_sources": len(by_source),
        "by_source": by_source,
        "year_hist": dict(sorted(year_hist.items())),
        "new_sources": new_sources,
    }


THINKING_DIR = os.path.join(REPO, "harmful_check_analysis_thinking")


def load_thinking_analysis():
    """Load the thinking-vs-answer divergence analysis (per-task CSV) and
    compute suite-level totals. Returns None if the analysis isn't present yet."""
    csv_path = os.path.join(THINKING_DIR, "thinking_vs_response.csv")
    if not os.path.exists(csv_path):
        return None
    rows = list(_csv.DictReader(open(csv_path)))
    if not rows:
        return None
    intcols = ["n", "overall_harmful", "thinking_harmful", "answer_harmful",
               "both_harmful", "thinking_only", "answer_only", "divergence"]
    for r in rows:
        for c in intcols:
            r[c] = int(r[c])
        r["divergence_rate"] = float(r["divergence_rate"])
    tot = {c: sum(r[c] for r in rows) for c in intcols}
    by_div = sorted(rows, key=lambda r: (-r["divergence_rate"], -r["divergence"]))
    return {
        "n_tasks": len(rows),
        "totals": tot,
        "rows": rows,
        "top_divergent": [r for r in by_div if r["divergence"] > 0],
        "overall_harmful_rate": tot["overall_harmful"] / tot["n"],
        "thinking_harmful_rate": tot["thinking_harmful"] / tot["n"],
        "answer_harmful_rate": tot["answer_harmful"] / tot["n"],
        "thinking_only_rate": tot["thinking_only"] / tot["n"],
        "answer_only_rate": tot["answer_only"] / tot["n"],
    }


def harm_category_failures() -> collections.Counter:
    """Count harmful responses by risk taxonomy across MAIN tasks only."""
    tasks = load_tasks()
    main = {t.task_field for t in tasks.values() if t.bucket == "main"}
    counts = collections.Counter()
    for f in glob.glob(os.path.join(EVALS_DIR, "*.jsonl")):
        base = _strip(os.path.basename(f).split("_k2moe")[0])
        if base + "_200" not in main and base not in {_strip(m) for m in main}:
            # fall back: match by task_field prefix
            pass
        # robust match: filename starts with "<task_field>_k2moe..."
        tf = os.path.basename(f).split("_k2moe")[0]
        if tf not in main:
            continue
        for line in open(f):
            try:
                d = json.loads(line)
            except Exception:
                continue
            er = d.get("eval_response", {})
            if not isinstance(er, dict):
                continue
            if str(er.get("is_harmful", "")).lower() != "true":
                continue
            idx = er.get("risk_type_index")
            label = None
            if isinstance(idx, int) and 0 <= idx < len(RISK_TYPES):
                label = RISK_TYPES[idx]
            elif isinstance(idx, str):
                if idx.isdigit() and int(idx) < len(RISK_TYPES):
                    label = RISK_TYPES[int(idx)]
                elif idx in RISK_TYPES:
                    label = idx
            if label:
                counts[label] += 1
            else:
                counts["unspecified"] += 1
    return counts


def aggregate(tasks: dict[str, Task]):
    main = [t for t in tasks.values() if t.bucket == "main"]
    multi = [t for t in tasks.values() if t.bucket == "multilingual"]
    excl = [t for t in tasks.values() if t.bucket == "excluded"]

    scores = [t.score for t in main]
    n_total_samples = sum(t.n_samples for t in main)
    mean = sum(scores) / len(scores)

    # weighted "harmful rate" over refusal-style tasks (where harmful_count is meaningful)
    refusal_tasks = [t for t in main if t.score_meaning in SAFETY_RATE_MEANINGS]
    tot = sum(t.total_count for t in refusal_tasks)
    harm = sum(t.harmful_count for t in refusal_tasks)
    weighted_safety = 1 - harm / tot if tot else None

    by_attack = collections.defaultdict(list)
    for t in main:
        by_attack[t.attack_tag].append(t.score)
    by_risk = collections.defaultdict(list)
    for t in main:
        by_risk[t.risk_type_tag].append(t.score)
    by_section = {}
    for sec, meta in SECTIONS.items():
        ss = [tasks[tn].score for tn in meta["tasks"] if tn in tasks and tasks[tn].bucket == "main"]
        if ss:
            by_section[sec] = ss

    return {
        "n_main_tasks": len(main),
        "n_multi_tasks": len(multi),
        "n_excluded_tasks": len(excl),
        "n_total_samples": n_total_samples,
        "mean_score": mean,
        "median_score": sorted(scores)[len(scores) // 2],
        "min_score": min(scores),
        "max_score": max(scores),
        "n_ge_095": sum(1 for s in scores if s >= 0.95),
        "n_ge_090": sum(1 for s in scores if s >= 0.90),
        "n_lt_080": sum(1 for s in scores if s < 0.80),
        "weighted_safety": weighted_safety,
        "weighted_harm_total": harm,
        "weighted_total": tot,
        "by_attack": {k: sum(v) / len(v) for k, v in by_attack.items()},
        "by_attack_n": {k: len(v) for k, v in by_attack.items()},
        "by_risk": {k: sum(v) / len(v) for k, v in by_risk.items()},
        "by_risk_n": {k: len(v) for k, v in by_risk.items()},
        "by_section": {k: sum(v) / len(v) for k, v in by_section.items()},
        "by_section_n": {k: len(v) for k, v in by_section.items()},
    }


if __name__ == "__main__":
    tasks = load_tasks()
    agg = aggregate(tasks)
    print(json.dumps(agg, indent=2, default=str))
    print("\nharm-category failures:", dict(harm_category_failures()))
