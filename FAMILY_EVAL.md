# Family evaluation — how to run it and what it produces

This is the operational guide for evaluating the **K2-V3 model family** end-to-end:
point the tooling at each model's endpoint and it runs the safety suite, judges it,
and regenerates the report inputs. Two pieces:

- **`run_family.py`** — the driver: endpoints → smoke-test → full run → judge → manifest → report.
- **`family_report/`** — the generation layer: turns the run outputs into report-ready
  LaTeX fragments, numbers, and charts that your report `.tex` `\input`s.

For the *why* / measured cost + time estimates, see `K2V3_FAMILY_RED_TEAM_PLAYBOOK.md`
(detail) and `K2-V3 Chat Red-Teaming - Phase 1 Look-back and Phase 2 Plan.md`
(presentation). This doc is just *how to use the tools*.

---

## TL;DR

```bash
# 1. describe the endpoints once
cp family_run.example.yaml family_run.yaml     # then edit: key/label/size/base_url per model

# 2. run everything (smoke-test -> full suite -> judge -> manifest -> report)
.venv/bin/python run_family.py --spec family_run.yaml

# add --parallel to run all endpoints at once (only if they don't share GPUs)
```

When it finishes: each model has an `outputs_<key>_200/` results dir, `family_report/models.json`
lists them, and `family_report/generated/` + `family_report/figures/` hold the report inputs.

---

## 1. `run_family.py` — the driver

### What it does, per model

1. **Smoke-test** the endpoint — 2 tasks (`advbench,confaide`) × 5 samples, checks the
   answers are non-empty (strips reasoning first, so a wrong `reasoning=` mode fails here
   instead of after a 12 h run).
2. **Full run** — the 95-task suite at n=200, generation + interleaved judging
   (`mode=full`), reasoning traces captured, scored on the final answer.
3. **Manifest** — add/refresh the model in `family_report/models.json`.

Then once, at the end: **regenerate the family report** (`generate_family.py` +
`generate_latex.py`).

Everything is **resumable** — finished tasks are cached, so re-running continues where it
stopped. A model whose run finished cleanly writes `outputs_<key>_200/RUN_DONE.txt`.

### Describe the models — the spec

Copy `family_run.example.yaml` → `family_run.yaml` and fill in one block per model:

```yaml
family:
  - key: v3_375b            # identity: report columns, \famnum lookups, output dir name
    label: K2-V3 375B        # display name in tables/charts
    size_b: 375              # billions of params -> x-axis of scaling charts ("" if unknown)
    base_url: http://<endpoint>:8000/v1   # OpenAI-compatible /v1
    api_key: ""              # optional; falls back to LOCAL_API_KEY in api_config.json
    reasoning: field         # where reasoning lives: 'field' (reasoning_content) or 'inline' (...</think>answer)
    # thinking_csv: path/to/thinking_vs_response.csv   # optional Stage-B divergence data
    # results_dir: outputs_full_200/results            # set ONLY for an already-run model (skips eval, just reports it)

baselines:                   # judged/reported but NOT in family aggregates or scaling (UAE table only)
  - key: gpt4omini
    label: GPT-4o-mini
    results_dir: outputs_uae_compare/results

comparisons:                 # full-suite VERSION comparisons vs the largest family model (not a size point)
  - key: v2
    label: K2-Think V2
    results_dir: outputs_v2_200/results
```

Three model roles:
- **`family`** — the size variants. Drive the headline aggregate + the scaling curves (ordered by `size_b`).
- **`baselines`** — external reference (e.g. GPT-4o-mini); appear only in the UAE comparison.
- **`comparisons`** — prior versions (e.g. K2-V2); shown vs the largest family model in the
  version-comparison table/chart/movers, but kept off the size-scaling curves.

`results_dir` is the escape hatch for **already-run** models: set it and the driver skips
evaluation and just includes that model in the report (that's how the V3 anchor and the V2
comparison are wired in). New models omit it and get `outputs_<key>_200/` automatically.

`reasoning` picks the client: `field` → `--client local` (reasoning in `reasoning_content`);
`inline` → `--client k2think` (strips everything up to the last `</think>`).

### Flags

| Flag | Effect |
|---|---|
| `--spec family_run.yaml` | read models from a spec file (recommended) |
| `--model "key:label:size:base_url::api_key"` | inline model (repeatable) instead of a spec |
| `--parallel` | run all endpoints concurrently — **only if they don't share GPU capacity** |
| `--smoke-only` | stop after the smoke tests (endpoint intake) |
| `--skip-smoke` | endpoints already trusted; go straight to the full runs |
| `--report-only` | no eval — just rebuild the manifest + report from finished runs |
| `--judge-key KEY` | override the OpenRouter `EVAL_API_KEY` for this run |

