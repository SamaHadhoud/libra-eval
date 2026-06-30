import os
import time
import asyncio
import openai
from .openai_client import OpenAI_Client

# K2-Think hosted API (api.k2think.ai). The server returns the chain-of-thought
# INLINE in `message.content`, formatted as:
#     <reasoning text>\n</think>\n<final answer>
# For safety scoring we evaluate ONLY the final answer (the text after the last
# </think>), which matches the documented K2-Think behaviour and keeps the
# comparison apples-to-apples with the V3 run (final-answer-only judging).


class K2Think_Client(OpenAI_Client):
    # Per-event-loop concurrency primitives (multi_call uses a fresh event loop
    # per batch, so a primitive bound to a closed loop can't be reused).
    _loop_primitives: dict = {}
    _next_slot: float = 0.0  # monotonic clock; safe to persist across loops

    def __init__(
        self,
        model: str = "MBZUAI-IFM/K2-Think-v2",
        api_config: dict = None,
        max_requests_per_minute=30,
        request_window=60,
        client_name="K2Think",
        max_concurrency=20,
    ):
        super().__init__(model=model, api_config=api_config,
                         max_requests_per_minute=max_requests_per_minute,
                         request_window=request_window, client_name=client_name)
        self.client_name = client_name
        cfg = api_config or {}
        base_url = os.environ.get("K2_BASE_URL") or cfg.get("K2_BASE_URL") or "https://api.k2think.ai/v1"
        api_key = os.environ.get("K2_API_KEY") or cfg.get("K2_API_KEY")
        assert api_key, "Set K2_API_KEY (env var or api_config.json) for the K2Think client."
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        # identity mapping: pass the model id straight through to the API
        self.name_mapping = {model: model}
        # content already contains the thinking inline; do NOT prepend it again
        self.capture_reasoning = False
        # Even-spacing pacer: the hosted API rate-limits per minute, and the base
        # limiter tracks traffic on completion (so a batch fires as one burst →
        # 429 → backoff waste). Override env K2_RPM / K2_CONCURRENCY to tune.
        self._rpm = int(os.environ.get("K2_RPM", max_requests_per_minute))
        self._max_concurrency = int(os.environ.get("K2_CONCURRENCY", max_concurrency))
        self._min_interval = 60.0 / max(self._rpm, 1)

    def _primitives(self):
        loop = asyncio.get_running_loop()
        key = id(loop)
        prims = K2Think_Client._loop_primitives.get(key)
        if prims is None:
            prims = asyncio.Semaphore(self._max_concurrency)
            K2Think_Client._loop_primitives[key] = prims
            K2Think_Client._loop_primitives[(key, "lock")] = asyncio.Lock()
        return prims, K2Think_Client._loop_primitives[(key, "lock")]

    async def _async_call(self, messages, **kwargs):
        """Bound concurrency and evenly space request *starts* so we sit just
        under the API's per-minute limit instead of bursting into 429s."""
        sem, lock = self._primitives()
        async with sem:
            async with lock:
                now = time.monotonic()
                if K2Think_Client._next_slot > now:
                    await asyncio.sleep(K2Think_Client._next_slot - now)
                K2Think_Client._next_slot = time.monotonic() + self._min_interval
            return await super()._async_call(messages, **kwargs)

    @staticmethod
    def _final_answer(text: str) -> str:
        """Return the answer after the last </think>. If there is no </think>
        marker the model answered directly (no reasoning trace) — keep as-is."""
        if not text:
            return text
        marker = "</think>"
        if marker in text:
            return text.rsplit(marker, 1)[-1].strip()
        # also handle a stray opening tag with no close
        return text.strip()

    def _call(self, messages, **kwargs):
        r = super()._call(messages, **kwargs)
        if isinstance(r, str):
            return self._final_answer(r)
        return r
