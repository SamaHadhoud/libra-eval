#!/usr/bin/env bash
# Full LIBRA-EVAL validation, n_samples_per_task=200, all 74 tasks.
# Designed to run unattended inside tmux. Logs everything; emits a report at the end.
set -uo pipefail

REPO="/Users/sama/Documents/LIBRAI/libra-eval"
cd "$REPO" || exit 1

PY="$REPO/.venv/bin/python3"
MODEL="k2moe375B-mid3_v3-checkpoint_0003500"
OUTDIR="$REPO/outputs_full_200"
LOG="$REPO/outputs_full_200_run.log"

mkdir -p "$OUTDIR"
echo "=== START $(date) ===" | tee -a "$LOG"
echo "model=$MODEL  n_samples=200  tasks=all  outdir=$OUTDIR" | tee -a "$LOG"

"$PY" -m libra_eval.run_eval \
    --client local \
    --models "$MODEL" \
    --tasks all \
    --n_samples_per_task 200 \
    --mode full \
    --evaluator llm \
    --generation_params '{"max_tokens": 8192}' \
    --output_dir "$OUTDIR" \
    2>&1 | tee -a "$LOG"

EVAL_RC=${PIPESTATUS[0]}
echo "=== EVAL FINISHED rc=$EVAL_RC $(date) ===" | tee -a "$LOG"

echo "=== generating report ===" | tee -a "$LOG"
"$PY" "$REPO/gen_report_200.py" "$OUTDIR" "$MODEL" 2>&1 | tee -a "$LOG"

echo "DONE rc=$EVAL_RC $(date)" > "$OUTDIR/RUN_DONE.txt"
echo "=== ALL DONE rc=$EVAL_RC $(date) ===" | tee -a "$LOG"
