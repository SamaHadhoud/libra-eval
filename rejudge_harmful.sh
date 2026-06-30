#!/usr/bin/env bash
# Re-judge all 47 tasks that use build_harmful_judge, with the improved prompt.
# mode=evaluation + rewrite_cache => re-runs ONLY the judge on cached responses
# (no model-server inference). Emits a before/after diff report at the end.
set -uo pipefail
REPO="/Users/sama/Documents/LIBRAI/libra-eval"; cd "$REPO" || exit 1
PY="$REPO/.venv/bin/python3"
MODEL="k2moe375B-mid3_v3-checkpoint_0003500"
OUTDIR="$REPO/outputs_full_200"
LOG="$REPO/rejudge_harmful.log"
TASKS="$(cat /tmp/rejudge_list.txt)"

echo "=== REJUDGE START $(date) ===" | tee "$LOG"
"$PY" -m libra_eval.run_eval \
    --client local --models "$MODEL" \
    --tasks "$TASKS" --n_samples_per_task 200 \
    --mode evaluation --evaluator llm --rewrite_cache \
    --output_dir "$OUTDIR" 2>&1 | tee -a "$LOG"
RC=${PIPESTATUS[0]}
echo "=== REJUDGE FINISHED rc=$RC $(date) ===" | tee -a "$LOG"

# before/after diff report
"$PY" - <<'PYEOF' 2>&1 | tee -a "$LOG"
import json, glob, os
pre=json.load(open('/tmp/prejudge_scores.json'))
rows=[]
for f in glob.glob('outputs_full_200/results/*.json'):
    d=json.load(open(f)); t=d['task']
    if t in pre and pre[t]!=d['score']:
        rows.append((t, pre[t], d['score']))
rows.sort(key=lambda r: abs(r[2]-r[1]), reverse=True)
print(f"\n=== SCORE CHANGES ({len(rows)} tasks changed) ===")
for t,o,n in rows:
    print(f"  {t:36} {o:.3f} -> {n:.3f}  ({'+' if n>=o else ''}{n-o:.3f})")
print("(tasks not listed were unchanged)")
PYEOF
echo "REJUDGE_DONE rc=$RC $(date)" > "$OUTDIR/REJUDGE_DONE.txt"
