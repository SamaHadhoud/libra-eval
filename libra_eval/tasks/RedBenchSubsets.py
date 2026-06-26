"""Standalone safety datasets surfaced via the RedBench compilation.

RedBench (arXiv:2601.03699) re-bundles ~37 existing safety benchmarks under one
normalized schema. Most already exist in this repo; the classes below add the
non-overlapping subsets as individual tasks (prompts only — RedBench's own model
annotations are dropped). Source repo: https://huggingface.co/datasets/knoveleng/redbench
"""

from .base import BaseDirectRiskyTask


class CatQA(BaseDirectRiskyTask):
    """CatQA: categorized harmful questions across 11 risk categories.
    paper: https://arxiv.org/abs/2308.09662"""
    task_name = "catqa"
    task_data_file = "CatQA.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"


class ForbiddenQuestions(BaseDirectRiskyTask):
    """Forbidden Question Set: prompts targeting OpenAI-disallowed scenarios.
    paper: https://arxiv.org/abs/2308.03825 ('Do Anything Now')"""
    task_name = "forbidden_questions"
    task_data_file = "ForbiddenQuestions.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"


class GPTFuzzer(BaseDirectRiskyTask):
    """GPTFuzzer: auto-generated jailbreak prompts seeking harmful content.
    paper: https://arxiv.org/abs/2309.10253"""
    task_name = "gptfuzzer"
    task_data_file = "GPTFuzzer.jsonl"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"


class MedSafetyBench(BaseDirectRiskyTask):
    """MedSafetyBench: medical-harm requests violating medical ethics.
    paper: https://arxiv.org/abs/2403.03744 (NeurIPS 2024)"""
    task_name = "med_safety_bench"
    task_data_file = "MedSafetyBench.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
