import time
import json
import re
import traceback
from openai import OpenAI
from .base import BaseClient
from libra_eval.utils.logger import logger

class LibrAI_Client(BaseClient):
    def __init__(
        self,
        api_key: str,
        max_requests_per_minute=200,
        request_window=60,
    ) -> None:
        super().__init__("", "", max_requests_per_minute, request_window)
        self.api_key = api_key
        # 使用 OpenAI 客户端，设置 base_url 为 LibrAI 的 API
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://prompter.librai.tech/api/llm/v1"
        )

    def call_librai_evaluator(self, evaluator_name: str, mapped_data: dict):
        """使用 OpenAI 兼容格式调用 LibrAI 评估器"""
        try:
            # 将 mapped_data 转换为 JSON 字符串，作为 user message 的 content
            prompter_data = json.dumps(mapped_data)
            
            messages = [
                {
                    "role": "user",
                    "content": prompter_data
                }
            ]
            
            # 调用 OpenAI 兼容的 API
            response = self.client.chat.completions.create(
                model=evaluator_name,  # 使用评估器名称作为 model
                messages=messages,
                temperature=0.7,
                max_completion_tokens=1000
            )
            
            # 提取响应内容
            ai_response = response.choices[0].message.content
            
            # 尝试从 markdown 代码块中提取 JSON
            if "```json" in ai_response or "```" in ai_response:
                # 提取代码块中的内容
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    ai_response = json_match.group(1)
            
            # 尝试解析为 JSON（如果评估器返回 JSON）
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                # 如果不是 JSON，返回原始字符串
                return ai_response
                
        except Exception as e:
            raise Exception(f"Error in LibrAI Evaluator: {e}, please check https://prompter.librai.tech/APIDoc for error code.")

    def _call(self, messages, **kwargs):
        """实现 BaseClient 的 _call 方法
        
        Args:
            messages: 可能是：
                1. 字典格式（评估器数据）: {"question": "...", "response": "..."}
                2. 标准 messages 格式: [{"role": "user", "content": "..."}]
                3. 列表包含字典: [{"question": "...", "response": "..."}]
        """
        num_retries = kwargs.get("num_retries", 1)
        evaluator_name = kwargs.get("evaluator_name", None)
        post_check_function = kwargs.get("post_check_function", None)
        assert evaluator_name is not None, "evaluator_name must be provided"

        # 处理输入格式
        mapped_data = {}
        
        if isinstance(messages, dict):
            # 直接传入的是字典（最常见的情况，来自 _single_eval_message）
            mapped_data = messages
        elif isinstance(messages, list) and len(messages) > 0:
            # 如果是列表
            if isinstance(messages[0], dict):
                if "role" in messages[0]:
                    # 标准 messages 格式，提取 content
                    if "content" in messages[0]:
                        content = messages[0]["content"]
                        # 尝试解析为 JSON（可能是 mapped_data 的 JSON 字符串）
                        try:
                            mapped_data = json.loads(content)
                        except (json.JSONDecodeError, TypeError):
                            # 如果不是 JSON，可能是直接的字符串，需要包装
                            mapped_data = {"content": content}
                else:
                    # 列表中的字典没有 role，可能是直接的 mapped_data
                    mapped_data = messages[0]
            else:
                mapped_data = {}
        else:
            mapped_data = {}

        r = ""
        for i in range(num_retries):
            try:
                r = self.call_librai_evaluator(evaluator_name, mapped_data)

                if post_check_function is None:
                    break
                else:
                    post_r = post_check_function(r)
                    if post_r:
                        return post_r
                    else:
                        logger.warning(f"Warning: Post check function failed. Response is {r} Retrying {i} ...")
            except Exception as e:
                logger.error(f"Error in LibrAI Evaluator: {e}")
                logger.debug(traceback.format_exc())
                if i < num_retries - 1:
                    time.sleep(1)
                else:
                    raise
                    
        if r == "":
            raise ValueError("LibrAI Evaluator Error, output is empty.")
        return r

    def _log_usage(self):
        """记录 token 使用情况（LibrAI API 可能不提供详细的 token 信息）"""
        # LibrAI API 可能不提供 token 使用信息，这里留空
        pass

    def construct_message_list(self, user_inputs: list[str], sys_inputs: list[str]) -> list[str]:
        """构造消息列表（用于兼容 BaseClient 接口）"""
        messages = []
        for sys_input, user_input in zip(sys_inputs, user_inputs):
            if sys_input:
                messages.append({"role": "system", "content": sys_input})
            messages.append({"role": "user", "content": user_input})
        return messages
