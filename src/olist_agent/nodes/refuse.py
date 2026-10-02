from __future__ import annotations

from ..state import AgentState


def refuse_node(state: AgentState) -> dict:
    reason = state.get("reason") or "The requested analysis is not supported by the available data."
    return {"answer": f"I can't answer that from this dataset: {reason}"}
