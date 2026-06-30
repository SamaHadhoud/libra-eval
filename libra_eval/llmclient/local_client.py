import os
import openai
from .base import MODEL_LIST
from .openai_client import OpenAI_Client

name_mapping = {k:k for k in MODEL_LIST}


class Local_Client(OpenAI_Client):
    def __init__(
        self,
        model: str = "",
        api_config: dict = None,
        max_requests_per_minute=60,
        request_window=10,
        client_name="Local",
    ):
        super().__init__(model=model, api_config=api_config, max_requests_per_minute=max_requests_per_minute, request_window=request_window, client_name=client_name)
        self.client_name = client_name

        # 从配置文件读取本地模型的 base_url 和 api_key
        # Read the local model's base_url and api_key from the config file
        assert "LOCAL_BASE_URL" in api_config and api_config["LOCAL_BASE_URL"] != "", "LOCAL_BASE_URL must be set in api_config.json"
        assert "LOCAL_API_KEY" in api_config and api_config["LOCAL_API_KEY"] != "", "LOCAL_API_KEY must be set in api_config.json"
        
        self.client = openai.OpenAI(
            base_url=api_config["LOCAL_BASE_URL"],
            api_key=api_config["LOCAL_API_KEY"],
        )
        self.name_mapping = name_mapping

        # Local servers may be reasoning models (e.g. k2moe) that return the
        # chain-of-thought in a `reasoning_content`/`reasoning` field. Capture it
        # so it is persisted (wrapped in <think_fast>) rather than discarded.
        # Capture the reasoning trace by default (for thinking-vs-answer work).
        # Set LOCAL_CAPTURE_REASONING=0 to store the final answer only — used for
        # runs that must match the original final-answer-only outputs_full_200.
        self.capture_reasoning = os.environ.get("LOCAL_CAPTURE_REASONING", "1") != "0"

    # Fields a reasoning-model server may require on prior assistant turns.
    _REASONING_FIELDS = ("think", "reasoning", "reasoning_content", "think_fast", "think_faster")

    def _call(self, messages, **kwargs):
        """Shim for reasoning-model servers (e.g. k2moe): a multi-turn input whose
        assistant turns lack a thinking/reasoning field is rejected with a 400.
        Inject an empty `reasoning_content` into such turns. No-op for single-turn
        inputs and harmless for non-reasoning local servers.
        """
        if isinstance(messages, list):
            patched = []
            for m in messages:
                if (isinstance(m, dict) and m.get("role") == "assistant"
                        and not any(k in m for k in self._REASONING_FIELDS)):
                    m = {**m, "reasoning_content": ""}
                patched.append(m)
            messages = patched
        return super()._call(messages, **kwargs)
