from .base import BaseDirectRiskyTask

# ClearHarm
# paper: https://arxiv.org/abs/2410.08590

class ClearHarm(BaseDirectRiskyTask):
    task_name = "clearharm"
    task_data_file = "ClearHarm.parquet"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"

    def read_task_data(self):
        """Override the data reading method, building the messages format from the prompt column."""
        data_df = super().read_task_data()

        # Convert the Parquet `prompt` column into the messages format
        data_df['messages'] = data_df['prompt'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)}
        ])

        return data_df
