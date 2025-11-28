import pandas as pd
import json
import os
from .base import BaseDirectRiskyTask

# StereoSet: Measuring stereotypical bias in pretrained language models
# paper: https://arxiv.org/abs/2004.09456

class StereoSet(BaseDirectRiskyTask):
    task_name = "stereoset"
    task_data_file = "StereoSet.json"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "fairness"

    def read_task_data(self):
        """重写数据读取方法，提取 context 字段"""
        task_fpath = os.path.abspath(os.path.join(__file__, "../../datasets", self.task_data_file))

        with open(task_fpath, 'r') as f:
            stereo_data = json.load(f)

        # 提取 intrasentence 数据（也可以考虑 intersentence）
        rows = []
        for item_type in ['intrasentence', 'intersentence']:
            if item_type in stereo_data.get('data', {}):
                for item in stereo_data['data'][item_type]:
                    rows.append({
                        'id': item.get('id'),
                        'target': item.get('target'),
                        'bias_type': item.get('bias_type'),
                        'context': item.get('context'),
                        'type': item_type
                    })

        data_df = pd.DataFrame(rows)

        # 添加 messages 列（使用 context 作为 prompt）
        data_df['messages'] = data_df['context'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)}
        ])

        return data_df
