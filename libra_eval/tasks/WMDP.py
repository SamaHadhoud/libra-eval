from .base import BaseDirectRiskyTask

# WMDP: Weapons of Mass Destruction Proxy
# paper: https://arxiv.org/abs/2403.03218

class WMDP(BaseDirectRiskyTask):
    task_name = "wmdp"
    task_data_file = "WMDP.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
