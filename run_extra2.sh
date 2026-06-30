#!/usr/bin/env bash
set -uo pipefail
REPO="/Users/sama/Documents/LIBRAI/libra-eval"; cd "$REPO" || exit 1
PY="$REPO/.venv/bin/python3"; MODEL="k2moe375B-mid3_v3-checkpoint_0003500"
OUT="$REPO/outputs_full_200"; LOG="$REPO/run_extra2.log"
echo "=== EXTRA2 START $(date) ===" | tee "$LOG"
"$PY" -m libra_eval.run_eval --client local --models "$MODEL" \
  --tasks case_bench,stealth_graph --n_samples_per_task 200 --mode full --evaluator llm \
  --generation_params '{"max_tokens": 8192}' --output_dir "$OUT" 2>&1 | tee -a "$LOG"
RC=${PIPESTATUS[0]}
echo "EXTRA2_DONE rc=$RC $(date)" > "$OUT/EXTRA2_DONE.txt"
echo "=== EXTRA2 FINISHED rc=$RC $(date) ===" | tee -a "$LOG"
