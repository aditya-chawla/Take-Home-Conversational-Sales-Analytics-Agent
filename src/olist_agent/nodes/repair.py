from __future__ import annotations

from typing import Any

from ..llm import invoke_json
from ..prompts import make_prompt, schema_context, sql_examples
from ..state import AgentState


def repair_node(llm: Any, db_path, state: AgentState) -> dict:
    history = [
        {"question": pair.get("question", ""), "answer": pair.get("answer", "")[:300]}
        for pair in state.get("history", [])[-3:]
    ]
    repair_block = (
        "\n\nYour previous SQL failed. Return the corrected JSON in the same format with action \"answer\".\n"
        f"Previous SQL: {state.get('sql', '')}\n"
        f"Problem: {state.get('error', 'Unknown query failure')}\n"
        "Fix the problem and do not repeat the same query. If the problem is zero rows, change a predicate "
        "that may not match the actual values listed in the schema."
    )
    payload = invoke_json(
        llm,
        make_prompt(
            "plan",
            schema=schema_context(db_path),
            examples=sql_examples(),
            question=state.get("rewritten") or state["question"],
            history=history,
            last_query=state.get("last_query", {}),
            repair_block=repair_block,
        ),
        label="repair",
    )
    sql = payload.get("sql")
    if payload.get("action") != "answer" or not isinstance(sql, str) or not sql.strip():
        raise ValueError("Repair did not return corrected SQL.")
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