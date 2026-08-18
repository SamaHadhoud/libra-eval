import time
import traceback
from openai import OpenAI
from .base import MODEL_LIST, BaseClient
from libra_eval.utils.logger import logger

models = list(filter(lambda x: x.startswith("gpt") or x.startswith("o"), MODEL_LIST))
name_mapping = {i:i for i in models}
_warned_unmapped = set()   # models we've already noted as not-in-name_mapping (log once)

_SAFETY_BLOCK_REFUSAL = ("[PROVIDER_SAFETY_BLOCK] The provider's safety filter blocked "
                         "this response, so the model produced no answer (treated as a refusal).")


def _merge_trailing_assistant(messages):
    """Some providers (e.g. Gemini/Google) reject a request whose last message is
    an assistant turn ('Requests ending with a model turn are not supported').
    Fold any trailing assistant turn(s) into the preceding user turn so the
    request ends on a user turn while preserving the prefill text as context.
    Applied only reactively on that specific error, so providers that DO support
    assistant-final prompts (local vLLM, k2think) are unaffected."""
    msgs = [dict(m) for m in messages]
    trailing = []
    while msgs and msgs[-1].get("role") == "assistant":
        trailing.insert(0, msgs.pop())
    if not trailing:
        return msgs
    add = "\n".join(m.get("content", "") for m in trailing if m.get("content"))
    if msgs and msgs[-1].get("role") == "user":
        merged = (msgs[-1].get("content", "") + ("\n" + add if add else "")).strip()
        msgs[-1] = {**msgs[-1], "content": merged}
    else:
        msgs.append({"role": "user", "content": add})
    return msgs


