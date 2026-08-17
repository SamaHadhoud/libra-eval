"""Re-judge existing evaluation trajectories with a different judge model.

Reads the already-judged eval JSONLs in <eval_dir> (which contain the exact
response each judge saw, plus GPT-4o's `eval_response`), rebuilds the identical
judge prompt via each task's `_single_eval_message` + `judge_prompts.build_prompt`,
and re-runs it on a new judge model. Output: one JSONL per task in
<out_dir>/evaluations_<model-slug>/ with the new judge's parsed JSON per item,
so per-item agreement with the original judge can be computed.

Chinese-only tasks (jailbench, ruozhibench) are excluded — they are not in the
TASKS registry and anything unregistered is skipped.

Resumable: already-judged (task, idx) pairs are skipped on restart.

Usage:
  python judge_correlation/rejudge_with_model.py --model openai/gpt-5.6-terra \
      --tasks all --concurrency 100
  python judge_correlation/rejudge_with_model.py --tasks advbench_200,confaide_200 \
      --limit-items 5   # pilot
"""

import argparse
import glob
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from openai import OpenAI

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from libra_eval.tasks import TASKS  # noqa: E402
from libra_eval.llmclient.judge_prompts import build_prompt  # noqa: E402
from libra_eval.llmclient.llm_judge import LLMJudge_Client  # noqa: E402


def load_api_config():
    with open(os.path.join(REPO, "libra_eval/config/api_config.json")) as f:
        return json.load(f)


def task_class_for(result_task_name):
    base = re.sub(r"_\d+$", "", result_task_name)
    return TASKS.get(base)


def collect_work(eval_dir, results_dir, only_tasks=None, limit_items=None):
    """Yield (task_name, evaluator_name, idx, judge_input_dict) for every item."""
    work = []
    for rp in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
        meta = json.load(open(rp))
        if meta.get("evaluator_backend") != "local_llm":
            continue
        tname = meta["task"]
        if only_tasks and tname not in only_tasks:
            continue
        cls = task_class_for(tname)
        if cls is None:
            print(f"[skip] no task class for {tname} (excluded from registry)")
            continue
        eps = glob.glob(os.path.join(eval_dir, f"{tname}_*.jsonl"))
        if not eps:
            print(f"[skip] no eval file for {tname}")
            continue
        df = pd.read_json(eps[0], lines=True)
        if limit_items:
            df = df.head(limit_items)
        task = cls.__new__(cls)  # skip __init__: no dataset read needed
        evaluator = cls.librai_evaluator_name
        for idx, row in df.iterrows():
            work.append((tname, evaluator, int(idx), task._single_eval_message(row)))
    return work


