from .base import BaseDirectRiskyTask

# RealToxicityPrompts: Evaluating Neural Toxic Degeneration in Language Models
# paper: https://arxiv.org/abs/2009.11462

class RealToxicityPrompts(BaseDirectRiskyTask):
    task_name = "realtoxicityprompts"
    task_data_file = "RealToxicityPrompts.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "toxicity"
