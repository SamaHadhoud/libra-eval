from .base import BaseOverRefusalTask

# FalseReject: improving contextual safety and mitigating over-refusals
# paper:   https://arxiv.org/abs/2505.08054
# dataset: https://huggingface.co/datasets/AmazonScience/FalseReject


class FalseReject(BaseOverRefusalTask):
    """FalseReject (test split): safe prompts that touch sensitive topics and
    are frequently over-refused. A safe model should ANSWER them; refusing
    counts as over-refusal."""
    task_name = "false_reject"
    task_data_file = "FalseReject.jsonl"
    attack_tag = "over_sensitive"
    round_tag = "single"
    risk_type_tag = "broad"
