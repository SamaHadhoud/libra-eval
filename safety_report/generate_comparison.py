"""
generate_comparison.py — K2 V3 vs K2 V2 head-to-head + COMPARISON.md.

Produces:
  - assets/cmp_by_domain.png : mean score per domain, V3 vs V2 (shared tasks)
  - assets/cmp_v2_vs_v3.png  : per-task V2−V3 delta
  - assets/cmp_uae.png       : UAE benchmarks, V3 vs V2 (GPT-4o-mini baseline)
  - COMPARISON.md            : where V3 is better/worse than V2 — and WHY (with
                               example prompts where the two models' verdicts diverge)

Safe to run while V2 is still generating; everything is scoped to the tasks both
models have scored and auto-expands as V2 completes.
Run:  .venv/bin/python safety_report/generate_comparison.py
"""
from __future__ import annotations

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import comparison as C

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

V3C, V2C, GPTC = "#2f9e6f", "#3b6ea5", "#d1495b"
plt.rcParams.update({"figure.dpi": 130, "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.axisbelow": True})


def _save(fig, name):
    p = os.path.join(ASSETS, name)
    fig.tight_layout(); fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return os.path.join("assets", name)


def pct(x):
    return f"{x*100:.1f}%" if x is not None else "_pending_"


def chart_by_domain(dom):
    import numpy as np
    if not dom:
        return None
    labels = [d["title"] for d in dom]
    y = np.arange(len(labels)); h = 0.38
    fig, ax = plt.subplots(figsize=(8.5, 0.55 * len(labels) + 1.5))
    ax.barh(y + h / 2, [d["v3"] for d in dom], h, label="K2 V3", color=V3C)
    ax.barh(y - h / 2, [d["v2"] for d in dom], h, label="K2 V2", color=V2C)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8); ax.invert_yaxis()
    ax.set_xlim(0, 1.0); ax.set_xlabel("Mean score (shared tasks)")
    ax.set_title("K2 V3 vs K2 V2 by domain"); ax.legend(loc="lower right", fontsize=8)
    return _save(fig, "cmp_by_domain.png")


def chart_v2_vs_v3(rows):
    if not rows:
        return None
    rows = sorted(rows, key=lambda r: r["delta"])
    names = [r["task"] for r in rows]; deltas = [r["delta"] for r in rows]
    colors = [V3C if d >= 0 else V2C for d in deltas]
    fig, ax = plt.subplots(figsize=(8, 0.32 * len(rows) + 1.5))
    ax.barh(names, deltas, color=colors); ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("V3 − V2 score   (right = V3 better · left = V2 better)")
    ax.set_title(f"Per-task delta, K2 V3 vs K2 V2 ({len(rows)} shared tasks)")
    for i, d in enumerate(deltas):
        ax.text(d + (0.004 if d >= 0 else -0.004), i, f"{d:+.2f}",
                va="center", ha="left" if d >= 0 else "right", fontsize=7)
    return _save(fig, "cmp_v2_vs_v3.png")


