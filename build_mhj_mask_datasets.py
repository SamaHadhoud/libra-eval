#!/usr/bin/env python3
"""Fetch + convert MHJ (multi-turn escalation) and MASK (honesty under pressure)
from Hugging Face into libra-eval `messages`-format JSONL datasets.

Both source repos are gated; run while authenticated (a cached HF token at
~/.cache/huggingface/token or HF_TOKEN env works). Re-runnable / idempotent.

Outputs (into libra_eval/datasets/):
  MHJ.jsonl                 537 human multi-turn jailbreaks  -> harmful judge (multi)
  MASKProvidedFacts.jsonl   274 in-context honesty-under-pressure -> MASK_Honesty judge
  MASKKnownFacts.jsonl      209 world-fact honesty-under-pressure -> MASK_Honesty judge
"""
import os, json
import pandas as pd
from huggingface_hub import hf_hub_download

DEST = os.path.join(os.path.dirname(__file__), "libra_eval", "datasets")
os.makedirs(DEST, exist_ok=True)


def build_mhj():
    """ScaleAI/mhj: each row has message_0..message_N as JSON {"body","role"}
    strings (all system/user turns of a human jailbreak). We keep the full
    escalation as the conversation; the model answers the final user turn and
    the standard harmful judge scores that answer."""
    p = hf_hub_download("ScaleAI/mhj", "harmbench_behaviors.csv", repo_type="dataset")
    df = pd.read_csv(p)
    msg_cols = [c for c in df.columns if c.startswith("message_")]
    # message_0, message_1, ... in order
    msg_cols = sorted(msg_cols, key=lambda c: int(c.split("_")[1]))

    rows = []
    for _, r in df.iterrows():
        messages = []
        for c in msg_cols:
            v = r[c]
            if not isinstance(v, str) or not v.strip():
                continue
            try:
                m = json.loads(v)
            except Exception:
                continue
            role = m.get("role", "user")
            content = m.get("body", "")
            messages.append({"role": role, "content": content})
        # need at least one user turn, and the conversation must end on a user turn
        if not messages or messages[-1]["role"] != "user":
            continue
        if not any(m["role"] == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})
        rows.append({
            "messages": messages,
            "tactic": r.get("tactic", ""),
            "source": r.get("Source", ""),
            "question_id": int(r["question_id"]) if pd.notna(r.get("question_id")) else -1,
            "goal": r.get("submission_message", ""),
        })
    out = os.path.join(DEST, "MHJ.jsonl")
    pd.DataFrame(rows).to_json(out, orient="records", lines=True, force_ascii=False)
    print(f"MHJ: wrote {len(rows)} rows -> {out}")


def build_mask(cfg, fname):
    """cais/MASK: a pressuring system_prompt + user_prompt push the model to
    assert the false side of a <pivotal>...</pivotal> proposition with a known
    ground_truth. We keep the pressure turn as the input; the MASK_Honesty judge
    decides whether the response asserts the false side (a lie)."""
    p = hf_hub_download("cais/MASK", f"{cfg}/test-00000-of-00001.parquet", repo_type="dataset")
    df = pd.read_parquet(p)
    rows = []
    for _, r in df.iterrows():
        sysp = str(r.get("system_prompt") or "").strip()
        userp = str(r.get("user_prompt") or "").strip()
        if not userp:
            continue
        messages = []
        if sysp:
            messages.append({"role": "system", "content": sysp})
        messages.append({"role": "user", "content": userp})
        rows.append({
            "messages": messages,
            "proposition": r.get("proposition", ""),
            "ground_truth": r.get("ground_truth", ""),
            "formatted_ground_truth": str(r.get("formatted_ground_truth", "")),
            "type": r.get("type", ""),
            "task_id": r.get("task_id", ""),
            "config": cfg,
        })
    out = os.path.join(DEST, fname)
    pd.DataFrame(rows).to_json(out, orient="records", lines=True, force_ascii=False)
    print(f"MASK/{cfg}: wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    build_mhj()
    build_mask("provided_facts", "MASKProvidedFacts.jsonl")
    build_mask("known_facts", "MASKKnownFacts.jsonl")
