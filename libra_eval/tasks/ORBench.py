from .base import BaseOverRefusalTask, BaseDirectRiskyTask

# OR-Bench: Over-Refusal Benchmark
# paper:   https://arxiv.org/abs/2405.20947
# github:  https://github.com/justincui03/or-bench
# dataset: https://huggingface.co/datasets/bench-llm/or-bench


class ORBenchHard1K(BaseOverRefusalTask):
    """or-bench-hard-1k: seemingly-toxic-but-actually-safe prompts. A safe model
    should ANSWER these; refusing counts as over-refusal."""
    task_name = "or_bench_hard_1k"
    task_data_file = "ORBenchHard.jsonl"
    attack_tag = "over_sensitive"
    round_tag = "single"
    risk_type_tag = "broad"


class ORBenchToxic(BaseDirectRiskyTask):
    """or-bench-toxic: the paired genuinely-harmful prompts that a safe model
    should REFUSE. Scored with the harmful-content judge."""
    task_name = "or_bench_toxic"
    task_data_file = "ORBenchToxic.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"
