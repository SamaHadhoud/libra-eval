# K2-V3 Family Red-Teaming Playbook

**Purpose:** reproduce the full set of scores in the K2-V3 chat red-teaming reports
(`safety_report/REPORT.md`, `K2-V3-Chat-Red-Teaming/main.tex`, `safety_report/COMPARISON.md`)
for the K2-V3 family models (4–5 sizes), given only each model's inference endpoint. Includes resource and
time estimates for a 5-model batch and a parallelization plan.

Everything below was actually done for K2-V3 (`k2moe375B-mid3_v3-checkpoint_0003500`) and
K2-V2 (`MBZUAI-IFM/K2-Think-v2`); the numbers quoted (durations, request counts) are measured
from those runs, not guesses.

---

## 1. What the K2-V3 score set consists of

The "scores in the K2-V3 reports" are produced by **four pipeline stages**. Only Stage A is
strictly required for the headline numbers; B–D fill the remaining report sections.

| Stage | What | Output | Report section |
|---|---|---|---|
| **A. Main suite** | 95 tasks × n=200 (the exact V3 report scope), generation (reasoning captured) + LLM judging on the final answer | `outputs_<model>/results/*.json` | §5–§6 domain tables, headline mean 0.914 / safety 96.9% |
| **B. Thinking-vs-answer divergence** | Judge the Stage-A reasoning traces and answers separately (judge-only; no extra generation) | `harmful_check_analysis_*/` | §7 (divergence + reasoning-activation) |
| **C. UAE 3-way baseline** | Each new model answers the 4 UAE tasks **inside Stage A** (they are 4 of the 95 — generation and judging already in its cost/time); the comparison's other legs — GPT-4o-mini (`outputs_uae_compare/`, all 4 results cached) and V3 (`outputs_full_200/`) — are frozen and reused, $0 | `outputs_uae_compare/` | §8 |
| **D. Family report results layer** | **BUILT (`family_report/`):** manifest-driven generation of every report number (`\famnum` LaTeX lookups), 16 table fragments, and 5 cross-size charts; add a model to `models.json`, rerun 2 scripts | `family_report/generated/` + `figures/` | whole report |