class OpenAI_Client(BaseClient):
    def __init__(
        self,
        model: str = "gpt-4-turbo",
        api_config: dict = None,
        max_requests_per_minute=200,
        request_window=60,
        for_eval=False, # Separate key for evaluator
        client_name="OpenAI",
    ):
        super().__init__(model, api_config, max_requests_per_minute, request_window)
        self.client_name = client_name
        if self.client_name == "OpenAI":
            assert self.api_config["OPENAI_API_KEY"] != ""
            api_key_name = "OPENAI_API_KEY" if not for_eval or "OPENAI_API_KEY_FOR_EVAL" not in self.api_config else "OPENAI_API_KEY_FOR_EVAL"
            self.client = OpenAI(api_key=self.api_config[api_key_name])
            self.name_mapping = name_mapping

    def _call(self, messages: str, **kwargs):
        if "seed" not in kwargs:
            kwargs["seed"] = 42  # default seed is 42

        # Per-request timeout and retry count, configurable via api_config
        # (REQUEST_TIMEOUT / REQUEST_NUM_RETRIES). Defaults are generous so slow
        # backends (e.g. a local model server on long prompts) don't get cut off
        # at 60s and fail the task.
        cfg = self.api_config or {}
        if "timeout" not in kwargs:
            kwargs["timeout"] = cfg.get("REQUEST_TIMEOUT", 120)

        # Convert system role to developer if needed
        if self.system_role_name == "developer":
            for msg in messages:
                if msg["role"] == "system":
                    msg["role"] = "developer"

        num_retries = kwargs.pop("num_retries", None)
        if num_retries is None:
            num_retries = cfg.get("REQUEST_NUM_RETRIES", 3)
        post_check_function = kwargs.pop("post_check_function", None)

        r = ""
        msgs_fixed = False   # whether we've already applied the model-turn workaround

        for i in range(num_retries):
            try:
                if self.model in self.name_mapping:
                    model_name = self.name_mapping[self.model]
                else:
                    # Not in the static alias table (normal for local vLLM served
                    # ids and OpenRouter slugs): use the id verbatim. Log once at
                    # debug so it doesn't spam the log on every request.
                    if self.model not in _warned_unmapped:
                        _warned_unmapped.add(self.model)
                        logger.debug(f"Model {self.model} not in name_mapping; using it verbatim.")
                    model_name = self.model
                # Non-standard OpenRouter params (e.g. `reasoning` to bound a
                # reasoning model's thinking budget so it leaves room for the
                # final answer) must go through extra_body, not as top-level
                # kwargs the OpenAI SDK would reject.
                call_kwargs = dict(kwargs)
                extra_body = call_kwargs.pop("extra_body", {}) or {}
                if "reasoning" in call_kwargs:
                    extra_body["reasoning"] = call_kwargs.pop("reasoning")
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    **call_kwargs,
                    **({"extra_body": extra_body} if extra_body else {}),
                )
                if "stream" in kwargs and kwargs["stream"]:
                    r = ""
                    for chunk in response:
                        if chunk.choices[0].delta.content is not None:
                            r += chunk.choices[0].delta.content
                else:
                    # Read the response defensively — a malformed 200 (choices or
                    # message = None, e.g. Gemini/Google under load) must not crash
                    # with "'NoneType' object is not subscriptable".
                    choices = getattr(response, "choices", None) or []
                    choice = choices[0] if choices else None
                    msg = getattr(choice, "message", None) if choice is not None else None
                    r = (msg.content or "") if msg is not None else ""
                    # Treat as a provider safety refusal ONLY with positive evidence
                    # (finish_reason=content_filter / native PROHIBITED/SAFETY/BLOCK).
                    # Never infer a refusal from a bare empty/None response — that
                    # would fabricate a "safe" score from an ambiguous failure. An
                    # unexplained empty falls through to the normal empty-response
                    # path (retry/drop), i.e. honest missing data, not a fake refusal.
                    fr = getattr(choice, "finish_reason", None) if choice is not None else None
                    native = str(getattr(choice, "native_finish_reason", "") or "") if choice is not None else ""
                    blocked = (fr == "content_filter") or ("PROHIBITED" in native.upper()) \
                        or ("SAFETY" in native.upper()) or ("BLOCK" in native.upper())
                    if blocked and not r.strip():
                        r = _SAFETY_BLOCK_REFUSAL
                    # Reasoning-model capture: some servers (e.g. k2moe) return the
                    # chain-of-thought in a separate `reasoning_content`/`reasoning`
                    # field that is otherwise discarded. When enabled, prepend it
                    # wrapped in <think_fast> tags so downstream thinking-vs-answer
                    # tooling (batch_harmful_check.py) can separate them. Off by
                    # default, so non-reasoning clients are unaffected.
                    if getattr(self, "capture_reasoning", False):
                        reasoning = getattr(msg, "reasoning_content", None) or getattr(msg, "reasoning", None)
                        if not reasoning:
                            # OpenRouter reasoning models (e.g. Gemini) may expose the
                            # trace only in a structured `reasoning_details` list; join
                            # its text parts as a fallback so the trace is still stored.
                            details = (getattr(msg, "model_extra", None) or {}).get("reasoning_details")
                            if isinstance(details, list):
                                reasoning = "\n".join(
                                    p.get("text", "") for p in details
                                    if isinstance(p, dict) and p.get("text"))
                        if reasoning:
                            r = f"<think_fast>{reasoning}</think_fast>\n{r}"
                if post_check_function is None:
                    break
                else:
                    post_r = post_check_function(r)
                    if post_r:
                        return post_r
                    else:
                        logger.warning(f"Warning: Post check function failed. Response is {r}. Retrying {i} ...")
            except Exception as e:
                logger.error(f"Error in LLM Client (attempt {i+1}/{num_retries}): {e}")
                logger.debug(traceback.format_exc())  # full stack trace at debug level
                # Provider rejects an assistant-final prompt (Gemini/Google:
                # "Requests ending with a model turn are not supported"). Fold the
                # trailing assistant turn into the user turn and retry immediately.
                if (not msgs_fixed) and isinstance(messages, list) and \
                        ("model turn" in str(e).lower()):
                    messages = _merge_trailing_assistant(messages)
                    msgs_fixed = True
                    continue
                if i < num_retries - 1:
                    time.sleep(min(2 ** i, 10))  # exponential backoff, capped at 10s

        if r == "":
            logger.warning(f"{self.client_name} Client Warning: Empty response from LLM Client call.")

        return r

    def _log_usage(self, usage_dict):
        try:
            self.usage.prompt_tokens += usage_dict.prompt_tokens
            self.usage.completion_tokens += usage_dict.completion_tokens
        except:  # noqa E722
            logger.warning("Warning: prompt_tokens or completion_token not found in usage_dict")


    def construct_message_list(
        self,
        prompt_list: list[str],
        system_role: str = "You are a helpful assistant designed to output JSON.",
        no_system_role: bool = False,
    ):
        messages_list = list()
        for prompt in prompt_list:
            if no_system_role:
                messages = [
                    {"role": "user", "content": prompt},
                ]
            else:
                messages = [
                    {"role": self.system_role_name, "content": system_role},
                    {"role": "user", "content": prompt},
                ]
            messages_list.append(messages)
        return messages_list
