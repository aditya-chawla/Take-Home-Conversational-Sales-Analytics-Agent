from __future__ import annotations

from ..state import AgentState


def failure_node(state: AgentState) -> dict:
    error = state.get("error") or "The query could not be completed."
    result = state.get("result")
    details = ""
    if result:
        details = (
            f"\n\nSQL:\n```sql\n{state.get('sql', '')}\n```\n"
            f"Rows returned: {result.get('row_count', 0)}"
        )
    elif state.get("sql"):
        details = f"\n\nLast attempted SQL:\n```sql\n{state['sql']}\n```"
    return {"answer": f"I couldn't answer this reliably after {state.get('retries', 0)} repair attempts: {error}{details}"}
