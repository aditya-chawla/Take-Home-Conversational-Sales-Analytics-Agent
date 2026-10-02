from __future__ import annotations

from .. import config
from ..guard import SQLValidationError, get_tables, validate_sql
from ..state import AgentState


def validate_node(db_path, state: AgentState) -> dict:
    try:
        validated = validate_sql(state["sql"], get_tables(str(db_path)), config.MAX_ROWS)
        return {"sql": validated.sql, "error": ""}
    except SQLValidationError as exc:
        return {"error": f"SQL validation error: {exc}"}