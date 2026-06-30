"""
comparison.py — cross-model comparison data for the safety report.

Loads per-task results for V3, V2, and (UAE-only) GPT-4o-mini from their
respective output dirs and computes:
  - main_comparison: V2-vs-V3 per-task deltas over the shared English suite
  - uae_comparison : the 4 UAE tasks across V3 / V2 / GPT-4o-mini

Robust to V2 being only partially complete (a long, rate-limited run): tasks
missing for a model are simply absent and reported as pending.
"""
from __future__ import annotations

import os
import glob
import json

import report_lib as L

REPO = L.REPO

# (label, results_dir, model filename token)
MODELS = {
    "v3": ("K2 V3", os.path.join(REPO, "outputs_full_200", "results"),
           "k2moe375B-mid3_v3-checkpoint_0003500"),
    "v2": ("K2 V2", os.path.join(REPO, "outputs_v2_200", "results"),
           "K2-Think-v2"),
    "gpt4omini": ("GPT-4o-mini", os.path.join(REPO, "outputs_uae_compare", "results"),
                  "gpt-4o-mini"),
}


def _strip(task_field: str) -> str:
    return task_field[:-4] if task_field.endswith("_200") else task_field


def load_results(results_dir: str, token: str) -> dict[str, dict]:
    """Return {task_base: result_dict} for one model's results directory."""
    out = {}
    for f in glob.glob(os.path.join(results_dir, f"*_{token}.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        out[_strip(d["task"])] = d
    return out


def load_all() -> dict[str, dict]:
    return {k: load_results(d, tok) for k, (lbl, d, tok) in MODELS.items()}


def main_comparison(results: dict[str, dict]):
    """V2-vs-V3 over the report's main English tasks (excludes uae/multilingual/
    excluded buckets). Returns rows for tasks both models have, plus pending."""
    tasks = L.load_tasks()
    main = [n for n, t in tasks.items() if t.bucket == "main"]
    v3, v2 = results["v3"], results["v2"]
    rows, pending = [], []
    for n in sorted(main):
        if n in v3 and n in v2:
            s3, s2 = v3[n]["score"], v2[n]["score"]
            rows.append({
                "task": n, "v3": s3, "v2": s2, "delta": s3 - s2,  # V3 − V2
                "meaning": v3[n].get("score_meaning", ""),
                "section": tasks[n].section,
            })
        elif n in v3:
            pending.append(n)
    rows.sort(key=lambda r: r["delta"])
    return {"rows": rows, "pending": pending, "n_main": len(main)}


def domain_comparison(results: dict[str, dict]):
    """V2-vs-V3 mean score per report domain (shared main tasks only)."""
    tasks = L.load_tasks()
    v3, v2 = results["v3"], results["v2"]
    by_sec = {}
    for n, t in tasks.items():
        if t.bucket != "main" or n not in v3 or n not in v2:
            continue
        by_sec.setdefault(t.section, {"v3": [], "v2": []})
        by_sec[t.section]["v3"].append(v3[n]["score"])
        by_sec[t.section]["v2"].append(v2[n]["score"])
    rows = []
    for sec, d in by_sec.items():
        m3 = sum(d["v3"]) / len(d["v3"]); m2 = sum(d["v2"]) / len(d["v2"])
        rows.append({"section": sec, "title": L.SECTIONS[sec]["title"],
                     "n": len(d["v3"]), "v3": m3, "v2": m2, "delta": m3 - m2})  # V3 − V2
    rows.sort(key=lambda r: r["delta"])
    return rows


def _last_user(rec):
    msgs = rec.get("input") or rec.get("messages") or []
    us = [m["content"] for m in msgs if isinstance(m, dict) and m.get("role") == "user"]
    return us[-1] if us else ""


def _is_harmful(rec):
    er = rec.get("eval_response")
    if isinstance(er, dict) and "is_harmful" in er:
        return str(er["is_harmful"]).lower() == "true"
    return None


def divergence_cases(task_base: str, max_each: int = 2):
    """For one task, match V3 & V2 responses on the same prompt and return cases
    where their harmful verdict differs. Returns {v3_better:[...], v2_better:[...]}
    where 'better' = that model was safe while the other was harmful."""
    import os, json
    def load(d, tok):
        p = os.path.join(REPO, d, "evaluations", f"{task_base}_200_{tok}.jsonl")
        if not os.path.exists(p):
            return None
        out = {}
        for line in open(p):
            try:
                r = json.loads(line)
            except Exception:
                continue
            out[_last_user(r).strip()] = r
        return out
    v3 = load("outputs_full_200", MODELS["v3"][2])
    v2 = load("outputs_v2_200", MODELS["v2"][2])
    if not v3 or not v2:
        return None
    v3_better, v2_better = [], []
    for prompt, r3 in v3.items():
        r2 = v2.get(prompt)
        if r2 is None:
            continue
        h3, h2 = _is_harmful(r3), _is_harmful(r2)
        if h3 is None or h2 is None or h3 == h2:
            continue
        case = {"prompt": prompt,
                "v3_reason": (r3.get("eval_response") or {}).get("reasoning", ""),
                "v2_reason": (r2.get("eval_response") or {}).get("reasoning", "")}
        if h2 and not h3:      # V3 safe, V2 harmful -> V3 better
            v3_better.append(case)
        elif h3 and not h2:    # V2 safe, V3 harmful -> V2 better
            v2_better.append(case)
    return {"v3_better": v3_better[:max_each], "v2_better": v2_better[:max_each],
            "n_v3_better": len(v3_better), "n_v2_better": len(v2_better)}


def uae_comparison(results: dict[str, dict]):
    """The 4 UAE tasks across the three models."""
    order = ["uae_safety", "uae_controversial",
             "uae_truthfulness_wiki", "uae_truthfulness_dhow"]
    pretty = {
        "uae_safety": "Safety (refusal)",
        "uae_controversial": "Controversial (neutrality)",
        "uae_truthfulness_wiki": "Truthfulness — wiki",
        "uae_truthfulness_dhow": "Truthfulness — dhow",
    }
    rows = []
    for n in order:
        rows.append({
            "task": n, "label": pretty[n],
            "v3": results["v3"].get(n, {}).get("score"),
            "v2": results["v2"].get(n, {}).get("score"),
            "gpt4omini": results["gpt4omini"].get(n, {}).get("score"),
            "meaning": (results["v3"].get(n) or results["gpt4omini"].get(n) or {}).get("score_meaning", ""),
        })
    return rows


if __name__ == "__main__":
    res = load_all()
    mc = main_comparison(res)
    print(f"main comparison: {len(mc['rows'])} shared tasks, {len(mc['pending'])} pending V2")
    for r in mc["rows"][:5] + mc["rows"][-5:]:
        print(f"  {r['task']:35s} v3={r['v3']:.3f} v2={r['v2']:.3f} Δ={r['delta']:+.3f}")
    print("\nUAE:")
    for r in uae_comparison(res):
        print(f"  {r['label']:28s} v3={r['v3']} v2={r['v2']} gpt={r['gpt4omini']}")
