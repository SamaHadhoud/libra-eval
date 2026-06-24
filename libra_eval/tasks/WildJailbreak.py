import pandas as pd
from .base import GenericHarmfulTask

# WildJailbreak: In-the-Wild Jailbreak Prompts
# paper: https://arxiv.org/abs/2406.18510

class WildJailbreak(GenericHarmfulTask):
    task_name = "wildjailbreak"
    task_data_file = "WildJailbreak.csv"
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
        # 使用 Behavior 列作为用户输入
        # Use the Behavior column as the user input
        # 如果有 ContextString，使用它作为 system message
        # If there is a ContextString, use it as the system message
        def create_messages(row):
            messages = []
            # 添加 system message（可包含上下文）
            # Add the system message (may contain context)
            system_content = "You are a helpful assistant."
            if pd.notna(row.get('ContextString', '')) and str(row.get('ContextString', '')).strip():
                system_content = str(row['ContextString'])
            messages.append({"role": "system", "content": system_content})
            # 添加 user message
            # Add the user message
            messages.append({"role": "user", "content": str(row['Behavior'])})
            return messages

        data_df['messages'] = data_df.apply(create_messages, axis=1)

        return data_df
