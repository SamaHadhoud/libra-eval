from .base import BaseDirectRiskyTask

# CoSafe: multi-turn dialogue safety via coreference / context dependency
# paper:   https://aclanthology.org/2024.emnlp-main.968/  (EMNLP 2024)
# github:  https://github.com/ErxinYu/CoSafe-Dataset


class CoSafe(BaseDirectRiskyTask):
    """1,400 five-turn dialogues whose final user query relies on the earlier
    (benign-looking) context to elicit unsafe content. The model answers that
    final turn given the full history; the harmful-content judge scores its reply
    (refusing / staying safe -> 1.0)."""
    task_name = "cosafe"
    task_data_file = "CoSafe.jsonl"
    attack_tag = "adversarial"
    round_tag = "multi"
    risk_type_tag = "broad"
