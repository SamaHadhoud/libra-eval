from .base import BaseDirectRiskyTask

# JBDistill-Bench
# Distilled jailbreak benchmark

class JBDistillBench(BaseDirectRiskyTask):
    task_name = "jbdistill_bench"
    task_data_file = "JBDistill-Bench.parquet"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"
