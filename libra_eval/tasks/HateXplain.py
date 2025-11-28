import pandas as pd
import json
import os
from .base import BaseDirectRiskyTask

# HateXplain: A Benchmark Dataset for Explainable Hate Speech Detection
# paper: https://arxiv.org/abs/2012.10289

class HateXplain(BaseDirectRiskyTask):
    task_name = "hatexplain"
    task_data_file = "HateXplain.json"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "toxicity"

    def read_task_data(self):
        """重写数据读取方法，连接 post_tokens 成文本"""
        task_fpath = os.path.abspath(os.path.join(__file__, "../../datasets", self.task_data_file))

        with open(task_fpath, 'r') as f:
            hate_data = json.load(f)

        # 展开字典结构，连接 tokens
        rows = []
        for post_id, post_info in hate_data.items():
            post_tokens = post_info.get('post_tokens', [])
            post_text = ' '.join(post_tokens)

            # 获取标签（多个标注者可能有不同标签，这里取多数）
            labels = [ann.get('label') for ann in post_info.get('annotators', [])]

            rows.append({
                'post_id': post_id,
                'post_text': post_text,
                'labels': labels
            })

        data_df = pd.DataFrame(rows)

        # 添加 messages 列
        data_df['messages'] = data_df['post_text'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)}
        ])

        return data_df
