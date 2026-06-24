import pandas as pd
from .base import GenericHarmfulTask

# JBShield
# Jailbreak defense benchmark

class JBShield(GenericHarmfulTask):
    task_name = "jbshield"
    task_data_file = "JBShield.csv"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"

    def read_task_data(self):
        """重写数据读取方法，添加格式转换
        Override the data reading method, adding format conversion"""
        # 调用父类方法读取 CSV 文件
        # Call the parent class method to read the CSV file
        data_df = super().read_task_data()

        # 将 CSV 格式转换为 messages 格式
        # Convert the CSV format into the messages format
        data_df['messages'] = data_df['prompt'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)}
        ])

        return data_df