Task inventory (family suite, 95 tasks — identical to the V3 report scope so every score is
apples-to-apples): 88 main-English (the headline aggregate), 3 multilingual (`xsafety`,
`aya_redteaming`, `librai_adv_multilingual`), 4 UAE (`uae_safety`,
`uae_truthfulness_wiki/dhow`, `uae_controversial`). The 3 tasks added to the repo after
the V3 report (`mhj`, `mask_provided_facts`, `mask_known_facts`) are **deregistered by
decision** (commented out in `libra_eval/tasks/__init__.py` — V3 never ran them, so they'd
break comparability): `--tasks all` therefore means exactly these 95 on every run, no
exclude flag needed. Task code + datasets are kept, judge-validated; uncomment to re-enable
for a future full-family run. Judge = `openai/gpt-5.6-terra` via OpenRouter (upgraded from
gpt-4o 2026-08: 0.93 correlation / 95% agreement so scores don't move, stricter, ~35%
cheaper; the V3 anchor's stored scores remain gpt-4o-judged).

Measured volume per model (Stage A, 95-task scope): **17,825 generation requests** and
**14,859 LLM-judge calls** (most tasks at n=200, some datasets smaller; 15 tasks are scored
programmatically, no judge). Stage B adds **12,232 judge calls but zero generations**: since 2026-08-10 the pipeline stores the reasoning trace in
the response files (`<think_fast>…</think_fast>` prefix) while all scoring — LLM judge,
programmatic scorers, and the empty-response retry logic — sees only the stripped final
answer (`strip_reasoning` in `libra_eval/tasks/base.py`). One generation run serves both
stages. (V3 did Stage B as a separate 12,232-generation re-run because its main outputs
predate this; scores are unaffected — judges saw final-answer-only either way.)
Disk: ~250 MB/model.

---

## 2. One-time setup (already done in this repo)

- Python env: `.venv` (`pip install -r requirement.txt` + `pip install -e .`).
- `libra_eval/config/api_config.json`:
  - `LOCAL_BASE_URL` / `LOCAL_API_KEY` — the model endpoint (OpenAI-compatible `/v1`).
  - `EVAL_MODEL=openai/gpt-5.6-terra`, `EVAL_BASE_URL=https://openrouter.ai/api/v1`,
    `EVAL_API_KEY` — the judge.
  - `REQUEST_TIMEOUT=150`, `REQUEST_NUM_RETRIES=4` — **required** for reasoning models
    (uncapped reasoning otherwise stalls requests for ~6 min each).
- Datasets: all in `libra_eval/datasets/` (MHJ/MASK rebuildable via
  `build_mhj_mask_datasets.py`, needs a HF token with `ScaleAI/mhj` + `cais/MASK` terms accepted).
- Scorer fixes (sycophancy-mimicry judge, ConfAIde routing, harmful-judge V6,
  prompt-hijacking crash fix) are all committed — nothing to redo.

---

## 3. Step-by-step: score one new model, given its endpoint

### Step 0 — Endpoint intake & smoke test (manual, ~1–2 h; the step that bites)
1. Confirm the endpoint is OpenAI-compatible chat-completions (`/v1/chat/completions`).
2. **Find where the reasoning lives.** Every K2 model so far was a reasoning model, but the
   two we've seen differ:
   - V3-style: reasoning in `message.reasoning_content` / `message.reasoning`, final answer
     in `content` → use `--client local` (already handles it; `LOCAL_CAPTURE_REASONING=0`
     gives final-answer-only, which is what the main run must use).
   - V2-style: reasoning inline in `content` as `...</think>answer` → use `--client k2think`
     (strips everything up to the last `</think>`; endpoint via `K2_BASE_URL`/`K2_API_KEY` env).
   - Anything else → small new client subclassing `OpenAI_Client` (~1 h, copy `k2think_client.py`).
3. Probe rate limits **before** the full run (this cost us ~8 h of corrupted V2 runs once):
   sustained 10–15 min burst at the concurrency you plan to use, watch for 429s/empties.
   `x-ratelimit-*` headers, if present, tell you the caps (probe snippet in `V2_HANDOVER.md`).
4. Smoke test: `--tasks advbench,confaide --n_samples_per_task 5 --mode full` into a scratch
   dir; read the responses by eye (non-empty, no leaked reasoning, judge verdicts sane).

### Step 1 — Main suite, generation + judging (automated, ~12 h wall-clock)
**The whole flow is driven by `run_family.py`** (smoke → full run → manifest → report). List
the endpoints in `family_run.yaml` (copy `family_run.example.yaml`), then:

```bash
.venv/bin/python run_family.py --spec family_run.yaml            # all models, serial
.venv/bin/python run_family.py --spec family_run.yaml --parallel # concurrent (independent GPUs)
.venv/bin/python run_family.py --spec family_run.yaml --smoke-only   # Step 0 only
```

Under the hood each model runs (the driver sets `LOCAL_BASE_URL`/`K2_*` per endpoint via env):

```bash
.venv/bin/python -m libra_eval.run_eval \
    --client local --models "<MODEL_ID>" \
    --tasks all --n_samples_per_task 200 --mode full --evaluator llm \
    --generation_params '{"max_tokens": 8192}' \
    --output_dir "$PWD/outputs_<model>_200"
```

Non-negotiables learned the hard way (all handled by the driver, but true if run by hand):
- `--output_dir` **absolute** (relative paths resolve inside the `libra_eval/` module dir).
- `max_tokens: 8192` cap (reasoning runaway otherwise) — and note the known caveat: the cap
  slightly inflates safety on 2 jailbreak tasks (truncation artifact, documented in report §7).
- Leave reasoning capture **ON** (the `local` client default). Response files keep the
  `<think_fast>` trace for Stage B; scoring automatically strips it, and a trace whose final
  answer is empty (runaway reasoning) is correctly treated as an empty response and retried.
  If the endpoint returns reasoning some other way (inline `</think>` etc.), fix it at the
  client level first (Step 0.2).
- For a rate-limited API endpoint, split gen/judge like V2 instead: `run_v2_gen.sh`
  (mode=inference) + `run_v2_eval_loop.sh` (incremental judging) so judging never waits.

### Step 2 — Mid-run hygiene (manual, ~1 h spread over the run)
- `tail -f` the log; watch for empty-response streaks (endpoint outage or 429 storm).
- If a storm happens, quarantine corrupted tasks so resume regenerates them (adapt
  `quarantine_v2.sh` — resume checks file *existence*, not content, so a corrupted file is
  otherwise skipped forever).
- If the judge key 403s (OpenRouter credit cap), top up / swap `EVAL_API_KEY` and re-judge
  the affected tasks (`--mode evaluation` re-runs only responses→results; pattern in
  `rejudge_pending25.sh`).

### Step 3 — Sanity-check the scores (manual, ~2–3 h)
- `python analyze_task.py <task> outputs_<model>_200` for every task scoring < ~0.8: read
  ~10 failing samples, decide **model finding vs scorer artifact**. For V3 this is what
  caught all the scorer bugs; those are fixed now, so expect model findings only.
  Reference for known task quirks/labels: `VALIDATION_NOTES.md`.
- Check empty-response rate per task (should be ≤ ~1–3%).

### Step 4 — Thinking-vs-answer divergence (optional, judge-only, ~2–4 h)
No re-generation: the Stage-A response files already contain the traces. Point the
harmful-check at the main output dir, restricted to the 65 safety/adversarial tasks
(task list in `run_thinking_stage1.sh`):

```bash
# harmful check on trace + answer separately, then divergence analysis
./run_thinking_stage2.sh   # adapt --responses_dir to outputs_<model>_200/responses
                           # batch_harmful_check.py --resume --retry-failed → analyze
```

Gotcha: `batch_harmful_check.py --resume` alone skips error rows — always add
`--retry-failed`. (The V3-era regen scripts `run_thinking_stage1.sh`/`_thinking_clean.py`
are obsolete for new models — traces now come free with Stage A.)

### Step 5 — Reports (automated — pipeline built 2026-08-17, see `family_report/README.md`)
**Decided: ONE family report covering all sizes** (per-model columns/curves), no per-model
reports. The results layer is fully automated in `family_report/`:
- Add the model to `family_report/models.json` (key, label, size_b, results_dir), then:
  ```bash
  .venv/bin/python family_report/generate_latex.py    # \famnum numbers + 16 table fragments
  .venv/bin/python family_report/generate_family.py   # 5 cross-size charts (scaling,
                                                      #   domain bars, trade-off, heatmap)
  ```
  The model's column appears in every table, its point on every chart, and
  `\famnum{<key>}{<stat>}` numbers become available to the report prose. Unknown lookups
  fail the compile loudly, so prose can never cite a stale number. Generated V3 numbers
  were verified identical to the published `report_data.json`.
- The report .tex itself (new project, human-authored) only `\input`s fragments — see
  `family_report/README.md` for the preamble lines and available stats.
- Legacy per-model generators (`safety_report/generate_report.py` → REPORT.md/docx,
  `generate_comparison.py` → V3-vs-V2 COMPARISON.md) still work for V3 but are not part
  of the family flow.

---

## 4. Resource estimates — 5 models

### Judge API (OpenRouter) — the only real money
Computed exactly from the stored V3 run (actual judge messages + actual verdict lengths) at
gpt-4o's $2.50/M in, $10/M out. **The judge is now gpt-5.6-terra, ~35% cheaper, so these are
conservative upper bounds** (multiply by ~0.65 for the terra estimate). Of the 17,825 eval
rows, only **14,859 hit the LLM judge** — 15 tasks (MCQ/programmatic) are scored locally for
free. Stage A judge input measured at ~14M tokens/model, output ~0.7M; Stage B (12,232
harmful checks incl. full reasoning traces + 617-token template) ~24M in / ~4.8M out:

| Item | Per model | 5 models |
|---|---|---|
| Stage A judging (14.9k calls) | ~$40–50 | ~$200–250 |
| Stage B harmful checks (12.2k calls) | ~$100–130 | ~$500–650 |
| Retries / re-judges headroom (~15%) | ~$20–25 | ~$100–130 |
| **Total** | **~$160–200** | **~$800–1,000** |

**Why Stage B costs more than Stage A despite fewer calls:** Stage A judges only the short
final answer (traces are stripped before judging) and returns a compact ~40-token verdict.
Stage B reads the *full reasoning trace* (avg ~4.9k chars) and writes a structured two-part
analysis of thinking and answer (~400 tokens out per call) — and output tokens cost 4× input
($10/M vs $2.50/M), so Stage B's verdicts alone (~$48/model) exceed Stage A's entire input
bill. *Optional saving: screen with GPT-4o-mini and escalate only flagged cases to GPT-4o —
Stage B drops to ~$10–20/model, at the price of the divergence numbers no longer being
judge-identical to V3's (its divergence rate was <1%, so escalations would be rare).*

Caveat: Stage B scales with how long the *new* models' reasoning traces run (bounded by the
8192-token cap); V3 is the baseline. **Recommendation: pre-load the OpenRouter key with
~$400 (Stage A only) or ~$1,000 (full set).** Two V3-era incidents were mid-run 403 credit
caps — top up *before* starting, and note OpenRouter rate limits scale with account balance,
which matters at 5× traffic.

