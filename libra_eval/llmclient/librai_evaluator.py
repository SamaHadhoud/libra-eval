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
        # Use the OpenAI client, setting base_url to LibrAI's API
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://prompter.librai.tech/api/llm/v1"
        )

    def call_librai_evaluator(self, mapped_data: dict, evaluator_name: str = "Junjie Gao/Harmful_judge/V6", timeout: int = 60):
        """
        使用 OpenAI 兼容格式调用 LibrAI 评估器
        Call the LibrAI evaluator using the OpenAI-compatible format

        Args:
            mapped_data: 评估器输入数据
            mapped_data: evaluator input data
            evaluator_name: 评估器名称
            evaluator_name: evaluator name
            timeout: API 超时时间（秒），默认 60 秒
            timeout: API timeout (seconds), defaults to 60 seconds
        """
        try:
            # 将 mapped_data 转换为 JSON 字符串，作为 user message 的 content
            # Convert mapped_data into a JSON string to use as the content of the user message
            prompter_data = json.dumps(mapped_data)

            messages = [
                {
                    "role": "user",
                    "content": prompter_data
                }
            ]

            # 调用 OpenAI 兼容的 API，添加超时控制
            # Call the OpenAI-compatible API, adding timeout control
            response = self.client.chat.completions.create(
                model=evaluator_name,  # 使用评估器名称作为 model | Use the evaluator name as the model
                messages=messages,
                temperature=0.7,
                max_completion_tokens=1000,
                timeout=timeout  # 添加超时控制 | Add timeout control
            )

            # 提取响应内容
            # Extract the response content
            ai_response = response.choices[0].message.content
            
            # 尝试从 markdown 代码块中提取 JSON
            # Try to extract JSON from a markdown code block
            if "```json" in ai_response or "```" in ai_response:
                # 提取代码块中的内容
                # Extract the content inside the code block
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    ai_response = json_match.group(1)
            
            # 尝试解析为 JSON（如果评估器返回 JSON）
            # Try to parse as JSON (if the evaluator returns JSON)
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                # 如果不是 JSON，返回原始字符串
                # If it is not JSON, return the original string
                return ai_response
                
        except Exception as e:
            raise Exception(f"Error in LibrAI Evaluator: {e}, please check https://prompter.librai.tech/APIDoc for error code.")

    def _call(self, messages, **kwargs):
        """实现 BaseClient 的 _call 方法
        Implements the _call method of BaseClient

        Args:
            messages: 可能是：
            messages: may be:
                1. 字典格式（评估器数据）: {"question": "...", "response": "..."}
                1. dict format (evaluator data): {"question": "...", "response": "..."}
                2. 标准 messages 格式: [{"role": "user", "content": "..."}]
                2. standard messages format: [{"role": "user", "content": "..."}]
                3. 列表包含字典: [{"question": "...", "response": "..."}]
                3. a list containing a dict: [{"question": "...", "response": "..."}]
        """
        num_retries = kwargs.get("num_retries", 1)
        evaluator_name = kwargs.get("evaluator_name", None)
        post_check_function = kwargs.get("post_check_function", None)
        assert evaluator_name is not None, "evaluator_name must be provided"

        # 处理输入格式
        # Handle the input format
        mapped_data = {}

        if isinstance(messages, dict):
            # 直接传入的是字典（最常见的情况，来自 _single_eval_message）
            # Directly passed in as a dict (the most common case, from _single_eval_message)
            mapped_data = messages
        elif isinstance(messages, list) and len(messages) > 0:
            # 如果是列表
            # If it is a list
            if isinstance(messages[0], dict):
                if "role" in messages[0]:
                    # 标准 messages 格式
                    # Standard messages format
                    # 检查评估器是否期望 conversation 格式（如 Harmful_judge）
                    # Check whether the evaluator expects the conversation format (e.g. Harmful_judge)
                    if evaluator_name and ("Harmful_judge" in evaluator_name or "Harmful_Judger" in evaluator_name):
                        # 转换为 conversation 格式
                        # Convert to the conversation format
                        mapped_data = {"conversation": messages}
                    else:
                        # 对于其他评估器，尝试提取 content
                        # For other evaluators, try to extract content
                        if "content" in messages[0]:
                            content = messages[0]["content"]
                            # 尝试解析为 JSON（可能是 mapped_data 的 JSON 字符串）
                            # Try to parse as JSON (it may be a JSON string of mapped_data)
                            try:
                                mapped_data = json.loads(content)
                            except (json.JSONDecodeError, TypeError):
                                # 如果不是 JSON，可能是直接的字符串，需要包装
                                # If it is not JSON, it may be a plain string that needs to be wrapped
                                mapped_data = {"content": content}
                else:
                    # 列表中的字典没有 role，可能是直接的 mapped_data
                    # The dict in the list has no role; it may be mapped_data directly
                    mapped_data = messages[0]
            else:
                mapped_data = {}
        else:
            mapped_data = {}

        # 获取超时参数，默认 60 秒
        # Get the timeout parameter, defaults to 60 seconds
        timeout = kwargs.get("timeout", 60)

        r = ""
        for i in range(num_retries):
            try:
                r = self.call_librai_evaluator(mapped_data, evaluator_name, timeout=timeout)

                if post_check_function is None:
                    time.sleep(0.3)  # 每次成功调用后延迟0.3秒，避免rate limit | Delay 0.3 seconds after each successful call to avoid rate limit
                    break
                else:
                    post_r = post_check_function(r)
                    if post_r:
                        time.sleep(0.3)  # 每次成功调用后延迟0.3秒，避免rate limit | Delay 0.3 seconds after each successful call to avoid rate limit
                        return post_r
                    else:
                        logger.warning(f"Warning: Post check function failed. Response is {r} Retrying {i} ...")
            except Exception as e:
                error_msg = str(e).lower()
                # 特殊处理超时错误
                # Special handling for timeout errors
                if "timeout" in error_msg or "timed out" in error_msg:
                    logger.error(f"API timeout on attempt {i+1}/{num_retries}: {evaluator_name}")
                    if i < num_retries - 1:
                        logger.info(f"Retrying after timeout...")
                        time.sleep(2)
                    else:
                        logger.error("All retries failed due to timeout")
                        return ""  # 返回空字符串而不是抛出异常 | Return an empty string instead of raising an exception
                else:
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
        """记录 token 使用情况（LibrAI API 可能不提供详细的 token 信息）
        Record token usage (the LibrAI API may not provide detailed token information)
        """
        # LibrAI API 可能不提供 token 使用信息，这里留空
        # The LibrAI API may not provide token usage information, so this is left empty
        pass

    def construct_message_list(self, user_inputs: list[str], sys_inputs: list[str]) -> list[str]:
        """构造消息列表（用于兼容 BaseClient 接口）
        Construct the message list (for compatibility with the BaseClient interface)
        """
        messages = []
        for sys_input, user_input in zip(sys_inputs, user_inputs):
            if sys_input:
                messages.append({"role": "system", "content": sys_input})
            messages.append({"role": "user", "content": user_input})
        return messages


class LibrAIEvaluator(LibrAI_Client):
    """向后兼容旧命名，避免外部 import 失败。
    Backward-compatible with the old name to avoid external import failures.
    """
    pass
