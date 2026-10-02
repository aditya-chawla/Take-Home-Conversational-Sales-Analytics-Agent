from types import SimpleNamespace

from olist_agent import config
from olist_agent.nodes.summarize import build_assumptions, summarize_node, unsupported_numbers


class NarrativeStub:
    def invoke(self, prompt, **kwargs):
        return SimpleNamespace(content="Revenue was 900 BRL.")


class ForbiddenLLM:
    def invoke(self, prompt, **kwargs):
        raise AssertionError("The model must not be called when NARRATE is off.")


def _state(result):
    return {
        "question": "What was revenue?",
        "rewritten": "What was revenue?",
        "result": result,
        "sql": "SELECT SUM(price) AS revenue FROM order_items LIMIT 200",
        "last_query": {"metric": "revenue", "filters": [], "period": ""},
        "assumptions": [],
    }


def test_unsupported_narrative_number_is_flagged_and_omitted(monkeypatch):
    monkeypatch.setattr(config, "NARRATE", True)
    result = {"columns": ["revenue"], "rows": [[100.0]], "row_count": 1}
    output = summarize_node(NarrativeStub(), _state(result))["answer"]
    assert "900 BRL" not in output
    assert "ungrounded numeric claims were detected and omitted" in output
    assert "SUM(price)" in output
    assert "Rows returned: 1" in output
    assert unsupported_numbers("The value was 100.", result) == []


def test_default_summary_is_deterministic_and_skips_the_model(monkeypatch):
    monkeypatch.setattr(config, "NARRATE", False)
    result = {"columns": ["revenue"], "rows": [[100.0]], "row_count": 1}
    output = summarize_node(ForbiddenLLM(), _state(result))["answer"]
    assert "1 row(s)" in output
    assert "Assumptions:" in output
    assert "SUM(price)" in output
    assert "Rows returned: 1" in output


def test_build_assumptions_reports_revenue_and_status_defaults():
    result = {"columns": ["revenue"], "rows": [[100.0]], "row_count": 1}
    assumptions = " ".join(build_assumptions(_state(result)))
    assert "freight is excluded" in assumptions
    assert "Status filter: none" in assumptions


def test_build_assumptions_reports_explicit_status_filter():
    state = _state({"columns": [], "rows": [], "row_count": 0})
    state["sql"] = "SELECT COUNT(DISTINCT order_id) FROM orders WHERE order_status = 'delivered'"
    assumptions = " ".join(build_assumptions(state))
    assert "order_status = 'delivered'" in assumptions
    assert "COUNT(DISTINCT order_id)" in assumptions