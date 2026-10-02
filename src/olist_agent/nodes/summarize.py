from __future__ import annotations

import json
import re
from typing import Any

from .. import config
from ..llm import invoke_text
from ..prompts import make_prompt
from ..state import AgentState


def _result_numbers(result: dict) -> set[str]:
    found: set[str] = set()
    for row in result.get("rows", []):
        for value in row:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                found.add(str(value))
                found.add(f"{value:g}")
                found.add(f"{value:,.2f}" if isinstance(value, float) else f"{value:,}")
    return found


def unsupported_numbers(text: str, result: dict) -> list[str]:
    allowed = _result_numbers(result)
    numbers = re.findall(r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?%?", text)
    normalized = {n.rstrip("%").replace(",", "") for n in allowed}
    return [n for n in numbers if n.rstrip("%").replace(",", "") not in normalized]


def build_assumptions(state: AgentState) -> list[str]:
    parts = [str(a) for a in (state.get("assumptions") or [])] if isinstance(
        state.get("assumptions"), list) else [str(state.get("assumptions"))]
    sql = state.get("sql", "")
    sql_lower = sql.lower()
    question_lower = (state.get("rewritten") or state.get("question", "")).lower()
    context = state.get("last_query", {})
    metric_lower = str(context.get("metric", "")).lower()
    if "revenue" in metric_lower or "revenue" in question_lower or re.search(r"sum\s*\([^)]*price", sql_lower):
        parts.append("Revenue is SUM(order_items.price); freight is excluded.")
    status_filter = re.search(
        r"(?:where|and)\s+(?:\w+\.)?order_status\s*=\s*['\"]([^'\"]+)['\"]", sql, flags=re.I)
    if status_filter:
        parts.append(f"Status filter: order_status = '{status_filter.group(1)}'.")
    else:
        parts.append("Status filter: none (all statuses).")
    if "count(distinct" in sql_lower and "order_id" in sql_lower:
        parts.append("Orders are counted as COUNT(DISTINCT order_id).")
    if "customer_unique_id" in sql_lower:
        parts.append("Customers are counted as DISTINCT customer_unique_id.")
    if "order_delivered_customer_date" in sql_lower and "order_purchase_timestamp" in sql_lower:
        parts.append("Time anchor: elapsed between purchase and customer delivery timestamps.")
    elif "order_delivered_customer_date" in sql_lower:
        parts.append("Time anchor: customer delivery timestamp.")
    elif "order_purchase_timestamp" in sql_lower:
        parts.append("Time anchor: order_purchase_timestamp.")
    elif context.get("period"):
        parts.append(f"Time period: {context['period']}.")
    if any(t in question_lower for t in ("recent", "latest", "last quarter", "last year")):
        parts.append("Recent/latest periods are anchored to MAX(order_purchase_timestamp) in the database.")
    if "order_purchase_timestamp" in sql_lower:
        parts.append("Coverage caveat: the first and latest periods may be partial.")
    return parts


def summarize_node(llm: Any, state: AgentState) -> dict:
    result = state.get("result", {"columns": [], "rows": [], "row_count": 0})
    number_warning = ""
    if config.NARRATE:
        narration = invoke_text(llm, make_prompt(
            "summarize",
            question=state.get("rewritten") or state["question"],
            result=json.dumps(result, ensure_ascii=False, default=str),
            assumptions=json.dumps(state.get("assumptions", []), ensure_ascii=False),
        ), label="summarize")
        if unsupported_numbers(narration, result):
            narration = (
                "I omitted the generated narrative because it contained numeric claims not "
                "traceable to the returned rows. See the result table."
            )
            number_warning = "\n\nNumber-check: ungrounded numeric claims were detected and omitted."
    else:
        narration = f"The query returned {result.get('row_count', 0)} row(s); see the table below."
    assumption_text = "; ".join(p for p in build_assumptions(state) if p) or "No additional assumptions."
    answer = (
        f"{narration}\n\nAssumptions: {assumption_text}"
        + number_warning
        + f"\n\nSQL:\n```sql\n{state.get('sql', '')}\n```\n"
        + f"Rows returned: {result.get('row_count', 0)}"
    )
    return {"answer": answer}