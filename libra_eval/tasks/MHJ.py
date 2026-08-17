from .base import BaseDirectRiskyTask

# MHJ — Multi-Turn Human Jailbreaks
# paper:  "LLM Defenses Are Not Robust to Multi-Turn Human Jailbreaks Yet" (Scale AI, 2024)
# arXiv:  2408.15221   ·   data: hf/ScaleAI/mhj
#
# 537 human-authored multi-turn jailbreaks that defeat single-turn-safe models.
# Each row is a sequence of escalating human (user) turns; there are no target
# assistant turns in the source. We present the full escalation as the
# conversation and let the model under test answer the final user turn; the
# standard harmful-content judge scores that final answer (refusing / staying
# safe -> 1.0). This is the single-pass "final-turn" replay; a fully faithful
# turn-by-turn replay (model responds and history accumulates each turn) is a
# future enhancement — it needs sequential generation the pipeline does not do.


class MHJ(BaseDirectRiskyTask):
    task_name = "mhj"
    task_data_file = "MHJ.jsonl"
    attack_tag = "adversarial"
    round_tag = "multi"
    risk_type_tag = "broad"
    # inherits llm_eval=True + harmful judge + safety_refusal_rate scoring
