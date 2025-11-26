from .base import GenericHarmfulTask

# MaliciousInstruct
# Note: Original MaliciousInstruct task requires torch, this is a simplified version using GenericHarmfulTask

class MaliciousInstructNew(GenericHarmfulTask):
    task_name = "malicious_instruct_new"
    task_data_file = "MaliciousInstruct.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
    llm_eval = True
    librai_evaluator_name = "Junjie Gao/Harmful_judge/V6"

