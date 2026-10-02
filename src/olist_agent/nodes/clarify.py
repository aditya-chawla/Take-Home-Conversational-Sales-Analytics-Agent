from __future__ import annotations

from ..state import AgentState


def clarify_node(state: AgentState) -> dict:
    reason = state.get("reason", "The request has multiple plausible interpretations.")
    options = state.get("options", [])
    suffix = f" For example: {', '.join(map(str, options[:3]))}?" if options else " Which metric or interpretation did you mean?"
    return {"answer": f"I need one clarification: {reason}{suffix}"}
