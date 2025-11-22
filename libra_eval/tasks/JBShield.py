from .base import BaseDirectRiskyTask

# JBShield
# Jailbreak defense benchmark

class JBShield(BaseDirectRiskyTask):
    task_name = "jbshield"
    task_data_file = "JBShield.csv"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"
