#!/usr/bin/env bash
# Run each remaining task in its OWN process so memory is released between them.
set -uo pipefail
REPO="/Users/sama/Documents/LIBRAI/libra-eval"; cd "$REPO" || exit 1
PY="$REPO/.venv/bin/python3"; MODEL="k2moe375B-mid3_v3-checkpoint_0003500"
OUT="$REPO/outputs_full_200"; LOG="$REPO/run_each3.log"
echo "=== EACH3 START $(date) ===" | tee "$LOG"
for T in aya_redteaming bbq realtoxicityprompts; do
  echo "=== $T start $(date) ===" | tee -a "$LOG"
  caffeinate -i "$PY" -m libra_eval.run_eval --client local --models "$MODEL" \
    --tasks "$T" --n_samples_per_task 200 --mode full --evaluator llm \
    --generation_params '{"max_tokens": 8192}' --output_dir "$OUT" 2>&1 | tee -a "$LOG"
  echo "=== $T rc=${PIPESTATUS[0]} $(date) ===" | tee -a "$LOG"
done
echo "EACH3_DONE $(date)" > "$OUT/EACH3_DONE.txt"
