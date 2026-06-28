from .base import BaseDirectRiskyTask

# Aya Red-teaming: human-written multilingual red-team prompts
# paper:   https://arxiv.org/abs/2406.18682  (Aya / Cohere For AI, 2024)
# dataset: https://huggingface.co/datasets/CohereForAI/aya_redteaming


class AyaRedTeaming(BaseDirectRiskyTask):
    """7,419 human-written harmful prompts across 8 languages (Arabic, English,
    French, Hindi, Russian, Spanish, Serbian, Tagalog). Fills the multilingual
    safety gap. `language` and `category` give per-subgroup breakdowns."""
    task_name = "aya_redteaming"
    task_data_file = "AyaRedTeaming.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
