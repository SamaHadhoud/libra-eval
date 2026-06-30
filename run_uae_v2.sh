#!/usr/bin/env bash
# UAE evaluation for V2 (k2think API). Waits for the main V2 generation to finish
# first (shared rate-limited key), then runs the 4 UAE tasks gen+judge in one
# pass into outputs_v2_200/. Requires K2_API_KEY in the environment.
set -uo pipefail
REPO="/Users/sama/Documents/LIBRAI/libra-eval"
cd "$REPO" || exit 1
: "${K2_API_KEY:?Set K2_API_KEY}"

PY="$REPO/.venv/bin/python3"
MODEL="MBZUAI-IFM/K2-Think-v2"
OUTDIR="$REPO/outputs_v2_200"
LOG="$REPO/outputs_uae_v2.log"

echo "=== UAE V2 waiting for main V2 generation to finish... $(date) ===" | tee -a "$LOG"
while [ ! -f "$OUTDIR/GEN_DONE.txt" ]; do sleep 120; done
echo "=== main gen done; starting UAE V2 $(date) ===" | tee -a "$LOG"

"$PY" -m libra_eval.run_eval \
    --client k2think --models "$MODEL" \
    --tasks uae_safety,uae_truthfulness_wiki,uae_truthfulness_dhow,uae_controversial \
    --n_samples_per_task 200 \
    --mode full --evaluator llm \
    --generation_params '{"max_tokens": 8192}' \
    --output_dir "$OUTDIR" 2>&1 | tee -a "$LOG"

RC=${PIPESTATUS[0]}
echo "DONE rc=$RC $(date)" > "$OUTDIR/UAE_V2_DONE.txt"
echo "=== UAE V2 FINISHED rc=$RC $(date) ===" | tee -a "$LOG"
