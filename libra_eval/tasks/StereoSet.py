from .base import BaseDirectRiskyTask

# StereoSet: Measuring stereotypical bias in pretrained language models
# paper: https://arxiv.org/abs/2004.09456

class StereoSet(BaseDirectRiskyTask):
    task_name = "stereoset"
    task_data_file = "StereoSet.json"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "fairness"
