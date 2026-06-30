#!/usr/bin/env python3
"""Pre-pass for stage-1 retry loop: delete response files that are missing or
mostly-empty so run_eval's resume actually regenerates them (resume only checks
file existence, not content). Prints REMAINING=<n> = number of expected tasks
that still need generation.
"""
import os, re, sys, glob
import pandas as pd

OUTDIR = sys.argv[1]
TASKS = sys.argv[2].split(",")
resp_dir = os.path.join(OUTDIR, "responses")
EMPTY_FRAC = 0.5

remaining = 0
for t in TASKS:
    pat = re.compile(rf"^{re.escape(t)}_\d+_.*\.jsonl$")
    fs = [f for f in os.listdir(resp_dir) if pat.match(f)] if os.path.isdir(resp_dir) else []
    if not fs:
        remaining += 1
        continue
    fp = os.path.join(resp_dir, fs[0])
    try:
        df = pd.read_json(fp, lines=True)
        s = df["response"].fillna("").astype(str)
        empty_frac = (s.str.strip() == "").sum() / len(df) if len(df) else 1.0
    except Exception:
        empty_frac = 1.0
    if empty_frac > EMPTY_FRAC:
        os.remove(fp)
        print(f"  deleted bad file: {fs[0]} (empty_frac={empty_frac:.2f})", file=sys.stderr)
        remaining += 1

print(f"REMAINING={remaining}")
