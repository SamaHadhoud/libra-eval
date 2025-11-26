import json
import os

from .base import MODEL_LIST
from .openai_client import OpenAI_Client
from .next_client import Next_Client
from .local_client import Local_Client
from .librai_evaluator import LibrAI_Client


def _load_api_config(api_config_path: str | None = None) -> dict:
    """Load API配置，允许外部覆盖默认路径。"""
    if api_config_path is None:
        api_config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "config",
            "api_config.json",
        )
    with open(os.path.abspath(api_config_path), "r") as f:
        return json.load(f)


def get_client(
    client_type: str = "openai",
    model: str = "gpt-4o-mini-2024-07-18",
    api_config: dict | None = None,
    **kwargs,
):
    """
    根据类型创建指定LLM客户端，默认读取config/api_config.json。
    """
    if api_config is None:
        api_config = _load_api_config(kwargs.pop("api_config_path", None))

    if client_type == "openai":
        client_cls = OpenAI_Client
    elif client_type == "next":
        client_cls = Next_Client
    elif client_type == "local":
        client_cls = Local_Client
    else:
        raise ValueError(f"Unsupported client_type: {client_type}")

    return client_cls(model=model, api_config=api_config, **kwargs)
