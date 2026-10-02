import json
import sqlite3
from types import SimpleNamespace

from olist_agent import config
from olist_agent.graph import build_graph

COUNT_SQL = "SELECT COUNT(*) AS orders FROM orders"


def _plan_reply(**overrides):
    payload = {
        "action": "answer",
        "reason": "Supported.",
        "options": [],
        "standalone_question": "",
        "sql": COUNT_SQL,
        "metric": "orders",
        "group_by": [],
        "filters": [],
        "period": "",
        "assumptions": [],
    }
    payload.update(overrides)
    return SimpleNamespace(content=json.dumps(payload))


def _user_question(prompt: str) -> str:
    return prompt.split("User question:", 1)[1].strip()


def _make_db(tmp_path, rows=(("one",), ("two",))):
    db_path = tmp_path / "orders.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE orders (order_id TEXT)")
        connection.executemany("INSERT INTO orders VALUES (?)", list(rows))
    return db_path


class AnswerStub:
    def __init__(self):
        self.prompts = []

    def invoke(self, prompt, **kwargs):
        self.prompts.append(prompt)
        if prompt.startswith("You are a SQLite analytics assistant"):
            return _plan_reply()
        raise AssertionError(f"Unexpected model prompt: {prompt[:60]}")


def test_graph_answer_path_makes_one_model_call(tmp_path):
    model = AnswerStub()
    graph = build_graph(llm=model, db_path=_make_db(tmp_path))
    state = graph.invoke(
        {"question": "How many orders are there?"},
        {"configurable": {"thread_id": "smoke"}},
    )
    assert state["action"] == "answer"
    assert state["result"]["rows"] == [[2]]
    assert COUNT_SQL in state["answer"]
    assert "see the table below" in state["answer"]
    assert state["trace"]["rows"] == 1
    assert len(model.prompts) == 1
    assert state["last_query"]["sql"].startswith("SELECT COUNT(*)")


def test_graph_narration_runs_only_when_enabled(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "NARRATE", True)

    class NarratingStub(AnswerStub):
        def invoke(self, prompt, **kwargs):
            if prompt.startswith("Answer in concise"):
                return SimpleNamespace(content="The query returned the requested count.")
            return super().invoke(prompt, **kwargs)

    graph = build_graph(llm=NarratingStub(), db_path=_make_db(tmp_path))
    state = graph.invoke(
        {"question": "How many orders are there?"},
        {"configurable": {"thread_id": "narrate"}},
    )
    assert "The query returned the requested count." in state["answer"]


class RefusalStub:
    def invoke(self, prompt, **kwargs):
        if prompt.startswith("You are a SQLite analytics assistant"):
            return _plan_reply(
                action="refuse",
                reason="Profit cannot be calculated because costs are not present.",
                sql="",
            )
        raise AssertionError("Refusal path should not generate SQL or a narrative.")


def test_graph_refuses_unavailable_metric_without_sql(tmp_path):
    graph = build_graph(llm=RefusalStub(), db_path=_make_db(tmp_path, rows=()))
    state = graph.invoke(
        {"question": "What was our profit?"},
        {"configurable": {"thread_id": "refusal"}},
    )
    assert state["action"] == "refuse"
    assert "costs are not present" in state["answer"]
    assert state["sql"] == ""


class ClarifyStub:
    def invoke(self, prompt, **kwargs):
        if prompt.startswith("You are a SQLite analytics assistant"):
            return _plan_reply(
                action="clarify",
                reason="Best sellers can be ranked several ways.",
                options=["revenue", "order count", "review score"],
                sql="",
            )
        raise AssertionError("Clarify path should not generate SQL.")


def test_graph_asks_clarifying_question_without_sql(tmp_path):
    graph = build_graph(llm=ClarifyStub(), db_path=_make_db(tmp_path, rows=()))
    state = graph.invoke(
        {"question": "Who are our best sellers?"},
        {"configurable": {"thread_id": "clarify"}},
    )
    assert state["action"] == "clarify"
    assert state["sql"] == ""
    assert "revenue" in state["answer"].lower()


class BadJsonStub:
    def invoke(self, prompt, **kwargs):
        return SimpleNamespace(content="this is not json")


