from __future__ import annotations

from .. import config
from ..db import QueryExecutionError, execute_query
from ..state import AgentState


def execute_node(db_path, state: AgentState) -> dict:
    try:
        result = execute_query(db_path, state["sql"], config.QUERY_TIMEOUT_SECONDS)
    except QueryExecutionError as exc:
        return {"error": str(exc)}
    if result["row_count"] == 0:
        return {"result": result, "error": "Query returned zero rows."}
    last_query = {**state.get("pending_query", {}), "sql": state["sql"]}
    return {"result": result, "error": "", "last_query": last_query}