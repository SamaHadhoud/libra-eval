import pandas as pd
from .base import BaseDirectRiskyTask

# ToxicChat: Unveiling Hidden Challenges of Toxicity Detection in Real-World User-AI Conversation
# paper: https://arxiv.org/abs/2310.17389

class ToxicChat(BaseDirectRiskyTask):
    task_name = "toxicchat"
    task_data_file = "ToxicChat.jsonl"
    attack_tag = "direct_risky"
    round_tag = "single"
    risk_type_tag = "toxicity"

    def read_task_data(self):
        """重写数据读取方法，提取 reddit_thread 的最后一条消息
        Override the data reading method to extract the last message of the reddit_thread"""
        # 调用父类方法读取 JSONL 文件
        # Call the parent class method to read the JSONL file
        data_df = super().read_task_data()

        # 提取最后一个 turn 的 text 作为 prompt
        # Extract the text of the last turn as the prompt
        def extract_last_turn_text(thread):
            if isinstance(thread, list) and len(thread) > 0:
                # 获取最后一个用户消息
                # Get the last user message
                last_turn = thread[-1]
                return last_turn.get('text', '')
            return ''

        data_df['user_text'] = data_df['reddit_thread'].apply(extract_last_turn_text)

        # 添加 messages 列
        # Add the messages column
        data_df['messages'] = data_df['user_text'].apply(lambda x: [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": str(x)}
        ])

        return data_df
