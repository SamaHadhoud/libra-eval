import pandas as pd
from .base import GenericHarmfulTask

# JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models
# paper: https://arxiv.org/abs/2404.01318

class JailbreakBench(GenericHarmfulTask):
    task_name = "jailbreakbench"
    task_data_file = "JailbreakBench.csv"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"

    def read_task_data(self):
        """重写数据读取方法，添加格式转换
        Override the data reading method to add format conversion"""
        # 调用父类方法读取 CSV 文件
        # Call the parent class method to read the CSV file
        data_df = super().read_task_data()

        # 将 CSV 格式转换为 messages 格式（使用 Goal 列）
        # Convert the CSV format to the messages format (using the Goal column)
        data_df['messages'] = data_df['Goal'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)}
        ])

        return data_df
