from .base import BaseDirectRiskyTask

# DiaSafety: context-sensitive dialogue safety
# paper:   https://aclanthology.org/2022.findings-acl.308/  (ACL Findings 2022)
# github:  https://github.com/thu-coai/DiaSafety
# dataset: https://huggingface.co/datasets/thu-coai/diasafety

# NOTE: DiaSafety ships labeled (context, response) pairs for classification.
# Here it is used generatively: the model produces a response to each context and
# the harmful-content judge scores that response (a contextually-safe reply ->
# 1.0). The original `label` / `response` are kept as metadata only. The existing
# `dialogue_safety` task (ParlAI) covers the classification framing.


class DiaSafety(BaseDirectRiskyTask):
    task_name = "diasafety"
    task_data_file = "DiaSafety.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
