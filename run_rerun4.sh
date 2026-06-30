#!/usr/bin/env bash
set -uo pipefail
REPO="/Users/sama/Documents/LIBRAI/libra-eval"; cd "$REPO" || exit 1
PY="$REPO/.venv/bin/python3"; MODEL="k2moe375B-mid3_v3-checkpoint_0003500"
OUT="$REPO/outputs_full_200"; LOG="$REPO/run_rerun4.log"
echo "=== RERUN4 START $(date) ===" | tee "$LOG"
caffeinate -i "$PY" -m libra_eval.run_eval --client local --models "$MODEL" \
  --tasks aya_redteaming,bbq,realtoxicityprompts,xsafety --n_samples_per_task 200 --mode full --evaluator llm \
  --generation_params '{"max_tokens": 8192}' --output_dir "$OUT" 2>&1 | tee -a "$LOG"
RC=${PIPESTATUS[0]}
echo "RERUN4_DONE rc=$RC $(date)" > "$OUT/RERUN4_DONE.txt"
echo "=== RERUN4 FINISHED rc=$RC $(date) ===" | tee -a "$LOG"
