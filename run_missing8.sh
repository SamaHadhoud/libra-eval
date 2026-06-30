#!/usr/bin/env bash
# Full run (inference + eval) for the 8 tasks with no results yet:
# 5 newly-added RedBenchSubsets tasks + cosafe/diasafety + the now-fixed prompthijackingrobustness.
set -uo pipefail
REPO="/Users/sama/Documents/LIBRAI/libra-eval"; cd "$REPO" || exit 1
PY="$REPO/.venv/bin/python3"
MODEL="k2moe375B-mid3_v3-checkpoint_0003500"
OUTDIR="$REPO/outputs_full_200"
LOG="$REPO/run_missing8.log"
TASKS="catqa,cosafe,diasafety,forbidden_questions,gptfuzzer,med_safety_bench,prompthijackingrobustness,sg_xstest"

echo "=== MISSING-8 START $(date) ===" | tee "$LOG"
"$PY" -m libra_eval.run_eval \
    --client local --models "$MODEL" \
    --tasks "$TASKS" --n_samples_per_task 200 \
    --mode full --evaluator llm \
    --generation_params '{"max_tokens": 8192}' \
    --output_dir "$OUTDIR" 2>&1 | tee -a "$LOG"
RC=${PIPESTATUS[0]}
echo "=== MISSING-8 FINISHED rc=$RC $(date) ===" | tee -a "$LOG"
# analyze + append notes for the new tasks
"$PY" "$REPO/analyze_task.py" new 2>&1 | tee -a "$LOG"
echo "MISSING8_DONE rc=$RC $(date)" > "$OUTDIR/MISSING8_DONE.txt"
