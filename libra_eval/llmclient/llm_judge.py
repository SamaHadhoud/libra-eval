"""Drop-in replacement for LibrAI_Client that runs the evaluation judges on any
OpenAI-compatible chat model (OpenRouter / OpenAI / local server).

The hosted LibrAI Prompter endpoint (https://prompter.librai.tech) that backed
the original automated evaluation is no longer available. This client keeps the
exact same interface the pipeline relies on —
``multi_call(messages_list, post_check_function=..., num_retries=..., evaluator_name=...)``
returning one parsed JSON dict per item — but produces the judgement locally via
prompt templates in ``judge_prompts.py``.

Configuration (in config/api_config.json), with fallbacks to the NEXT_* gateway
so an existing OpenRouter key can be reused:

    "EVAL_MODEL":    "openai/gpt-5.6-terra"       # judge model (OpenRouter slug)
    "EVAL_BASE_URL": "https://openrouter.ai/api/v1"
    "EVAL_API_KEY":  "<key>"

If EVAL_* are absent, NEXT_BASE_URL/NEXT_API_KEY are used; EVAL_MODEL defaults to
"openai/gpt-5.6-terra" (upgraded from gpt-4o 2026-08 after a re-judge study:
0.93 per-task correlation / 95% item agreement, terra is the stricter judge and
~35% cheaper — see the judge-correlation study).
"""

import json
import re

from openai import OpenAI

from .base import BaseClient
from .judge_prompts import build_prompt
from libra_eval.utils.logger import logger

DEFAULT_EVAL_MODEL = "openai/gpt-5.6-terra"
DEFAULT_EVAL_BASE_URL = "https://openrouter.ai/api/v1"


class LLMJudge_Client(BaseClient):
    def __init__(
        self,
        api_config: dict,
        model: str | None = None,
        max_requests_per_minute: int = 60,
        request_window: int = 60,
    ) -> None:
        base_url = (
            api_config.get("EVAL_BASE_URL")
            or api_config.get("NEXT_BASE_URL")
            or DEFAULT_EVAL_BASE_URL
        )
        api_key = (
            api_config.get("EVAL_API_KEY")
            or api_config.get("NEXT_API_KEY")
            or api_config.get("OPENAI_API_KEY")
            or ""
        )
        model = model or api_config.get("EVAL_MODEL") or DEFAULT_EVAL_MODEL

        assert api_key != "", (
            "No judge API key found. Set EVAL_API_KEY (or NEXT_API_KEY) in "
            "config/api_config.json."
        )

        super().__init__(model, api_config, max_requests_per_minute, request_window)
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        logger.info(f"LLMJudge_Client using model={model} base_url={base_url}")

    @staticmethod
    def _parse_json(text):
        """Best-effort JSON extraction from a model reply (handles code fences)."""
        if isinstance(text, dict):
            return text
        text = (text or "").strip()
        if "```" in text:
            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if m:
                text = m.group(1)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                return json.loads(m.group(0))
            raise

    def _map_input(self, messages):
        """Normalize the eval input into the dict the prompt builders expect.

        Mirrors LibrAI_Client._call: most tasks pass a dict straight from
        _single_eval_message; a few may pass an OpenAI-style message list.
        """
        if isinstance(messages, dict):
            return messages
        if isinstance(messages, list) and messages and isinstance(messages[0], dict):
            if "role" in messages[0]:
                return {"conversation": messages}
            return messages[0]
        return {"response": str(messages)}

    def _call(self, messages, **kwargs):
        evaluator_name = kwargs.get("evaluator_name")
        assert evaluator_name is not None, "evaluator_name must be provided"
        timeout = kwargs.get("timeout") or self.api_config.get("REQUEST_TIMEOUT", 120)

        data = self._map_input(messages)
        system_prompt, user_prompt = build_prompt(evaluator_name, data)

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": self.system_role_name, "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=512,
            timeout=timeout,
        )
        content = completion.choices[0].message.content
        return self._parse_json(content)

    def _log_usage(self):
        # Token usage is not tracked for the judge client.
        pass
