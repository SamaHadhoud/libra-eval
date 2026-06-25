import pandas as pd
from .base import GenericHarmfulTask, BaseOverRefusalTask

# JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models
# paper: https://arxiv.org/abs/2404.01318

class JailbreakBench(GenericHarmfulTask):
    task_name = "jailbreakbench"
    task_data_file = "JailbreakBench.csv"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"

    def read_task_data(self):
        """Override the data reading method to add format conversion."""
        # Call the parent class method to read the CSV file
        data_df = super().read_task_data()

        # Convert the CSV format to the messages format (using the Goal column)
        data_df['messages'] = data_df['Goal'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)}
        ])

        return data_df


class JailbreakBenchBenign(BaseOverRefusalTask):
    """JBB-Behaviors benign-behavior subset, used for over-refusal evaluation.

    JBB-Behaviors now contains 100 harmful behaviors (the JailbreakBench task) and
    100 benign behaviors. Each benign request is paired with a harmful one and should
    be answered normally rather than refused.
    """
    task_name = "jailbreakbench_benign"
    task_data_file = "JailbreakBench-Benign.csv"
    attack_tag = "over_sensitive"
    round_tag = "single"
    risk_type_tag = "broad"

    def read_task_data(self):
        """Override the data reading method to add format conversion."""
        data_df = super().read_task_data()
        # Build the messages format using the Goal column
        data_df['messages'] = data_df['Goal'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)}
        ])
        return data_df
