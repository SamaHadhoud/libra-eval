from .base import GenericHarmfulTask

# MaliciousInstructions
# Note: Original MaliciousInstructions task requires torch, this is a simplified version using GenericHarmfulTask

class MaliciousInstructionsNew(GenericHarmfulTask):
    task_name = "malicious_instructions_new"
    task_data_file = "MaliciousInstructions.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
    llm_eval = True
    librai_evaluator_name = "Junjie Gao/Harmful_judge/V6"

