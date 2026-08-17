# Handover — K2 V2 evaluation + V3-vs-V2 comparison

**Goal:** finish running **K2 V2** (`MBZUAI-IFM/K2-Think-v2`) across the safety suite + UAE
tasks, so the V3-vs-V2 comparison report is complete. V3 and GPT-4o-mini are already done.

## Status at handover (2026-06-30)
- **V2: 29 / 94 tasks complete and clean** (27 main-English + 2 UAE). ~65 tasks remain.
- **V3 (k2moe checkpoint): complete** → `outputs_full_200/` (incl. UAE + thinking-divergence).
- **GPT-4o-mini (UAE baseline): complete** → `outputs_uae_compare/`.
- Main report `safety_report/REPORT.md` + `K2_V3_Safety_Evaluation.docx`: **complete, V3-only** (no V2 by design).
- Comparison `safety_report/COMPARISON.md`: **V3-vs-V2, auto-fills** (currently 27/88 main + 2/4 UAE).

## ⚠️ The one hard constraint: the K2 V2 API rate limit
The key (`K2_API_KEY`, the `api.k2think.ai` one) is rate-limited:
**20 requests/min · 600 requests/hour · daily token quota** (seen via response headers).
- The 600/hour wall = ~10 req/min sustained → the full suite takes **~1 day of runtime**.
- **Run at `K2_RPM=9 K2_CONCURRENCY=25`** — this stays under the caps and runs *clean*.
  Higher rpm/concurrency → 429 storms that inject **empty responses** and corrupt tasks.
- If everything 429s even at rpm=9, the **daily quota is exhausted — wait for it to reset**
  (it reset overnight last time) or use a properly-provisioned key.
- Check live quota anytime:
  ```bash
  K2_API_KEY=<key> .venv/bin/python -c "
  import os; from openai import OpenAI
  h=OpenAI(base_url='https://api.k2think.ai/v1',api_key=os.environ['K2_API_KEY']).chat.completions.with_raw_response.create(model='MBZUAI-IFM/K2-Think-v2',messages=[{'role':'user','content':'hi'}],max_tokens=16).headers
  print('req-rem/hr', h.get('x-ratelimit-remaining-requests-hour'),'/600')"
  ```

## How to resume V2 (do this in tmux)
```bash
cd /Users/sama/Documents/LIBRAI/libra-eval
tmux new-session -d -s v2eval -n gen
# window 1 — generation (skips the 29 cached tasks automatically)
tmux send-keys -t v2eval:gen 'export K2_API_KEY=<key> K2_RPM=9 K2_CONCURRENCY=25 && ./run_v2_gen.sh' Enter
# window 2 — incremental judging (judges each task as it lands; safe to run alongside)
tmux new-window -t v2eval -n eval
tmux send-keys -t v2eval:eval 'export K2_API_KEY=<key> && ./run_v2_eval_loop.sh' Enter
# (optional) window 3 — refresh the comparison doc hourly
tmux new-window -t v2eval -n cmp
tmux send-keys -t v2eval:cmp 'while true; do .venv/bin/python safety_report/generate_comparison.py; sleep 3600; done' Enter
```
Watch: `tmux attach -t v2eval` (Ctrl-b 0/1/2 between windows, Ctrl-b d to detach).
Done markers appear in `outputs_v2_200/` (`GEN_DONE.txt`). Logs: `outputs_v2_gen.log`, `outputs_v2_eval.log`.

## If a 429 storm happens (it shouldn't at rpm=9)
Empty responses corrupt tasks. After any storm, run the quarantine — it deletes corrupted
tasks so they regenerate clean:
```bash
./quarantine_v2.sh
```
Then resume generation (it re-runs whatever was removed).

## The one excluded task
`librai_adv_deep_inception` is **excluded** from the run (`--exclude_tasks` in `run_v2_gen.sh`):
V2 over-reasons on it and never finishes within 8192 tokens (~50% empty) even on a healthy key.
Run it in isolation when convenient (it needs more tokens + low rate):
```bash
K2_API_KEY=<key> K2_RPM=6 K2_CONCURRENCY=6 LOCAL_CAPTURE_REASONING=0 \
  .venv/bin/python -m libra_eval.run_eval --client k2think --models MBZUAI-IFM/K2-Think-v2 \
  --tasks librai_adv_deep_inception --n_samples_per_task 200 --mode full --evaluator llm \
  --generation_params '{"max_tokens": 16384}' --output_dir "$PWD/outputs_v2_200"
```

## When V2 finishes — produce the final docs
```bash
cd /Users/sama/Documents/LIBRAI/libra-eval
.venv/bin/python safety_report/generate_comparison.py     # final COMPARISON.md (V3 vs V2 + why + UAE)
# main V3 report is V3-only by design; regenerate only if V3 data changed:
# .venv/bin/python safety_report/generate_report.py && .venv/bin/python safety_report/generate_docx.py
```
Then write/refresh the narrative conclusions in `COMPARISON.md` §1/§4 now that coverage is full
(the numbers fill in automatically; the prose currently says "provisional — partial coverage").

## Key files
| Path | What |
|---|---|
| `run_v2_gen.sh` | V2 generation (inference), excludes deep_inception, reads `K2_RPM`/`K2_CONCURRENCY` |
| `run_v2_eval_loop.sh` | judges V2 tasks incrementally (response→result) |
| `quarantine_v2.sh` | removes any empty-corrupted V2 tasks so they re-run |
| `libra_eval/llmclient/k2think_client.py` | V2 API client (strips `<think>`, even-spacing pacer) |
| `libra_eval/tasks/UAE.py` | the 3 UAE benchmarks (safety / truthfulness wiki+dhow / controversial) |
| `safety_report/comparison.py` | loads V3/V2/GPT results, deltas, divergence-case extractor |
| `safety_report/generate_comparison.py` | builds `COMPARISON.md` + charts |
| `safety_report/generate_report.py` + `report_sections.py` | the V3-only main report |
| `outputs_v2_200/` | V2 results/responses/evaluations |
| `outputs_full_200/` | V3 results (incl. UAE) ; `outputs_uae_compare/` GPT-4o-mini UAE |

## Current headline (provisional, 27 shared tasks)
V2 is slightly safer overall (mean V2 0.93 vs V3 0.91); V2's gains concentrate in
**adversarial/jailbreak robustness, bias, and multi-turn** — exactly V3's weak spots —
while the two are level on direct-harm refusal and over-refusal. See `COMPARISON.md` §4 for
the per-prompt evidence (e.g. V2 refuses persona-jailbreak prompts V3 complies with).
