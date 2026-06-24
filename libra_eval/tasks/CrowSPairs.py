import pandas as pd
from .base import BaseDirectRiskyTask

# CrowS-Pairs: A Challenge Dataset for Measuring Social Biases
# paper: https://arxiv.org/abs/2010.00133

class CrowSPairs(BaseDirectRiskyTask):
    task_name = "crows_pairs"
    task_data_file = "CrowS-Pairs.csv"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "fairness"

    def read_task_data(self):
        """重写数据读取方法，添加格式转换
        Override the data reading method to add format conversion"""
        # 调用父类方法读取 CSV 文件
        # Call the parent class method to read the CSV file
        data_df = super().read_task_data()

        # 将 CSV 格式转换为 messages 格式（使用 prompt 列）
        # Convert the CSV format to messages format (using the prompt column)
        data_df['messages'] = data_df['prompt'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)}
        ])

        return data_df
