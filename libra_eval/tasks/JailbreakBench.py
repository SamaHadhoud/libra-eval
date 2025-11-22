from .base import BaseDirectRiskyTask

# JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models
# paper: https://arxiv.org/abs/2404.01318

class JailbreakBench(BaseDirectRiskyTask):
    task_name = "jailbreakbench"
    task_data_file = "JailbreakBench.csv"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"
