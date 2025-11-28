import pandas as pd
from .base import BaseDirectRiskyTask

# SORRY-Bench: Systematically Evaluating Large Language Model Safety Refusal Behaviors
# paper: https://arxiv.org/abs/2406.14598

class SORRYBench(BaseDirectRiskyTask):
    task_name = "sorry_bench"
    task_data_file = "SORRY-Bench.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "broad"

    def read_task_data(self):
        """重写数据读取方法，添加格式转换"""
        # 调用父类方法读取 JSONL 文件
        data_df = super().read_task_data()

        # 将 JSONL 格式转换为 messages 格式（使用 turns 列的第一个元素）
        def extract_first_turn(turns):
            if isinstance(turns, list) and len(turns) > 0:
                return turns[0]
            return str(turns)

        data_df['messages'] = data_df['turns'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": extract_first_turn(x)}
        ])

        return data_df
