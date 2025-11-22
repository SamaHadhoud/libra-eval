from .base import BaseDirectRiskyTask

# HateXplain: A Benchmark Dataset for Explainable Hate Speech Detection
# paper: https://arxiv.org/abs/2012.10289

class HateXplain(BaseDirectRiskyTask):
    task_name = "hatexplain"
    task_data_file = "HateXplain.json"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "toxicity"
