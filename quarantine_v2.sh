#!/usr/bin/env bash
# Delete any V2 task whose response file contains empty responses (a sign the
# rate-limit storm injected 429-exhaustion blanks). Removes response+eval+result
# so the task regenerates cleanly on the next run. Safe to run anytime.
set -uo pipefail
cd "$(dirname "$0")" || exit 1
OUT=outputs_v2_200; SUF=_200_K2-Think-v2
q=0
for f in $OUT/responses/*${SUF}.jsonl; do
  [ -e "$f" ] || continue
  t=$(basename "$f" | sed "s/${SUF}.jsonl//")
  e=$(.venv/bin/python -c "import json,sys; print(sum(1 for l in open('$f') if not json.loads(l).get('response','').strip()))")
  if [ "$e" -gt 0 ]; then
    rm -f "$OUT/responses/${t}${SUF}.jsonl" "$OUT/evaluations/${t}${SUF}.jsonl" "$OUT/results/${t}${SUF}.json"
    echo "quarantined $t ($e empty)"; q=$((q+1))
  fi
done
echo "quarantined $q | clean V2 results: $(ls $OUT/results/ 2>/dev/null | grep -c json)/94"
