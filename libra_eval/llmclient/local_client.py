import openai
from .base import MODEL_LIST
from .openai_client import OpenAI_Client

name_mapping = {k:k for k in MODEL_LIST}


class Local_Client(OpenAI_Client):
    def __init__(
        self,
        model: str = "",
        api_config: dict = None,
        max_requests_per_minute=20,
        request_window=10,
        client_name="Local",
    ):
        super().__init__(model=model, api_config=api_config, max_requests_per_minute=max_requests_per_minute, request_window=request_window, client_name=client_name)
        self.client_name = client_name

        # 从配置文件读取本地模型的 base_url 和 api_key
        assert "LOCAL_BASE_URL" in api_config and api_config["LOCAL_BASE_URL"] != "", "LOCAL_BASE_URL must be set in api_config.json"
        assert "LOCAL_API_KEY" in api_config and api_config["LOCAL_API_KEY"] != "", "LOCAL_API_KEY must be set in api_config.json"
        
        self.client = openai.OpenAI(
            base_url=api_config["LOCAL_BASE_URL"],
            api_key=api_config["LOCAL_API_KEY"],
        )
        self.name_mapping = name_mapping
