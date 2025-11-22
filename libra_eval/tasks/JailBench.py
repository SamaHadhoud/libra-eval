from .base import BaseDirectRiskyTask

# JailBench
# paper: https://arxiv.org/abs/2404.01318

class JailBench(BaseDirectRiskyTask):
    task_name = "jailbench"
    task_data_file = "JailBench.csv"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"
