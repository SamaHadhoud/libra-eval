#!/usr/bin/env bash
# UAE-specific evaluation for V3 (local checkpoint), final-answer-only to match
# the existing outputs_full_200 suite. Generates + judges in one pass.
set -uo pipefail
REPO="/Users/sama/Documents/LIBRAI/libra-eval"
cd "$REPO" || exit 1

PY="$REPO/.venv/bin/python3"
MODEL="k2moe375B-mid3_v3-checkpoint_0003500"
OUTDIR="$REPO/outputs_full_200"
LOG="$REPO/outputs_uae_v3.log"
export LOCAL_CAPTURE_REASONING=0   # final-answer-only (match V3 suite)

echo "=== UAE V3 START $(date) ===" | tee -a "$LOG"
"$PY" -m libra_eval.run_eval \
    --client local --models "$MODEL" \
    --tasks uae_safety,uae_truthfulness_wiki,uae_truthfulness_dhow,uae_controversial \
    --n_samples_per_task 200 \
    --mode full --evaluator llm \
    --generation_params '{"max_tokens": 8192}' \
    --output_dir "$OUTDIR" 2>&1 | tee -a "$LOG"

RC=${PIPESTATUS[0]}
echo "DONE rc=$RC $(date)" > "$OUTDIR/UAE_V3_DONE.txt"
echo "=== UAE V3 FINISHED rc=$RC $(date) ===" | tee -a "$LOG"
