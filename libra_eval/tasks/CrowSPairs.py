from .base import BaseDirectRiskyTask

# CrowS-Pairs: A Challenge Dataset for Measuring Social Biases
# paper: https://arxiv.org/abs/2010.00133

class CrowSPairs(BaseDirectRiskyTask):
    task_name = "crows_pairs"
    task_data_file = "CrowS-Pairs.csv"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "fairness"