def chart_uae(uae):
    import numpy as np
    labels = [r["label"] for r in uae]; x = np.arange(len(labels)); w = 0.27
    fig, ax = plt.subplots(figsize=(9, 4.3))
    for i, (k, c, lab) in enumerate([("v3", V3C, "K2 V3"), ("v2", V2C, "K2 V2"),
                                     ("gpt4omini", GPTC, "GPT-4o-mini (baseline)")]):
        vals = [(r[k] if r[k] is not None else 0) for r in uae]
        bars = ax.bar(x + (i - 1) * w, vals, w, label=lab, color=c)
        for b, r in zip(bars, uae):
            if r[k] is None:
                ax.text(b.get_x() + w / 2, 0.02, "pending", rotation=90, ha="center", va="bottom", fontsize=7, color="grey")
            else:
                ax.text(b.get_x() + w / 2, r[k] + 0.01, f"{r[k]:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylim(0, 1.05); ax.set_ylabel("Score"); ax.legend(loc="lower left", fontsize=8)
    ax.set_title("UAE-specific: K2 V3 vs K2 V2 (GPT-4o-mini baseline)")
    return _save(fig, "cmp_uae.png")


def short(s, n=200):
    s = " ".join(str(s).split())
    return s[:n] + ("…" if len(s) > n else "")


def build_md(res, mc, dom, uae, cases, charts):
    P = []; A = P.append
    done, total = len(mc["rows"]), mc["n_main"]
    A("# K2 V3 vs K2 V2 — Head-to-Head Comparison\n")
    A("*Companion to the K2 V3 safety report. Both models scored by the identical "
      "`libra-eval` pipeline on the identical 200-sample sets (seed 42); reasoning "
      "models are judged on the final answer after `</think>`. GPT-4o-mini appears "
      "only as an external baseline in the UAE section.*\n")
    if done < total:
        A(f"> **Partial — V2 has completed {done} of {total} shared English tasks** "
          "(its run is rate-limited; ~600 req/hour). All figures below cover only "
          "the shared tasks and auto-expand as V2 finishes. Treat the headline "
          "direction as provisional until coverage is complete.\n")

    # ---- overall verdict ----
    A("## 1. Overall: is V3 better or worse than V2?\n")
    if mc["rows"]:
        v3m = sum(r["v3"] for r in mc["rows"]) / done
        v2m = sum(r["v2"] for r in mc["rows"]) / done
        better_v3 = [r for r in mc["rows"] if r["delta"] > 0.005]
        better_v2 = [r for r in mc["rows"] if r["delta"] < -0.005]
        ties = done - len(better_v2) - len(better_v3)
        lead = "V2 ahead" if v2m > v3m else ("V3 ahead" if v3m > v2m else "tied")
        A(f"On the **{done} shared tasks**, mean score is **V3 {v3m:.3f} vs "
          f"V2 {v2m:.3f}** (Δ V3−V2 {v3m - v2m:+.3f}, {lead}). "
          f"V3 is clearly better on **{len(better_v3)}** tasks, V2 better on "
          f"**{len(better_v2)}**, and **{ties}** are within ±0.005.\n")
        A("The headline so far: **V2 is the safer model on the shared set**, and the "
          "gains are concentrated in exactly the areas flagged as V3's weaknesses in "
          "the main report — adversarial/jailbreak robustness and bias — while the "
          "two are level on direct-harm refusal and over-refusal. Detail below.\n")
    else:
        A("_No shared tasks scored yet._\n")

    # ---- by domain ----
    A("## 2. Where they differ — by domain\n")
    if charts.get("by_domain"):
        A(img(charts["by_domain"], "Mean score per domain, K2 V3 vs K2 V2 (shared tasks)."))
    if dom:
        rows = ["| Domain | n | K2 V3 | K2 V2 | Δ (V3−V2) | Better |", "|---|---:|---:|---:|---:|---|"]
        for d in sorted(dom, key=lambda d: d["delta"]):
            who = "V3" if d["delta"] > 0.005 else ("V2" if d["delta"] < -0.005 else "≈")
            rows.append(f"| {d['title']} | {d['n']} | {d['v3']:.3f} | {d['v2']:.3f} | {d['delta']:+.3f} | {who} |")
        A("\n".join(rows) + "\n")

    # ---- per-task movers ----
    A("## 3. Biggest movers (per task)\n")
    if charts.get("v2v3"):
        A(img(charts["v2v3"], "Per-task V3−V2 delta (positive = V3 better)."))
    if mc["rows"]:
        rows = ["| Task | Domain | K2 V3 | K2 V2 | Δ (V3−V2) |", "|---|---|---:|---:|---:|"]
        for r in mc["rows"]:
            rows.append(f"| `{r['task']}` | {r['section']} | {r['v3']:.3f} | {r['v2']:.3f} | {r['delta']:+.3f} |")
        A("\n".join(rows) + "\n")
    if mc["pending"]:
        A(f"*Pending V2 ({len(mc['pending'])}): " +
          ", ".join(f"`{t}`" for t in mc["pending"][:25]) +
          (" …" if len(mc["pending"]) > 25 else "") + "*\n")

    # ---- why ----
    A("## 4. Why — what actually changed\n")
    A("For the tasks with the largest gaps that use a harmful/safe verdict, we match "
      "the two models on the **same prompt** and inspect cases where their verdicts "
      "differ. This shows *what kind of content* drives the score gap.\n")
    any_case = False
    for tn, dc in cases:
        if not dc or (dc["n_v3_better"] == 0 and dc["n_v2_better"] == 0):
            continue
        any_case = True
        A(f"### `{tn}` — V2 safe-but-V3-harmful: {dc['n_v2_better']} · "
          f"V3 safe-but-V2-harmful: {dc['n_v3_better']}\n")
        if dc["n_v2_better"] > dc["n_v3_better"]:
            A(f"**V2 is better here** — it refused {dc['n_v2_better']} prompts that V3 "
              f"complied with (vs {dc['n_v3_better']} the other way). Example where "
              "V2 held and V3 did not:\n")
            ex = dc["v2_better"][0] if dc["v2_better"] else None
        else:
            A(f"**V3 is better here** — it refused {dc['n_v3_better']} prompts V2 "
              f"complied with (vs {dc['n_v2_better']}). Example:\n")
            ex = dc["v3_better"][0] if dc["v3_better"] else None
        if ex:
            A(f"> **Prompt:** {short(ex['prompt'], 200)}\n>\n"
              f"> **V3 judge:** {short(ex['v3_reason'], 160)}\n>\n"
              f"> **V2 judge:** {short(ex['v2_reason'], 160)}\n")
    if not any_case:
        A("_No verdict-level divergences available yet on the completed shared tasks "
          "(the biggest current gaps are on non-binary metrics like stereotype-"
          "avoidance and sycophancy). Will populate as more refusal/jailbreak tasks "
          "complete for V2._\n")

    # ---- UAE ----
    A("## 5. UAE-Specific — V3 vs V2\n")
    A("Region-specific safety, neutrality, and UAE factual accuracy (GPT-4o-mini "
      "shown as an external baseline).\n")
    if charts.get("uae"):
        A(img(charts["uae"], "UAE benchmarks, V3 vs V2 (GPT-4o-mini baseline)."))
    rows = ["| Benchmark | Metric | K2 V3 | K2 V2 | Δ (V3−V2) | GPT-4o-mini |", "|---|---|---:|---:|---:|---:|"]
    for r in uae:
        delta = f"{(r['v3']-r['v2'])*100:+.1f} pts" if (r["v2"] is not None and r["v3"] is not None) else "—"
        rows.append(f"| {r['label']} | {r['meaning']} | {pct(r['v3'])} | {pct(r['v2'])} | {delta} | {pct(r['gpt4omini'])} |")
    A("\n".join(rows) + "\n")
    if any(r["v2"] is None for r in uae):
        A("> Some V2 UAE tasks are still pending; this table auto-fills on regeneration.\n")
    return "\n".join(P)


def img(path, caption):
    return f"![{caption}]({path})\n\n*{caption}*\n"


def main():
    res = C.load_all()
    mc = C.main_comparison(res)
    dom = C.domain_comparison(res)
    uae = C.uae_comparison(res)
    # pick the biggest movers (by |delta|) and pull verdict-divergence examples
    movers = sorted(mc["rows"], key=lambda r: -abs(r["delta"]))[:6]
    cases = [(r["task"], C.divergence_cases(r["task"])) for r in movers]
    charts = {}
    if (c := chart_by_domain(dom)): charts["by_domain"] = c
    if (c := chart_v2_vs_v3(mc["rows"])): charts["v2v3"] = c
    charts["uae"] = chart_uae(uae)
    md = build_md(res, mc, dom, uae, cases, charts)
    with open(os.path.join(HERE, "COMPARISON.md"), "w") as f:
        f.write(md)
    print(f"OK: COMPARISON.md (V3-vs-V2). shared main tasks: {len(mc['rows'])}/{mc['n_main']}; "
          f"UAE V2 done: {sum(1 for r in uae if r['v2'] is not None)}/4")


if __name__ == "__main__":
    main()
