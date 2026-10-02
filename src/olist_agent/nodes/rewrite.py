from __future__ import annotations

from typing import Any

from ..llm import invoke_json
from ..prompts import make_prompt
from ..state import AgentState


def rewrite_node(llm: Any, state: AgentState) -> dict:
    history = state.get("history", [])[-3:]
    if not history:
        return {"rewritten": state["question"]}
    compact_history = [
        {"question": pair.get("question", ""), "answer": pair.get("answer", "")[:500]}
        for pair in history
    ]
    payload = invoke_json(llm, make_prompt(
        "rewrite",
        question=state["question"],
        history=compact_history,
        last_query=state.get("last_query", {}),
    ))
    rewritten = payload.get("question")
    if not isinstance(rewritten, str) or not rewritten.strip():
        raise ValueError("Rewrite node returned no standalone question.")
    return {"rewritten": rewritten.strip()}
