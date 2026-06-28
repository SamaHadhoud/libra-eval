from .base import BaseDirectRiskyTask

# XSafety: multilingual safety benchmark
# paper:   https://arxiv.org/abs/2310.00905  (ACL 2024)
# github:  https://github.com/Jarviswang94/Multilingual_safety_benchmark


class XSafety(BaseDirectRiskyTask):
    """25,599 safety prompts across 10 languages (ar, bn, de, en, fr, hi, ja,
    ru, es, zh) and ~14 safety categories. Fills the multilingual safety gap.
    `language` and `category` give per-subgroup breakdowns."""
    task_name = "xsafety"
    task_data_file = "XSafety.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
