from __future__ import annotations

from typing import Any, TypedDict


class QueryContext(TypedDict, total=False):
    sql: str
    metric: str
    group_by: list[str]
    filters: list[str]
    period: str


class QAPair(TypedDict):
    question: str
    answer: str


class AgentState(TypedDict, total=False):
    question: str
    rewritten: str
    history: list[QAPair]
    last_query: QueryContext
    pending_query: QueryContext
    action: str
    reason: str
    options: list[str]
    sql: str
    result: dict[str, Any]
    error: str
    retries: int
    answer: str
    assumptions: list[str]
    trace: dict[str, Any]
    started_at: float
    log_start: int
    clarification: str
    turns: list[str]
    heldout: bool