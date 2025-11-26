from .base import GenericHarmfulTask

# RedEval HarmfulQA
# Note: Original RedEval task requires torch, this is a simplified version using GenericHarmfulTask

class RedEvalHarmfulQA(GenericHarmfulTask):
    task_name = "red_eval_harmful_qa"
    task_data_file = "RedEvalHarmfulQA.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
    llm_eval = True
    librai_evaluator_name = "Junjie Gao/Harmful_judge/V6"