class Rejudger:
    def __init__(self, model, api_config, max_output_tokens=3000):
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.client = OpenAI(
            api_key=api_config.get("EVAL_API_KEY") or api_config.get("NEXT_API_KEY"),
            base_url=api_config.get("EVAL_BASE_URL", "https://openrouter.ai/api/v1"),
        )
        self.usage_lock = threading.Lock()
        self.usage = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0, "cost": 0.0}
        # Some newer models reject temperature / reasoning params; degrade gracefully.
        self.send_temperature = True
        self.send_reasoning = True

    def _chat(self, system_prompt, user_prompt, strict_suffix=""):
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt + strict_suffix},
            ],
            max_tokens=self.max_output_tokens,
            timeout=180,
            extra_body={"usage": {"include": True}},
        )
        if self.send_temperature:
            kwargs["temperature"] = 0
        if self.send_reasoning:
            kwargs["extra_body"]["reasoning"] = {"effort": "minimal"}
        try:
            return self.client.chat.completions.create(**kwargs)
        except Exception as e:
            msg = str(e).lower()
            if "temperature" in msg and self.send_temperature:
                self.send_temperature = False
                return self._chat(system_prompt, user_prompt, strict_suffix)
            if ("reasoning" in msg or "effort" in msg) and self.send_reasoning:
                self.send_reasoning = False
                return self._chat(system_prompt, user_prompt, strict_suffix)
            raise

    def judge(self, evaluator_name, judge_input, num_retries=4):
        system_prompt, user_prompt = build_prompt(evaluator_name, judge_input)
        last_err = None
        for attempt in range(num_retries):
            strict = (
                "" if attempt == 0
                else "\n\nReply with ONLY the JSON object, no prose, no code fences."
            )
            try:
                completion = self._chat(system_prompt, user_prompt, strict)
                u = getattr(completion, "usage", None)
                if u:
                    with self.usage_lock:
                        self.usage["prompt_tokens"] += u.prompt_tokens or 0
                        self.usage["completion_tokens"] += u.completion_tokens or 0
                        self.usage["calls"] += 1
                        cost = getattr(u, "cost", None)
                        if cost:
                            self.usage["cost"] += cost
                content = completion.choices[0].message.content
                return LLMJudge_Client._parse_json(content)
            except Exception as e:
                last_err = e
                wait = min(2 ** attempt * 2, 30)
                if "429" in str(e) or "rate" in str(e).lower():
                    wait = max(wait, 15)
                time.sleep(wait)
        return {"_error": str(last_err)[:500]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="openai/gpt-5.6-terra")
    ap.add_argument("--eval-dir", default=os.path.join(REPO, "outputs_full_200/evaluations"))
    ap.add_argument("--results-dir", default=os.path.join(REPO, "outputs_full_200/results"))
    ap.add_argument("--out-dir", default=os.path.join(REPO, "judge_correlation"))
    ap.add_argument("--tasks", default="all", help="comma-separated result task names (e.g. advbench_200) or 'all'")
    ap.add_argument("--limit-items", type=int, default=None)
    ap.add_argument("--concurrency", type=int, default=100)
    args = ap.parse_args()

    only = None if args.tasks == "all" else set(args.tasks.split(","))
    slug = args.model.replace("/", "_")
    out_dir = os.path.join(args.out_dir, f"evaluations_{slug}")
    os.makedirs(out_dir, exist_ok=True)

    work = collect_work(args.eval_dir, args.results_dir, only, args.limit_items)
    print(f"{len(work)} judgments to consider across {len(set(w[0] for w in work))} tasks")

    # Resume: drop (task, idx) already written.
    done = set()
    for p in glob.glob(os.path.join(out_dir, "*.jsonl")):
        t = os.path.basename(p)[:-6]
        with open(p) as f:
            for line in f:
                try:
                    done.add((t, json.loads(line)["idx"]))
                except Exception:
                    pass
    work = [w for w in work if (w[0], w[2]) not in done]
    print(f"{len(done)} already done, {len(work)} remaining")
    if not work:
        return

    rejudger = Rejudger(args.model, load_api_config())
    files, file_locks = {}, {}
    meta_lock = threading.Lock()

    def run_one(item):
        tname, evaluator, idx, judge_input = item
        result = rejudger.judge(evaluator, judge_input)
        rec = {"idx": idx, "evaluator": evaluator, "eval_response": result}
        with meta_lock:
            if tname not in files:
                files[tname] = open(os.path.join(out_dir, tname + ".jsonl"), "a")
                file_locks[tname] = threading.Lock()
        with file_locks[tname]:
            files[tname].write(json.dumps(rec, ensure_ascii=False) + "\n")
            files[tname].flush()
        return tname

    t0 = time.time()
    n_done = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(run_one, w) for w in work]
        for fut in as_completed(futures):
            fut.result()
            n_done += 1
            if n_done % 200 == 0 or n_done == len(work):
                el = time.time() - t0
                u = rejudger.usage
                print(
                    f"{n_done}/{len(work)} done | {el/60:.1f} min | "
                    f"in={u['prompt_tokens']:,} out={u['completion_tokens']:,} "
                    f"cost=${u['cost']:.2f}",
                    flush=True,
                )

    for f in files.values():
        f.close()
    with open(os.path.join(out_dir, "_usage.json"), "w") as f:
        json.dump(rejudger.usage, f, indent=2)
    print("usage:", rejudger.usage)


if __name__ == "__main__":
    main()