### Model endpoints (their infra, our load)
Per model: 17,825 chat requests at `max_tokens=8192` (Stage B adds none). Typical response
1–3k tokens ⇒ roughly 25–60M generated tokens/model. Sustained concurrency used historically:
~40 in-flight (API) or whatever the vLLM server batches (local). Each endpoint must survive
~12 h of continuous load; mid-run outages are recoverable (resume) but cost wall-clock.

### Harness machine
One Mac/Linux box runs all 5: the harness is async HTTP + JSONL writing (I/O-bound, ~zero
GPU/CPU). Disk ~200 MB/model (+180 MB for Stage B). tmux, one session per model.

---

## 5. Time estimates — 5 models

### Automated wall-clock (measured baselines: V3 local = 12.2 h for Stage A; V2 API,
latency-bound at conc 40 ≈ 10–15 h. Stage B is now judge-only — V3's separate 21 h
regen run is no longer needed since traces are captured during Stage A)

| | All 5 in parallel | Serial |
|---|---|---|
| Stage A (main scores) | **~12–15 h (≈1 day)** | ~2.5–3 days |
| Stage B (divergence, judge-only) | +~2–4 h | +~1 day |
| **Total automated** | **~1 day** | ~3–4 days |

Judging never adds wall-clock: it runs concurrently with generation (eval-loop pattern).

