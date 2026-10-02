from olist_agent.llm import create_llm


def test_ollama_request_disables_thinking():
    params = create_llm()._chat_params([])
    assert params["think"] is False
    assert params["options"]["temperature"] == 0
    assert params["options"]["num_ctx"] == 8192
