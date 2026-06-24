"""Offline verification that every registered task reads its dataset and
produces the chat-format inputs / eval messages its pipeline expects.

No API keys or network needed: we exercise read_task_data(), _single_input(),
and _single_eval_message() on a sample of rows, mimicking run_pipeline()
without calling any LLM or evaluator.
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libra_eval.tasks import TASKS
from libra_eval.tasks.base import ATTACK_TAGS, ROUND_TAGS, RISK_TYPE_TAGS

SAMPLE = 20  # rows to exercise per task

results = []
for name in sorted(TASKS):
    cls = TASKS[name]
    row = {"task": name, "class": cls.__name__, "rows": None,
           "input_ok": 0, "input_fail": 0, "eval_ok": 0, "eval_fail": 0,
           "tags_ok": True, "status": "OK", "detail": ""}
    try:
        # 1) instantiate -> reads & parses the full dataset file
        inst = cls(debug=False, output_dir=None)
        df = inst.data_df
        row["rows"] = len(df)

        # tag validity (same checks as Task.__post_init__)
        if (inst.attack_tag not in ATTACK_TAGS or inst.round_tag not in ROUND_TAGS
                or inst.risk_type_tag not in RISK_TYPE_TAGS):
            row["tags_ok"] = False

        # 2) exercise _single_input on a sample of rows
        sample = df.head(SAMPLE)
        first_input = None
        for _, r in sample.iterrows():
            try:
                msgs = inst._single_input(r)
                assert isinstance(msgs, list) and len(msgs) > 0
                assert all("role" in m and "content" in m for m in msgs)
                if first_input is None:
                    first_input = msgs
                row["input_ok"] += 1
            except Exception as e:
                row["input_fail"] += 1
                if not row["detail"]:
                    row["detail"] = f"input: {type(e).__name__}: {e}"

        # 3) exercise _single_eval_message with a dummy response
        for _, r in sample.iterrows():
            try:
                inst2 = r.copy()
                inst2["response"] = "This is a dummy assistant response."
                if first_input is not None:
                    inst2["input"] = first_input
                inst._single_eval_message(inst2)
                row["eval_ok"] += 1
            except Exception as e:
                row["eval_fail"] += 1
                if "input:" not in row["detail"] and not row["detail"]:
                    row["detail"] = f"eval: {type(e).__name__}: {e}"

        if row["input_fail"] or row["eval_fail"] or not row["tags_ok"]:
            row["status"] = "WARN"
    except Exception as e:
        row["status"] = "FAIL"
        row["detail"] = f"{type(e).__name__}: {e}".splitlines()[0][:200]
    results.append(row)

# ---- report ----
def line(r):
    flag = {"OK": "✓", "WARN": "!", "FAIL": "✗"}[r["status"]]
    tags = "" if r["tags_ok"] else " [BAD TAG]"
    rows = r["rows"] if r["rows"] is not None else "-"
    return (f"{flag} {r['task']:<34} rows={str(rows):>7}  "
            f"in {r['input_ok']}/{r['input_ok']+r['input_fail']}  "
            f"eval {r['eval_ok']}/{r['eval_ok']+r['eval_fail']}{tags}  {r['detail']}")

print(f"\n{'='*100}\nVerified {len(results)} registered tasks "
      f"(sampling {SAMPLE} rows each)\n{'='*100}")
for r in results:
    print(line(r))

ok = [r for r in results if r["status"] == "OK"]
warn = [r for r in results if r["status"] == "WARN"]
fail = [r for r in results if r["status"] == "FAIL"]
print(f"\nSUMMARY: {len(ok)} OK, {len(warn)} WARN, {len(fail)} FAIL")
if fail:
    print("FAIL:", ", ".join(r["task"] for r in fail))
if warn:
    print("WARN:", ", ".join(r["task"] for r in warn))