def test_graph_reports_failure_when_model_returns_invalid_json(tmp_path):
    graph = build_graph(llm=BadJsonStub(), db_path=_make_db(tmp_path))
    state = graph.invoke(
        {"question": "How many orders are there?"},
        {"configurable": {"thread_id": "badjson"}},
    )
    assert "couldn't answer" in state["answer"].lower()
    assert state.get("result", {}) == {}


class BadSqlStub:
    def invoke(self, prompt, **kwargs):
        if prompt.startswith("You are a SQLite analytics assistant"):
            return _plan_reply(sql="DROP TABLE orders")
        if prompt.startswith("Repair the SQLite"):
            return _plan_reply(sql="DROP TABLE orders")
        raise AssertionError(f"Unexpected model prompt: {prompt[:60]}")


def test_failed_query_does_not_pollute_last_query_and_keeps_data_safe(tmp_path):
    db_path = _make_db(tmp_path)
    graph = build_graph(llm=BadSqlStub(), db_path=db_path)
    state = graph.invoke(
        {"question": "Drop everything."},
        {"configurable": {"thread_id": "badsql"}},
    )
    assert "couldn't answer" in state["answer"].lower()
    assert state["retries"] == config.MAX_RETRIES
    assert not state.get("last_query")
    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 2


STANDALONE = {
    "Break that down by customer state.": "Top 5 categories by revenue in 2017 broken down by customer state",
    "Only delivered orders.": "Top 5 categories by revenue in 2017 broken down by customer state, only delivered orders",
    "Compare with 2018.": "Compare top 5 categories by revenue in 2017 and 2018 by customer state, only delivered orders",
}


class FollowupStub:
    def __init__(self):
        self.prompts = []

    def invoke(self, prompt, **kwargs):
        self.prompts.append(prompt)
        if prompt.startswith("Rewrite the newest"):
            newest = prompt.split("Newest question:", 1)[1].split("\nRecent Q/A:", 1)[0].strip()
            return SimpleNamespace(content=json.dumps(
                {"question": STANDALONE.get(newest, "Top 5 categories by revenue in 2017")}
            ))
        if prompt.startswith("You are a SQLite analytics assistant"):
            question = _user_question(prompt)
            return _plan_reply(standalone_question=STANDALONE.get(question, question))
        raise AssertionError(f"Unexpected model prompt: {prompt[:60]}")


QUESTIONS = [
    "Top 5 categories by revenue in 2017.",
    "Break that down by customer state.",
    "Only delivered orders.",
    "Compare with 2018.",
]


def _run_four_turns(graph, thread_id):
    thread = {"configurable": {"thread_id": thread_id}}
    final = None
    for question in QUESTIONS:
        final = graph.invoke({"question": question}, thread)
    assert final is not None
    return final


def test_followup_plan_prompt_carries_history_and_last_query(tmp_path):
    model = FollowupStub()
    graph = build_graph(llm=model, db_path=_make_db(tmp_path))
    final = _run_four_turns(graph, "four-turn")
    plan_prompts = [p for p in model.prompts if p.startswith("You are a SQLite analytics assistant")]
    assert len(plan_prompts) == 4
    assert not any(p.startswith("Rewrite the newest") for p in model.prompts)
    last = plan_prompts[-1]
    assert "Break that down by customer state." in last
    assert "Only delivered orders." in last
    assert COUNT_SQL in last
    assert "customer state" in final["rewritten"]
    assert "2017 and 2018" in final["rewritten"]
    assert len(final["history"]) == 3


def test_followup_with_separate_rewrite_step_enabled(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "USE_REWRITE", True)
    model = FollowupStub()
    graph = build_graph(llm=model, db_path=_make_db(tmp_path))
    final = _run_four_turns(graph, "four-turn-rewrite")
    assert "2017 and 2018" in final["rewritten"]
    assert "customer state" in final["rewritten"]
    assert "delivered orders" in final["rewritten"]
    rewrite_prompt = next(p for p in reversed(model.prompts) if p.startswith("Rewrite the newest"))
    assert "Break that down by customer state." in rewrite_prompt
    assert "Only delivered orders." in rewrite_prompt
    assert COUNT_SQL in rewrite_prompt