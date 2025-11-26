from .base import GenericHarmfulTask

# HarmBench
# paper: https://arxiv.org/abs/2402.04249
# Note: Original HarmBench task requires torch, this is a simplified version using GenericHarmfulTask

class HarmBenchNew(GenericHarmfulTask):
    task_name = "harm_bench_new"
    task_data_file = "HarmBench.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
    llm_eval = True
    librai_evaluator_name = "Junjie Gao/Harmful_judge/V6"

