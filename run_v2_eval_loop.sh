#!/usr/bin/env bash
# Incremental judging for the V2 run: repeatedly find tasks that have a response
# file but no result file yet, and evaluate exactly those (mode=evaluation, reads
# cached responses, judges via the OpenRouter EVAL_API_KEY). Runs alongside
# generation and exits once generation is done and nothing is left to judge.
#
#   K2_API_KEY=xxxx ./run_v2_eval_loop.sh
# (K2_API_KEY is only needed because run_eval constructs the gen client object;
#  no generation calls are made in evaluation mode.)
set -uo pipefail
REPO="/Users/sama/Documents/LIBRAI/libra-eval"
cd "$REPO" || exit 1
: "${K2_API_KEY:?Set K2_API_KEY (gen client is constructed even in eval mode)}"

PY="$REPO/.venv/bin/python3"
MODEL="MBZUAI-IFM/K2-Think-v2"
OUTDIR="$REPO/outputs_v2_200"
LOG="$REPO/outputs_v2_eval.log"
SUFFIX="_200_K2-Think-v2"

pending() {  # list base task names with a response file but no result file
  "$PY" - "$OUTDIR" "$SUFFIX" <<'PYEOF'
import os, sys, glob
outdir, suffix = sys.argv[1], sys.argv[2]
resp = {os.path.basename(p)[:-6].replace(suffix, "")
        for p in glob.glob(os.path.join(outdir, "responses", f"*{suffix}.jsonl"))}
res = {os.path.basename(p)[:-5].replace(suffix, "")
       for p in glob.glob(os.path.join(outdir, "results", f"*{suffix}.json"))}
print(",".join(sorted(resp - res)))
PYEOF
}

echo "=== V2 EVAL LOOP START $(date) ===" | tee -a "$LOG"
while true; do
  TASKS="$(pending)"
  if [ -n "$TASKS" ]; then
    echo "[$(date +%H:%M:%S)] judging: $TASKS" | tee -a "$LOG"
    "$PY" -m libra_eval.run_eval \
      --client k2think --models "$MODEL" \
      --tasks "$TASKS" \
      --n_samples_per_task 200 \
      --mode evaluation --evaluator llm \
      --output_dir "$OUTDIR" 2>&1 | tee -a "$LOG"
  else
    echo "[$(date +%H:%M:%S)] nothing pending" | tee -a "$LOG"
  fi
  # stop when generation is finished AND nothing remains to judge
  if [ -f "$OUTDIR/GEN_DONE.txt" ] && [ -z "$(pending)" ]; then
    echo "=== V2 EVAL LOOP DONE $(date) ===" | tee -a "$LOG"
    echo "DONE $(date)" > "$OUTDIR/EVAL_DONE.txt"
    break
  fi
  sleep 120
done
