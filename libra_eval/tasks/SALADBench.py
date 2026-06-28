from .base import BaseDirectRiskyTask

# SALAD-Bench: hierarchical safety benchmark
# paper:   https://arxiv.org/abs/2402.05044  (ACL 2024 Findings)
# dataset: https://huggingface.co/datasets/OpenSafetyLab/Salad-Data


class SALADBench(BaseDirectRiskyTask):
    """21,318 harmful questions (base_set) organized under a 3-level safety
    taxonomy (6 domains / 16 tasks / 66 categories). The harmful-content judge
    scores the response; `category` (top domain) and `subcategory` give a
    per-risk breakdown."""
    task_name = "salad_bench"
    task_data_file = "SALADBench.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
