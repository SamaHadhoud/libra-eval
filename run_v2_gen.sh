#!/usr/bin/env bash
# K2-Think-v2 GENERATION-ONLY run (mode=inference) over the 91 registered tasks
# (88 English main + 3 multilingual; jailbench/ruozhibench/wmdp are not registered).
# Judging is deferred — run run_v2_eval.sh once the judge key is topped up.
#
# Requires K2_API_KEY in the environment (NOT stored in this file):
#   K2_API_KEY=xxxx ./run_v2_gen.sh
set -uo pipefail

REPO="/Users/sama/Documents/LIBRAI/libra-eval"
cd "$REPO" || exit 1

: "${K2_API_KEY:?Set K2_API_KEY in the environment before running}"

PY="$REPO/.venv/bin/python3"
MODEL="MBZUAI-IFM/K2-Think-v2"
OUTDIR="$REPO/outputs_v2_200"
LOG="$REPO/outputs_v2_gen.log"

mkdir -p "$OUTDIR"
echo "=== V2 GEN START $(date) ===" | tee -a "$LOG"
echo "model=$MODEL  mode=inference  n_samples=200  tasks=all(91)  outdir=$OUTDIR" | tee -a "$LOG"

"$PY" -m libra_eval.run_eval \
    --client k2think \
    --models "$MODEL" \
    --tasks all \
    --exclude_tasks librai_adv_deep_inception \
    --n_samples_per_task 200 \
    --mode inference \
    --generation_params '{"max_tokens": 8192}' \
    --output_dir "$OUTDIR" \
    2>&1 | tee -a "$LOG"

RC=${PIPESTATUS[0]}
# Only mark done on a clean exit — a kill (rc!=0) must NOT write GEN_DONE,
# otherwise the eval loop would think generation finished prematurely.
if [ "$RC" = "0" ]; then
  echo "DONE rc=$RC $(date)" > "$OUTDIR/GEN_DONE.txt"
fi
echo "=== V2 GEN FINISHED rc=$RC $(date) ===" | tee -a "$LOG"
