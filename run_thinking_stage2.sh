#!/usr/bin/env bash
# Stage 2+3: thinking-vs-answer harmful check (judges reasoning vs final answer
# separately) + divergence analysis. Hits OpenRouter, so wrapped in a resilient
# retry loop: --resume skips done files, --retry-failed re-does only error rows.
set -uo pipefail

REPO="/Users/sama/Documents/LIBRAI/libra-eval"
cd "$REPO" || exit 1

PY="$REPO/.venv/bin/python3"
OUTDIR="$REPO/outputs_thinking_full"
LOG="$REPO/outputs_thinking_hc.log"
JUDGE="openai/gpt-4o"
BASE_URL="https://openrouter.ai/api/v1"
EVAL_KEY=$("$PY" -c "import json;print(json.load(open('$REPO/libra_eval/config/api_config.json'))['EVAL_API_KEY'])")

echo "=== STAGE2 START $(date) ===" | tee -a "$LOG"

# Pass 1: normal resume run. Subsequent passes: retry only failed/null rows.
MAX_ATTEMPTS=20
for attempt in $(seq 1 $MAX_ATTEMPTS); do
    echo "--- harmful-check attempt $attempt/$MAX_ATTEMPTS $(date) ---" | tee -a "$LOG"
    # Always retry-failed: existing files have error rows from the prior
    # credit-exhausted run that --resume alone would skip (they have a
    # harmful_check field, just with an error). retry-failed re-judges only
    # the failed/null rows and preserves the good ones.
    EXTRA="--resume --retry-failed"
    "$PY" "$REPO/batch_harmful_check.py" \
        --api_key "$EVAL_KEY" --model "$JUDGE" --base_url "$BASE_URL" \
        --input_dir "$OUTDIR/responses" \
        --output_dir "$OUTDIR/harmful_checks" \
        --max_concurrent 5 $EXTRA >> "$LOG" 2>&1

    # Count remaining failed/null rows across all output files.
    FAILED=$("$PY" - "$OUTDIR/harmful_checks" <<'PY'
import sys, json, glob, os
d=sys.argv[1]; fail=0
for f in glob.glob(os.path.join(d,"*.jsonl")):
    for line in open(f):
        try:
            hc=json.loads(line).get("harmful_check",{})
            if hc.get("overall_is_harmful") is None or "error" in hc: fail+=1
        except Exception: fail+=1
print(fail)
PY
)
    echo "--- attempt $attempt: remaining failed rows = $FAILED ---" | tee -a "$LOG"
    if [ "${FAILED:-1}" -eq 0 ]; then
        echo "--- all rows judged ---" | tee -a "$LOG"
        break
    fi
    sleep 60
done

echo "=== STAGE3 analysis $(date) ===" | tee -a "$LOG"
"$PY" "$REPO/analyze_harmful_checks.py" \
    --harmful_check_dir "$OUTDIR/harmful_checks" \
    --output_dir "$REPO/harmful_check_analysis_thinking" >> "$LOG" 2>&1

echo "DONE failed=$FAILED $(date)" > "$OUTDIR/STAGE2_DONE.txt"
echo "=== STAGE2+3 DONE failed=$FAILED $(date) ===" | tee -a "$LOG"
