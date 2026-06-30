#!/usr/bin/env bash
# Re-judge the 25 tasks corrupted by the earlier OpenRouter 403, with the improved
# harmful-judge prompt. mode=evaluation + rewrite_cache => judge-only on cached responses.
# Safeguard: any task that comes back with empty verdicts (limit hit again) is restored
# from the pre-rejudge snapshot and reported as still-pending, never left at spurious 0.5.
set -uo pipefail
REPO="/Users/sama/Documents/LIBRAI/libra-eval"; cd "$REPO" || exit 1
PY="$REPO/.venv/bin/python3"
MODEL="k2moe375B-mid3_v3-checkpoint_0003500"
OUTDIR="$REPO/outputs_full_200"
LOG="$REPO/rejudge_pending25.log"
TASKS="$($PY -c "import json;print(','.join(json.load(open('/tmp/corrupted_tasks.json'))))")"

echo "=== REJUDGE-25 START $(date) ===" | tee "$LOG"
echo "tasks: $TASKS" | tee -a "$LOG"
"$PY" -m libra_eval.run_eval \
    --client local --models "$MODEL" \
    --tasks "$TASKS" --n_samples_per_task 200 \
    --mode evaluation --evaluator llm --rewrite_cache \
    --output_dir "$OUTDIR" 2>&1 | tee -a "$LOG"
echo "=== REJUDGE-25 EVAL DONE $(date) ===" | tee -a "$LOG"

# Post-validate + safeguard restore + diff
"$PY" - <<'PYEOF' 2>&1 | tee -a "$LOG"
import json, glob, os
pre=json.load(open('/tmp/prejudge_scores.json'))
pending=json.load(open('/tmp/corrupted_tasks.json'))
done, still_pending = [], []
for t in pending:
    evf=f'outputs_full_200/evaluations/{t}_200_{ "k2moe375B-mid3_v3-checkpoint_0003500" }.jsonl'
    rf=f'outputs_full_200/results/{t}_200_k2moe375B-mid3_v3-checkpoint_0003500.json'
    ev=[json.loads(l) for l in open(evf)] if os.path.exists(evf) else []
    n_empty=sum(1 for r in ev if not isinstance(r.get('eval_response'),dict))
    d=json.load(open(rf))
    if ev and n_empty==0:
        d.pop('_rejudge_pending', None); json.dump(d,open(rf,'w'),indent=2)
        done.append((t, pre.get(t+'_200'), d['score']))
    else:
        # limit hit again -> restore snapshot score, keep pending
        if t+'_200' in pre:
            d['score']=pre[t+'_200']; d['_rejudge_pending']=f"still pending (empty {n_empty}/{len(ev)})"
            json.dump(d,open(rf,'w'),indent=2)
        still_pending.append(t)
json.dump(still_pending, open('outputs_full_200/REJUDGE_PENDING.json','w'),indent=1)
print(f"\n=== RE-JUDGED OK: {len(done)}/{len(pending)} ===")
for t,o,n in sorted(done, key=lambda r:(r[2]-(r[1] or 0))):
    o=o if o is not None else float('nan'); print(f"  {t:36} {o:.3f} -> {n:.3f}  ({n-o:+.3f})")
print(f"\n=== STILL PENDING: {len(still_pending)} ===")
for t in still_pending: print(f"  {t}")
PYEOF
echo "REJUDGE25_DONE $(date)" > "$OUTDIR/REJUDGE25_DONE.txt"
