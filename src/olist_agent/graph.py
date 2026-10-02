from __future__ import annotations

import time
import uuid
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from . import config
from .llm import CALL_LOG, create_llm
from .nodes.clarify import clarify_node
from .nodes.execute import execute_node
from .nodes.failure import failure_node
from .nodes.plan import plan_node
from .nodes.refuse import refuse_node
from .nodes.repair import repair_node
from .nodes.rewrite import rewrite_node
from .nodes.summarize import summarize_node
from .nodes.validate import validate_node
from .state import AgentState


def _begin(state: AgentState) -> dict:
    return {
        "started_at": time.monotonic(),
        "log_start": len(CALL_LOG),
        "rewritten": "",
        "action": "",
        "reason": "",
        "options": [],
        "sql": "",
        "pending_query": {},
        "result": {},
        "error": "",
        "retries": 0,
        "answer": "",
        "assumptions": [],
    }


def _finalize(state: AgentState) -> dict:
    history = list(state.get("history", []))
    history.append({"question": state.get("question", ""), "answer": state.get("answer", "")})
    elapsed = time.monotonic() - state.get("started_at", time.monotonic())
    trace = {
        "question": state.get("question", ""),
        "rewritten": state.get("rewritten", ""),
        "action": state.get("action", ""),
        "sql": state.get("sql", ""),
        "rows": state.get("result", {}).get("row_count", 0),
        "retries": state.get("retries", 0),
        "latency_seconds": round(elapsed, 3),
        "llm_calls": CALL_LOG[state.get("log_start", 0):],
    }
    return {"history": history[-3:], "trace": trace}


def _safe(fn):
    def run(state):
        try:
            return fn(state)
        except Exception as exc:
            return {"action": "failed", "error": f"{type(exc).__name__}: {exc}"}
    return run


def _rewrite_or_pass(model):
    def run(state):
        try:
            return rewrite_node(model, state)
        except Exception:
            return {"rewritten": state["question"]}
    return run


def _after_validation(state: AgentState) -> str:
    if state.get("error"):
        return "repair" if state.get("retries", 0) < config.MAX_RETRIES else "failure"
    return "execute"


def _after_execution(state: AgentState) -> str:
    if state.get("error"):
        return "repair" if state.get("retries", 0) < config.MAX_RETRIES else "failure"
    return "summarize"


def _after_repair(state: AgentState) -> str:
    return "failure" if state.get("action") == "failed" else "validate"


def build_graph(llm: Any | None = None, db_path=config.DB_PATH, checkpointer=None):
    model = llm or create_llm()
    workflow = StateGraph(AgentState)
    workflow.add_node("begin", _begin)
    workflow.add_node("rewrite", _rewrite_or_pass(model))
    workflow.add_node("plan", _safe(lambda state: plan_node(model, db_path, state)))
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("refuse", refuse_node)
    workflow.add_node("validate", lambda state: validate_node(db_path, state))
    workflow.add_node("execute", lambda state: execute_node(db_path, state))
    workflow.add_node("repair", _safe(lambda state: repair_node(model, db_path, state)))
    workflow.add_node("failure", failure_node)
    workflow.add_node("summarize", lambda state: summarize_node(model, state))
    workflow.add_node("finalize", _finalize)

    workflow.add_edge(START, "begin")
    if config.USE_REWRITE:
        workflow.add_edge("begin", "rewrite")
        workflow.add_edge("rewrite", "plan")
    else:
        workflow.add_edge("begin", "plan")
    workflow.add_conditional_edges("plan", lambda state: state["action"], {
        "answer": "validate", "clarify": "clarify", "refuse": "refuse", "failed": "failure",
    })
    workflow.add_edge("clarify", "finalize")
    workflow.add_edge("refuse", "finalize")
    workflow.add_conditional_edges("validate", _after_validation, {
        "execute": "execute", "repair": "repair", "failure": "failure",
    })
    workflow.add_conditional_edges("execute", _after_execution, {
        "summarize": "summarize", "repair": "repair", "failure": "failure",
    })
    workflow.add_conditional_edges("repair", _after_repair, {
        "validate": "validate", "failure": "failure",
    })
    workflow.add_edge("summarize", "finalize")
    workflow.add_edge("failure", "finalize")
    workflow.add_edge("finalize", END)
    return workflow.compile(checkpointer=checkpointer or MemorySaver())


def new_thread_id() -> str:
    return str(uuid.uuid4())