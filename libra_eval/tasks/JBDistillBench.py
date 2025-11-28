import pandas as pd
from .base import BaseDirectRiskyTask

# JBDistill-Bench
# Distilled jailbreak benchmark

class JBDistillBench(BaseDirectRiskyTask):
    task_name = "jbdistill_bench"
    task_data_file = "JBDistill-Bench.parquet"
    attack_tag = "adversarial"
    round_tag = "single"
    risk_type_tag = "broad"

    def read_task_data(self):
        """重写数据读取方法，添加格式转换"""
        # 调用父类方法读取 Parquet 文件
        data_df = super().read_task_data()

        # 将 Parquet 格式转换为 messages 格式（使用 prompt 列）
        data_df['messages'] = data_df['prompt'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)}
        ])

        return data_df
