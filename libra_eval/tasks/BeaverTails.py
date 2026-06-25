from .base import BaseDirectRiskyTask

# paper: https://arxiv.org/abs/2307.04657
# dataset: https://huggingface.co/datasets/PKU-Alignment/BeaverTails?row=5
#
# BeaverTails labels (prompt, response) PAIRS by whether the *reference response*
# was safe -- NOT by whether the prompt is benign. Both subsets therefore contain
# harmful prompts (the "good" subset just had a safe reference response, often
# because it refused). Since we judge our model's freshly-generated response, the
# source label is irrelevant: both subsets are scored as direct-risky safety
# (1.0 = our model's response is not harmful). The two differ only in prompt
# distribution. (BeaverTailsGood was previously framed as over-refusal, which
# wrongly penalized the model for correctly refusing the harmful prompts in it.)


class BeaverTailsBad(BaseDirectRiskyTask):
    task_name = "beavertails_bad"
    task_data_file = "BeaverTailsBad.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"


class BeaverTailsGood(BaseDirectRiskyTask):
    task_name = "beavertails_good"
    task_data_file = "BeaverTailsGood.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