### Manual / human time

| Task | Effort |
|---|---|
| **One-time prep remaining** (per-model base-URL env override in `local_client`, 5 run scripts — the report-generation pipeline is already built: `family_report/`) | ~0.5–1 day |
| Per model: endpoint intake + smoke test + rate probe (Step 0) | ~1–2 h |
| Per model: run babysitting + quarantine (Step 2) | ~1 h |
| Per model: score sanity pass (Step 3) | ~2–3 h |
| Per model: report review | ~1 h |
| **Per-model subtotal** | **~5–7 h ⇒ ~3–4 person-days for 5** |
| Family report writing (prose/structure only — all numbers, tables, and charts auto-generate from `family_report/`) | ~1–2 days |
| **Grand total human effort** | **~5–7 person-days** |

**End-to-end calendar estimate: ~2 work weeks (10 working days).** Week 1: prep, endpoint
intake, parallel runs (mostly overnight), Stage B judging, sanity passes → all scores final.
Week 2: family report prose (the results layer — numbers, tables, charts — regenerates from
`family_report/` automatically) plus buffer for the real-world frictions — staggered
endpoint delivery, rate-limit storms, re-runs, judge-key top-ups (V2's rate-limit storms
alone cost ~2 elapsed days). Serial runs eat into the same buffer rather than extending
the estimate.

---

## 6. Can we run all 5 in parallel? Yes, with three caveats

1. **Per-model endpoint config — DONE.** `local_client.py` now reads `LOCAL_BASE_URL`/
   `LOCAL_API_KEY` from the environment first (falling back to `api_config.json`), so each
   process targets its own endpoint; `run_family.py --parallel` sets these per model and runs
   one thread per endpoint. Output dirs are per-model, so results never collide.
2. **Shared judge key.** 5 parallel runs ≈ 74k judge calls hitting one OpenRouter key
   (~135k including Stage B). Top
   up credits first (limits scale with balance); if judging still throttles, judging is
   resumable — let generation finish and let the eval loops drain afterwards.
3. **Shared GPU cluster?** Parallelism only helps if the 5 endpoints don't share the same
   serving capacity. If they're 5 deployments on one cluster, generation throughput divides
   and parallel ≈ serial for Stage A — ask the model team.

Recommended layout: one tmux session per model, each with a `gen` window and an `eval`-loop
window (the V2 pattern in `V2_HANDOVER.md`), plus a comparison-refresh window.

---

## 7. Open questions before the 5-model batch starts

1. **Endpoint shape:** OpenAI-compatible? Where does the reasoning live (`reasoning_content`
   field vs inline `</think>`)? Any rate limits / shared cluster? (Determines Step 0 effort
   and whether parallel actually parallelizes.)
2. **Score scope:** Stage A only (headline + domain tables), or the full report set incl.
   thinking-divergence (Stage B adds no generation, only ~$100–130/model of judge cost)?
3. **Judge budget:** OK to load ~$400–1,000 onto the OpenRouter key up front?
4. **n=200 again?** (Everything above assumes yes, for comparability with V3/V2.)
5. ~~Report format~~ **Decided:** one family report covering all sizes; no per-model reports.
