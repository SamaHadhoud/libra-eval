from .base import BaseDirectRiskyTask

# GA Jailbreak
# Genetic Algorithm generated jailbreak prompts

class GAJailbreak(BaseDirectRiskyTask):
    task_name = "ga_jailbreak"
    task_data_file = "GA Jailbreak.xlsx"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"

    def read_task_data(self):
        # The .xlsx file has no `messages` column; build it from the `question` column.
        data_df = super().read_task_data()
        data_df["messages"] = data_df["question"].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)},
        ])
        return data_df
