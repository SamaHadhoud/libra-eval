from .base import BaseDirectRiskyTask

# GA Long-Context Jailbreak
# Long context jailbreak attacks using genetic algorithms

class GALongContextJailbreak(BaseDirectRiskyTask):
    task_name = "ga_long_context_jailbreak"
    task_data_file = "GA Long-Context Jailbreak.csv"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"
