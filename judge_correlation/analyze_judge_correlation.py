"""Correlate the original GPT-4o judge with a re-judge by another model.

Joins outputs_full_200/evaluations/*.jsonl (GPT-4o `eval_response`) with
judge_correlation/evaluations_<slug>/*.jsonl (new judge) on item index, then:

  Per item  — re-scores every item under BOTH judges with the task's own
              `_single_eval_postprocess` (so agreement is measured on the exact
              quantity that enters the reported score), plus raw-verdict
              agreement / Cohen's kappa for the binary judges.
  Per task  — official score under each judge, Pearson/Spearman across tasks,
              mean |delta|, biggest movers.

Writes: judge_correlation/per_task_scores_<slug>.csv,
        judge_correlation/disagreements_<slug>.jsonl,
        judge_correlation/REPORT_<slug>.md
"""

import argparse
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from libra_eval.tasks import TASKS  # noqa: E402


def cohen_kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    po = (a == b).mean()
    pe = sum(((a == k).mean()) * ((b == k).mean()) for k in set(a) | set(b))
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.std() == 0 or y.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x, y):
    return pearson(pd.Series(x).rank(), pd.Series(y).rank())


def norm_binary(v):
    """Normalize is_harmful / disclosed / match style fields to {0,1,None}."""
    s = str(v).strip().lower()
    if s in ("true", "yes", "1", "1.0"):
        return 1
    if s in ("false", "no", "0", "0.0"):
        return 0
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="openai/gpt-5.6-terra")
    ap.add_argument("--eval-dir", default=os.path.join(REPO, "outputs_full_200/evaluations"))
    ap.add_argument("--results-dir", default=os.path.join(REPO, "outputs_full_200/results"))
    ap.add_argument("--out-dir", default=os.path.join(REPO, "judge_correlation"))
    args = ap.parse_args()

    slug = args.model.replace("/", "_")
    new_dir = os.path.join(args.out_dir, f"evaluations_{slug}")

    task_rows, item_frames, disagreements = [], [], []

    for np_path in sorted(glob.glob(os.path.join(new_dir, "*.jsonl"))):
        tname = os.path.basename(np_path)[:-6]
        base = re.sub(r"_\d+$", "", tname)
        cls = TASKS.get(base)
        if cls is None:
            continue
        old_paths = glob.glob(os.path.join(args.eval_dir, f"{tname}_*.jsonl"))
        if not old_paths:
            continue

        old_df = pd.read_json(old_paths[0], lines=True)
        new_df = pd.read_json(np_path, lines=True).drop_duplicates("idx").set_index("idx")
        # keep only items the new judge answered without transport errors
        new_df = new_df[~new_df["eval_response"].apply(
            lambda r: isinstance(r, dict) and "_error" in r)]
        common = old_df.index.intersection(new_df.index)
        if len(common) == 0:
            continue

        task = cls.__new__(cls)
        evaluator = cls.librai_evaluator_name

        # Hybrid tasks (ConfAIde) route some items programmatically and store
        # {"_route": ...} dicts. Programmatic rows are judge-independent: reuse
        # the stored result for BOTH judges and only compare the judge-routed
        # rows; the new judge's raw verdict must be re-wrapped for postprocess.
        old_resp = old_df.loc[common, "eval_response"]
        routes = old_resp.apply(lambda r: r.get("_route") if isinstance(r, dict) else None)
        is_hybrid = routes.notna().any()
        if is_hybrid:
            judged_mask = (routes == "judge").values
            new_resp = [
                {"_route": "judge", "verdict": nr} if jm else orr
                for nr, orr, jm in zip(
                    new_df.loc[common, "eval_response"].values, old_resp.values, judged_mask
                )
            ]
        else:
            judged_mask = np.ones(len(common), dtype=bool)
            new_resp = list(new_df.loc[common, "eval_response"].values)

        def score_with(df, responses):
            tmp = df.loc[common].copy()
            tmp["eval_response"] = responses
            return tmp.apply(task._single_eval_postprocess, axis=1).astype(float)

        try:
            s_old = score_with(old_df, old_resp)
            s_new = score_with(old_df, new_resp)
        except Exception as e:
            print(f"[skip] {tname}: postprocess failed: {e}")
            continue

        # raw binary verdicts where the judge emits one (harmful/refusal judges)
        def raw_bin(resp):
            if not isinstance(resp, dict):
                return None
            if isinstance(resp.get("verdict"), dict):
                resp = resp["verdict"]
            for k in ("is_harmful", "disclosed", "match", "is_biased", "leaked",
                      "is_correct", "hijacked", "is_offensive", "compliant"):
                if k in resp:
                    return norm_binary(resp[k])
            return None

        rb_old = old_resp.apply(raw_bin).values
        rb_new = np.array([raw_bin(r) for r in new_resp], dtype=object)

        # per-item comparison only over rows an LLM actually judged
        jm = judged_mask
        item_frames.append(pd.DataFrame({
            "task": tname, "evaluator": evaluator, "idx": np.asarray(common)[jm],
            "score_old": s_old.values[jm], "score_new": s_new.values[jm],
            "bin_old": rb_old[jm], "bin_new": rb_new[jm],
        }))

        for i, idx in enumerate(common):
            if jm[i] and s_old.values[i] != s_new.values[i]:
                disagreements.append({
                    "task": tname, "idx": int(idx), "evaluator": evaluator,
                    "score_gpt4o": float(s_old.values[i]),
                    "score_new": float(s_new.values[i]),
                    "eval_gpt4o": old_df.loc[idx, "eval_response"],
                    "eval_new": new_df.loc[idx, "eval_response"],
                    "response_snippet": str(old_df.loc[idx, "response"])[:600],
                })

        task_rows.append({
            "task": tname, "evaluator": evaluator, "n": len(common),
            "n_judged": int(jm.sum()),
            "score_gpt4o": round(float(s_old.mean()), 4),
            "score_new": round(float(s_new.mean()), 4),
            "delta": round(float(s_new.mean() - s_old.mean()), 4),
            "item_agreement": round(float((s_old.values[jm] == s_new.values[jm]).mean()), 4),
        })

    tasks_df = pd.DataFrame(task_rows).sort_values("delta", key=abs, ascending=False)
    items = pd.concat(item_frames, ignore_index=True)

    # ---- global stats ----
    r_task = pearson(tasks_df["score_gpt4o"], tasks_df["score_new"])
    rho_task = spearman(tasks_df["score_gpt4o"], tasks_df["score_new"])
    item_agree = float((items["score_old"] == items["score_new"]).mean())
    r_item = pearson(items["score_old"], items["score_new"])

    binmask = items["bin_old"].notna() & pd.Series(items["bin_new"]).notna()
    bins = items[binmask]
    kappa = cohen_kappa(bins["bin_old"].astype(int), bins["bin_new"].astype(int)) if len(bins) else float("nan")
    bin_agree = float((bins["bin_old"] == bins["bin_new"]).mean()) if len(bins) else float("nan")

    # per-evaluator-family breakdown
    fam_rows = []
    for ev, g in items.groupby("evaluator"):
        fam_rows.append({
            "evaluator": ev, "n_items": len(g),
            "item_agreement": round(float((g["score_old"] == g["score_new"]).mean()), 4),
            "pearson_item": round(pearson(g["score_old"], g["score_new"]), 4)
            if g["score_old"].std() > 0 and g["score_new"].std() > 0 else None,
        })
    fam_df = pd.DataFrame(fam_rows).sort_values("n_items", ascending=False)

    tasks_df.to_csv(os.path.join(args.out_dir, f"per_task_scores_{slug}.csv"), index=False)
    with open(os.path.join(args.out_dir, f"disagreements_{slug}.jsonl"), "w") as f:
        for d in disagreements:
            f.write(json.dumps(d, ensure_ascii=False, default=str) + "\n")

    md = []
    md.append(f"# Judge correlation: openai/gpt-4o vs {args.model}\n")
    md.append(f"- Tasks compared: **{len(tasks_df)}** | items: **{len(items):,}**")
    md.append(f"- Per-task score correlation: Pearson **{r_task:.4f}**, Spearman **{rho_task:.4f}**")
    md.append(f"- Mean |score delta| per task: **{tasks_df['delta'].abs().mean():.4f}** "
              f"(max {tasks_df['delta'].abs().max():.4f})")
    md.append(f"- Per-item score agreement: **{item_agree:.2%}** (Pearson {r_item:.4f})")
    md.append(f"- Binary-verdict judges ({len(bins):,} items): agreement **{bin_agree:.2%}**, "
              f"Cohen's kappa **{kappa:.4f}**\n")
    md.append("## Agreement by judge family\n")
    md.append(fam_df.to_markdown(index=False))
    md.append("\n## Tasks by |score delta| (new minus gpt-4o)\n")
    md.append(tasks_df.to_markdown(index=False))
    with open(os.path.join(args.out_dir, f"REPORT_{slug}.md"), "w") as f:
        f.write("\n".join(md) + "\n")

    print(f"tasks={len(tasks_df)} items={len(items):,}")
    print(f"per-task Pearson={r_task:.4f} Spearman={rho_task:.4f} mean|delta|={tasks_df['delta'].abs().mean():.4f}")
    print(f"per-item agreement={item_agree:.2%} | binary kappa={kappa:.4f} ({len(bins):,} items)")
    print("report:", os.path.join(args.out_dir, f"REPORT_{slug}.md"))


if __name__ == "__main__":
    main()
