#!/usr/bin/env python3
"""
run_family.py — one-command driver for the K2-V3 size-family evaluation.

Give it a list of model endpoints; for each model it will, in order:
  1. smoke-test the endpoint  (2 tasks x 5 samples, checks non-empty answers)
  2. run the full 95-task suite (generation + interleaved gpt-5.6-terra judging)
  3. add/refresh the model's entry in family_report/models.json
and finally regenerate the whole family report (charts + LaTeX fragments).

Everything is resumable: run_eval skips tasks whose result file already exists,
and each stage records a marker so a re-invocation continues where it stopped.
Per-model work is independent, so `--parallel` runs all endpoints at once
(one process per endpoint) — only do this if the endpoints don't share GPUs.

--------------------------------------------------------------------------------
USAGE
    # from a models spec file (recommended — see family_run.example.yaml):
    .venv/bin/python run_family.py --spec family_run.yaml

    # or inline, one --model per endpoint  (key:label:size_b:base_url[:api_key])
    .venv/bin/python run_family.py \
        --model "v3_375b:K2-V3 375B:375:http://<endpoint-a>:8000/v1::sk-xxx" \
        --model "v3_32b:K2-V3 32B:32:http://<endpoint-b>:8000/v1::sk-yyy"

    # run all endpoints concurrently (independent GPU capacity only):
    .venv/bin/python run_family.py --spec family_run.yaml --parallel

    # stop after smoke tests (endpoint intake), or skip them once trusted:
    .venv/bin/python run_family.py --spec family_run.yaml --smoke-only
    .venv/bin/python run_family.py --spec family_run.yaml --skip-smoke

    # report only (no eval) — after runs already finished:
    .venv/bin/python run_family.py --spec family_run.yaml --report-only

Each model needs: key (letters/digits/underscore), label, size_b (or "" if
unknown), base_url (OpenAI-compatible /v1). api_key is optional (falls back to
the LOCAL_API_KEY in api_config.json). A model may add:
  reasoning=inline   -> endpoint returns reasoning as ...</think>answer  (k2think client)
  reasoning=field    -> reasoning in reasoning_content, answer in content (default, local client)
  thinking_csv=PATH  -> Stage B divergence CSV to wire into the report
The judge is whatever api_config.json says (now openai/gpt-5.6-terra); override
with EVAL_API_KEY in the environment or --judge-key.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(REPO, ".venv", "bin", "python3")
if not os.path.exists(PY):
    PY = sys.executable
SUITE_N = 200
SMOKE_TASKS = "advbench,confaide"
SMOKE_N = 5
# tasks deregistered for the family scope live outside TASKS already; nothing
# to exclude here — `--tasks all` == the 95-task V3 report scope.


# --------------------------------------------------------------------------- #
# Model spec parsing
# --------------------------------------------------------------------------- #
class Model:
    def __init__(self, key, label, size_b, base_url, api_key="",
                 reasoning="field", thinking_csv="", is_baseline=False,
                 results_dir=""):
        self.key = key
        self.label = label
        self.size_b = size_b
        self.base_url = base_url
        self.api_key = api_key
        self.reasoning = reasoning          # "field" (local) | "inline" (k2think)
        self.thinking_csv = thinking_csv
        self.is_baseline = is_baseline
        # New models get outputs_<key>_200; already-run models (the V3 anchor in
        # outputs_full_200, baselines) point their spec's results_dir at the
        # existing dir and are reported without re-running.
        if results_dir:
            rd = results_dir if os.path.isabs(results_dir) else os.path.join(REPO, results_dir)
            self.outdir = os.path.dirname(rd.rstrip("/")) if rd.rstrip("/").endswith("results") else rd
            self._results_dir = rd
        else:
            self.outdir = os.path.join(REPO, f"outputs_{key}_{SUITE_N}")
            self._results_dir = os.path.join(self.outdir, "results")
        self.prerun = bool(results_dir)     # skip eval for pre-existing runs

    @property
    def client(self):
        return "k2think" if self.reasoning == "inline" else "local"

    @property
    def results_dir(self):
        return self._results_dir

    @property
    def results_dir_rel(self):
        return os.path.relpath(self._results_dir, REPO)


def _num_or_none(s):
    s = str(s).strip()
    if s in ("", "null", "none", "None"):
        return None
    return float(s) if "." in s else int(s)


def parse_inline(s: str) -> Model:
    # key:label:size_b:base_url[:api_key]   (label may not contain ':')
    parts = s.split(":")
    if len(parts) < 4:
        sys.exit(f"--model needs at least key:label:size_b:base_url  (got {s!r})")
    key, label, size_b, base_url = parts[0], parts[1], parts[2], ":".join(parts[3:5]) if parts[3] in ("http", "https") else parts[3]
    # rebuild base_url + optional api_key robustly (URLs contain ':')
    rest = s.split(":", 3)[3]  # everything after key:label:size_b:
    # api_key, if present, is the last ' ' -free token after a space is not used;
    # instead we split base_url from api_key on the LAST '::' if provided
    if "::" in rest:
        base_url, api_key = rest.rsplit("::", 1)
    else:
        base_url, api_key = rest, ""
    return Model(key=key, label=label, size_b=_num_or_none(size_b),
                 base_url=base_url, api_key=api_key)


def load_spec(path: str) -> list[Model]:
    """Accept a tiny YAML/JSON spec without a yaml dependency."""
    txt = open(path).read()
    try:
        data = json.loads(txt)
    except json.JSONDecodeError:
        data = _mini_yaml(txt)
    models = []
    for role, is_base in (("family", False), ("baselines", True)):
        for e in data.get(role, []):
            models.append(Model(
                key=e["key"], label=e["label"],
                size_b=_num_or_none(e.get("size_b", "")),
                base_url=e.get("base_url", ""), api_key=e.get("api_key", ""),
                reasoning=e.get("reasoning", "field"),
                thinking_csv=e.get("thinking_csv", ""), is_baseline=is_base,
                results_dir=e.get("results_dir", "")))
    if not models:
        sys.exit(f"no models found in {path}")
    return models


def _mini_yaml(txt: str) -> dict:
    """Minimal parser for the flat family_run.yaml shape (family:/baselines:
    lists of `- key: ...` blocks). Avoids a PyYAML dependency."""
    out, cur_list, cur_item = {}, None, None
    for raw in txt.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            cur_list = line[:-1].strip()
            out[cur_list] = []
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            cur_item = {}
            out[cur_list].append(cur_item)
            stripped = stripped[2:]
        if ":" in stripped and cur_item is not None:
            k, v = stripped.split(":", 1)
            cur_item[k.strip()] = v.strip().strip('"').strip("'")
    return out


# --------------------------------------------------------------------------- #
# Shell helpers
# --------------------------------------------------------------------------- #
def env_for(m: Model) -> dict:
    e = dict(os.environ)
    e["LOCAL_BASE_URL"] = m.base_url
    if m.api_key:
        e["LOCAL_API_KEY"] = m.api_key
        e["K2_API_KEY"] = m.api_key
    if m.reasoning == "inline":
        e["K2_BASE_URL"] = m.base_url
    # main-run responses store the trace but score only the final answer
    e["LOCAL_CAPTURE_REASONING"] = "1"
    return e


def run(cmd: list[str], env=None, log=None) -> int:
    print(f"    $ {' '.join(cmd)}")
    with open(log, "a") if log else _nullcm() as lf:
        p = subprocess.run(cmd, env=env, cwd=REPO,
                           stdout=(lf or None), stderr=subprocess.STDOUT)
    return p.returncode


class _nullcm:
    def __enter__(self): return None
    def __exit__(self, *a): return False


# --------------------------------------------------------------------------- #
# Stages
# --------------------------------------------------------------------------- #
def smoke_test(m: Model) -> bool:
    print(f"[{m.key}] smoke test ({SMOKE_TASKS}, n={SMOKE_N}) -> {m.base_url}")
    sdir = os.path.join(m.outdir, "_smoke")
    os.makedirs(sdir, exist_ok=True)
    rc = run([PY, "-m", "libra_eval.run_eval",
              "--client", m.client, "--models", m.label,
              "--tasks", SMOKE_TASKS, "--n_samples_per_task", str(SMOKE_N),
              "--mode", "inference",
              "--generation_params", '{"max_tokens": 8192}',
              "--output_dir", sdir],
             env=env_for(m), log=os.path.join(m.outdir, "smoke.log"))
    if rc != 0:
        print(f"[{m.key}] SMOKE FAILED (rc={rc}) — see {m.outdir}/smoke.log")
        return False
    # verify responses have non-empty final answers
    import glob
    ok = empty = 0
    for f in glob.glob(os.path.join(sdir, "responses", "*.jsonl")):
        for line in open(f):
            try:
                r = json.loads(line).get("response", "")
            except Exception:
                continue
            after = r.rsplit("</think>", 1)[-1] if "</think>" in r else r
            after = after.split("</think_fast>", 1)[-1]
            (ok := ok + 1) if after.strip() else (empty := empty + 1)
    total = ok + empty
    print(f"[{m.key}] smoke: {ok}/{total} non-empty answers")
    if total == 0 or empty / total > 0.2:
        print(f"[{m.key}] SMOKE FAILED — too many empty answers "
              f"(check reasoning= mode: field vs inline)")
        return False
    print(f"[{m.key}] smoke OK")
    return True


def full_run(m: Model) -> bool:
    print(f"[{m.key}] full suite (95 tasks x n={SUITE_N}, judge from api_config)")
    os.makedirs(m.outdir, exist_ok=True)
    rc = run([PY, "-m", "libra_eval.run_eval",
              "--client", m.client, "--models", m.label,
              "--tasks", "all", "--n_samples_per_task", str(SUITE_N),
              "--mode", "full", "--evaluator", "llm",
              "--generation_params", '{"max_tokens": 8192}',
              "--output_dir", m.outdir],
             env=env_for(m), log=os.path.join(m.outdir, "run.log"))
    marker = os.path.join(m.outdir, "RUN_DONE.txt")
    if rc == 0:
        open(marker, "w").write(f"done {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"[{m.key}] full run done")
        return True
    print(f"[{m.key}] RUN FAILED (rc={rc}) — see {m.outdir}/run.log "
          f"(re-run to resume: finished tasks are cached)")
    return False


def do_model(m: Model, skip_smoke: bool, smoke_only: bool) -> bool:
    if not skip_smoke:
        if not smoke_test(m):
            return False
    if smoke_only:
        return True
    return full_run(m)


# --------------------------------------------------------------------------- #
# Manifest + report
# --------------------------------------------------------------------------- #
def write_manifest(models: list[Model]):
    path = os.path.join(REPO, "family_report", "models.json")
    existing = json.load(open(path)) if os.path.exists(path) else {}
    comment = existing.get("_comment", "K2-V3 family manifest.")
    fam, base = [], []
    for m in models:
        entry = {"key": m.key, "label": m.label,
                 "size_b": m.size_b,
                 "results_dir": m.results_dir_rel}
        if m.thinking_csv:
            entry["thinking_csv"] = m.thinking_csv
        (base if m.is_baseline else fam).append(entry)
    # keep any pre-existing baselines (e.g. gpt4omini) not in this run
    have = {m.key for m in models}
    for e in existing.get("baselines", []):
        if e["key"] not in have:
            base.append(e)
    for e in existing.get("family", []):
        if e["key"] not in have and os.path.isdir(os.path.join(REPO, e["results_dir"])):
            fam.append(e)
    fam.sort(key=lambda e: (e.get("size_b") is None, e.get("size_b") or 0))
    json.dump({"_comment": comment, "family": fam, "baselines": base},
              open(path, "w"), indent=2)
    print(f"[manifest] {len(fam)} family + {len(base)} baseline entries -> {path}")


def generate_report():
    print("[report] regenerating charts + LaTeX fragments")
    for script in ("generate_family.py", "generate_latex.py"):
        rc = run([PY, os.path.join(REPO, "family_report", script)])
        if rc != 0:
            print(f"[report] {script} FAILED (rc={rc})")
            return False
    print("[report] done — family_report/figures/ + generated/ refreshed")
    return True


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", help="YAML/JSON models spec (family_run.yaml)")
    ap.add_argument("--model", action="append", default=[],
                    help="inline model key:label:size_b:base_url[::api_key]")
    ap.add_argument("--parallel", action="store_true",
                    help="run all endpoints concurrently (independent GPUs only)")
    ap.add_argument("--skip-smoke", action="store_true")
    ap.add_argument("--smoke-only", action="store_true")
    ap.add_argument("--report-only", action="store_true",
                    help="skip eval; just rebuild manifest + report from existing outputs")
    ap.add_argument("--judge-key", help="override EVAL_API_KEY for judging")
    args = ap.parse_args()

    if args.judge_key:
        os.environ["EVAL_API_KEY"] = args.judge_key

    models = load_spec(args.spec) if args.spec else [parse_inline(s) for s in args.model]
    if not models:
        ap.error("give --spec or at least one --model")
    print(f"family run: {[m.key for m in models]}  "
          f"(judge = {json.load(open(os.path.join(REPO,'libra_eval/config/api_config.json'))).get('EVAL_MODEL')})")

    ok = {m.key: True for m in models}
    if not args.report_only:
        # pre-run models (existing results_dir) and baselines are report-only
        eval_models = [m for m in models if not m.is_baseline and not m.prerun]
        for m in models:
            if m.prerun and not m.is_baseline:
                print(f"[{m.key}] pre-run (results_dir given) — skipping eval, "
                      f"reporting from {m.results_dir_rel}")
        if args.parallel:
            import concurrent.futures as cf
            with cf.ThreadPoolExecutor(max_workers=len(eval_models)) as ex:
                futs = {ex.submit(do_model, m, args.skip_smoke, args.smoke_only): m
                        for m in eval_models}
                for fut in cf.as_completed(futs):
                    ok[futs[fut].key] = fut.result()
        else:
            for m in eval_models:
                ok[m.key] = do_model(m, args.skip_smoke, args.smoke_only)
        if args.smoke_only:
            print("\nsmoke-only: " + ", ".join(f"{k}={'OK' if v else 'FAIL'}"
                                                 for k, v in ok.items()))
            return

    # only manifest+report the models whose results are present
    ready = [m for m in models if os.path.isdir(m.results_dir)]
    if not ready:
        print("no completed runs to report on yet.")
        return
    write_manifest(ready)
    generate_report()
    failed = [k for k, v in ok.items() if not v]
    if failed:
        print(f"\nWARNING: these models did not finish cleanly: {failed} "
              f"(re-run to resume; report covers only completed runs)")


if __name__ == "__main__":
    main()
