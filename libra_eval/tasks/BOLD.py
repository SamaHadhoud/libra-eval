from .base import BaseDirectRiskyTask

# BOLD: Bias in Open-Ended Language Generation Dataset
# paper: https://arxiv.org/abs/2101.11718

class BOLD(BaseDirectRiskyTask):
    task_name = "bold"
    task_data_file = "BOLD.json"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "fairness"
