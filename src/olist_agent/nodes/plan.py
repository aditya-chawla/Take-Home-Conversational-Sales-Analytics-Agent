from __future__ import annotations

from typing import Any

from ..llm import invoke_json
from ..prompts import make_prompt, schema_context, sql_examples
from ..state import AgentState


def plan_node(llm: Any, db_path, state: AgentState) -> dict:
    history = [
        {"question": pair.get("question", ""), "answer": pair.get("answer", "")[:300]}
        for pair in state.get("history", [])[-3:]
    ]
    payload = invoke_json(
        llm,
        make_prompt(
            "plan",
            schema=schema_context(db_path),
            examples=sql_examples(),
            question=state.get("rewritten") or state["question"],
            history=history,
            last_query=state.get("last_query", {}),
            repair_block="",
        ),
        label="plan",
    )
    action = payload.get("action")
    if action not in {"answer", "clarify", "refuse"}:
        raise ValueError(f"Plan returned invalid action: {action!r}")
    out: dict[str, Any] = {
        "action": action,
        "reason": str(payload.get("reason", "")),
        "options": payload.get("options") if isinstance(payload.get("options"), list) else [],
        "rewritten": str(
            payload.get("standalone_question") or state.get("rewritten") or state["question"]
        ),
    }
    if action == "answer":
        sql = payload.get("sql")
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError("Plan returned action=answer but no SQL.")
        out.update({
            "sql": sql.strip(),
            "error": "",
            "assumptions": payload.get("assumptions", []),
            "pending_query": {
                "sql": sql.strip(),
                "metric": str(payload.get("metric", "")),
                "group_by": payload.get("group_by", []),
                "filters": payload.get("filters", []),
                "period": str(payload.get("period", "")),
            },
        })
    return out