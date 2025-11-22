from .base import BaseDirectRiskyTask

# SORRY-Bench: Systematically Evaluating Large Language Model Safety Refusal Behaviors
# paper: https://arxiv.org/abs/2406.14598

class SORRYBench(BaseDirectRiskyTask):
    task_name = "sorry_bench"
    task_data_file = "SORRY-Bench.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
