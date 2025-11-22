from .base import BaseDirectRiskyTask

# ToxicChat: Unveiling Hidden Challenges of Toxicity Detection in Real-World User-AI Conversation
# paper: https://arxiv.org/abs/2310.17389

class ToxicChat(BaseDirectRiskyTask):
    task_name = "toxicchat"
    task_data_file = "ToxicChat.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "toxicity"
