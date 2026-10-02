from __future__ import annotations

from typing import Any

from ..llm import invoke_json
from ..prompts import make_prompt, schema_context
from ..state import AgentState


def repair_node(llm: Any, db_path, state: AgentState) -> dict:
    history = [
        {"question": pair.get("question", ""), "answer": pair.get("answer", "")[:300]}
        for pair in state.get("history", [])[-3:]
    ]
    payload = invoke_json(
        llm,
        make_prompt(
            "repair",
            schema=schema_context(db_path),
            question=state.get("rewritten") or state["question"],
            previous_sql=state.get("sql", ""),
            error=state.get("error", "Unknown query failure"),
            history=history,
            last_query=state.get("last_query", {}),
        ),
        label="repair",
    )
    sql = payload.get("sql")
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("Repair node returned no SQL.")
    return {
        "sql": sql.strip(),
        "pending_query": {
            "sql": sql.strip(),
            "metric": str(payload.get("metric", "")),
            "group_by": payload.get("group_by", []),
            "filters": payload.get("filters", []),
            "period": str(payload.get("period", "")),
        },
        "assumptions": payload.get("assumptions", state.get("assumptions", [])),
        "retries": state.get("retries", 0) + 1,
    }