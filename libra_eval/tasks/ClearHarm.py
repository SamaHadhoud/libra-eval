from .base import BaseDirectRiskyTask

# ClearHarm
# paper: https://arxiv.org/abs/2410.08590

class ClearHarm(BaseDirectRiskyTask):
    task_name = "clearharm"
    task_data_file = "ClearHarm.parquet"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
