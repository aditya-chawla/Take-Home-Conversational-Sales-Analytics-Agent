from __future__ import annotations

import json
import os
import re
from typing import Any

from langchain_ollama import ChatOllama

from . import config

THINKING_MODELS = ("qwen3")
CALL_LOG: list[dict[str, Any]] = []


def create_llm(model: str = config.MODEL_NAME) -> ChatOllama:
    kwargs: dict[str, Any] = dict(
        model=model,
        temperature=config.TEMPERATURE,
        num_ctx=config.NUM_CTX,
        num_predict=600,
        keep_alive="1h",
    )
    if model.lower().startswith(THINKING_MODELS):
        kwargs["reasoning"] = False
    return ChatOllama(**kwargs)


def _clean(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def _record(response: Any, label: str) -> None:
    meta = getattr(response, "response_metadata", None) or {}
    entry = {
        "label": label,
        "prompt_tokens": meta.get("prompt_eval_count"),
        "output_tokens": meta.get("eval_count"),
        "prefill_s": round(meta.get("prompt_eval_duration", 0) / 1e9, 1),
        "gen_s": round(meta.get("eval_duration", 0) / 1e9, 1),
        "load_s": round(meta.get("load_duration", 0) / 1e9, 1),
    }
    CALL_LOG.append(entry)
    if os.getenv("OLIST_DEBUG"):
        print(entry, flush=True)


def invoke_text(llm: Any, prompt: str, label: str = "text", json_mode: bool = False) -> str:
    try:
        response = llm.invoke(prompt, format="json") if json_mode else llm.invoke(prompt)
    except TypeError:
        response = llm.invoke(prompt)
    _record(response, label)
    content = getattr(response, "content", response)
    if isinstance(content, list):
        content = "".join(
            str(part.get("text", "")) if isinstance(part, dict) else str(part) for part in content
        )
    return _clean(str(content))


def invoke_json(llm: Any, prompt: str, retries: int = 1, label: str = "json") -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        request = prompt if attempt == 0 else (
            prompt + "\nReturn valid JSON only. Previous response was invalid: " + str(last_error)
        )
        text = invoke_text(llm, request, label=label, json_mode=True)
        text = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text, flags=re.I)
        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("Expected a JSON object.")
            return parsed
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
    raise ValueError(f"Model did not return valid JSON after {retries + 1} attempts: {last_error}")