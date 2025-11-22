from .base import BaseDirectRiskyTask

# GA Jailbreak
# Genetic Algorithm generated jailbreak prompts

class GAJailbreak(BaseDirectRiskyTask):
    task_name = "ga_jailbreak"
    task_data_file = "GA Jailbreak.xlsx"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"
