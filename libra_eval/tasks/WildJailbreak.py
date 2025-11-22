from .base import BaseDirectRiskyTask

# WildJailbreak: In-the-Wild Jailbreak Prompts
# paper: https://arxiv.org/abs/2406.18510

class WildJailbreak(BaseDirectRiskyTask):
    task_name = "wildjailbreak"
    task_data_file = "WildJailbreak.csv"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"