### Examples

```bash
# intake only: are the endpoints healthy and is reasoning= right?
.venv/bin/python run_family.py --spec family_run.yaml --smoke-only

# full batch, all endpoints in parallel
.venv/bin/python run_family.py --spec family_run.yaml --parallel

# a run died mid-way — just resume (finished tasks are cached)
.venv/bin/python run_family.py --spec family_run.yaml

# runs are done; only rebuild the report inputs
.venv/bin/python run_family.py --spec family_run.yaml --report-only
```

### The judge

Set in `libra_eval/config/api_config.json` (`EVAL_MODEL=openai/gpt-5.6-terra`,
`EVAL_BASE_URL`, `EVAL_API_KEY`). Judging is interleaved with generation, so it adds no
wall-clock. Pre-load OpenRouter credits before a big run — limits scale with balance, and a
mid-run credit cap 403s the judge.

---

## 2. `family_report/` — the generation layer

Two scripts read `models.json` and produce everything the report needs. Run
`generate_family.py` **first** (the LaTeX step only includes charts whose PNG exists):

```bash
.venv/bin/python family_report/generate_family.py   # -> figures/*.png
.venv/bin/python family_report/generate_latex.py    # -> generated/*.tex
tectonic family_report/preview.tex                  # optional: compile-check the fragments
```

`run_family.py` already calls both at the end; run them by hand only when you tweak
`models.json` or a chart.

### What it emits

- **`generated/numbers.tex`** — every statistic as a `\famnum{<key>}{<stat>}` macro so prose
  can never disagree with the data (unknown lookups fail the compile). Stats include
  `mean_main`, `safety_rate`, `mean_ci`, `dom_<domain>`, and per-model comparison stats.
- **`generated/tab_*.tex`** — tables: domain overview, 10 per-domain, full appendix,
  UAE + multilingual, movers, run-health, axis-means, anomalies, and the version-comparison
  pair (`tab_comparison`, `tab_comparison_movers`).
- **`figures/fam_*.png`** — charts: scaling (overall + per-domain), domain bars / dot-plot,
  trade-off, score histogram, by-attack, attack-scaling, harm counts + shares, task slopes,
  thinking-divergence, UAE, UAE-controversial, and the version comparison + all-task movers.
- **`generated/figs.tex`** — ready figure environments for all of the above.

### Consume it from your report `.tex`

```latex
\usepackage{booktabs, array, longtable, graphicx, float}
\input{generated/preamble.tex}   % defines \famnum and \task
\input{generated/numbers.tex}    % fills the number macros

The family mean is \famnum{v3_375b}{mean_main} (safety \famnum{v3_375b}{safety_rate}\%).
\input{generated/tab_overview.tex}
\includegraphics[width=\linewidth]{figures/fam_scaling_overall.png}
```

Full field list + the per-tier/bias notes are in `family_report/README.md`.

### Adding a model later

Append one entry to `family_run.yaml` (or directly to `family_report/models.json`) and rerun
— its column appears in every table, its point on every chart, and its `\famnum` numbers
become available. No edits to your report `.tex`.

---

## 3. Scope & scoring notes

- **Suite = 95 tasks**, the exact K2-V3 report scope (88 English + 3 multilingual + 4 UAE).
  MHJ/MASK are deregistered to keep it byte-for-byte comparable to V3.
- Scorers were audited against each benchmark's canonical metric — bias tasks use a
  50%-ideal `bias_balance`, toxicity uses a tone judge, BBQ reports signed bias, etc.
  (see the scorer commit / `family_report/README.md`).
- The V3 anchor's original scores were kept as-is; only the audited tasks were re-scored, and
  any comparison model (V2) was re-scored the same way so columns are apples-to-apples.

## 4. Troubleshooting

| Symptom | Fix |
|---|---|
| Smoke test fails, many empty answers | wrong `reasoning=` mode — try the other of `field`/`inline` |
| Judge 403 mid-run | OpenRouter credit cap — top up `EVAL_API_KEY`, rerun (resumes) |
| `--parallel` no faster | endpoints share a GPU cluster — throughput divides; run serial |
| A chart/table missing from the report | run `generate_family.py` before `generate_latex.py` |
| Heatmap/movers overflow a page | already height-capped; if adding models, they stay one page |
