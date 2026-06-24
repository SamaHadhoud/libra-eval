import pandas as pd
import json
import os
from .base import BaseDirectRiskyTask

# BOLD: Bias in Open-Ended Language Generation Dataset
# paper: https://arxiv.org/abs/2101.11718

class BOLD(BaseDirectRiskyTask):
    task_name = "bold"
    task_data_file = "BOLD.json"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "fairness"

    def read_task_data(self):
        """重写数据读取方法，展开嵌套JSON结构
        Override the data reading method to flatten the nested JSON structure"""
        task_fpath = os.path.abspath(os.path.join(__file__, "../../datasets", self.task_data_file))

        with open(task_fpath, 'r') as f:
            bold_data = json.load(f)

        # 展开三层嵌套: category -> occupation -> prompts
        # Flatten the three-level nesting: category -> occupation -> prompts
        rows = []
        for category, occupations in bold_data.items():
            if isinstance(occupations, dict):
                for occupation, prompts in occupations.items():
                    if isinstance(prompts, list):
                        for prompt in prompts:
                            rows.append({
                                'category': category,
                                'occupation': occupation,
                                'prompt': prompt
                            })

        data_df = pd.DataFrame(rows)

        # 添加 messages 列
        # Add the messages column
        data_df['messages'] = data_df['prompt'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)}
        ])

        return data_df
