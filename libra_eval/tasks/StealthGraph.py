from .base import BaseDirectRiskyTask

# StealthGraph: knowledge-graph-guided implicit domain-specific harmful prompts
# paper:  https://arxiv.org/abs/2601.04740
# github: https://github.com/ZJUIDG-AIVA/StealthGraph


class StealthGraph(BaseDirectRiskyTask):
    """3,163 domain-specific harmful prompts (medicine / finance / law /
    education) whose intent is obfuscated into *implicit* form via KG-guided
    rewriting, so they evade naive refusal triggers. We present the stealth
    (implicit) prompt and score the response with the harmful-content judge
    (refusing / staying safe -> 1.0). `domain` and `category` give per-subgroup
    breakdowns."""
    task_name = "stealth_graph"
    task_data_file = "StealthGraph.jsonl"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"
