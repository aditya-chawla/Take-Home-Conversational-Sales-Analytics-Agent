# tests

Fast unit and smoke tests. They don't need Ollama, the Kaggle data, or a GPU, and the whole suite runs in a few seconds with `pytest -q`.

| File | What it checks |
|---|---|
| `test_db.py` | That the database builder loads CSV files into SQLite correctly, and that the executor is read-only and enforces the time limit. |
| `test_profile_data.py` | That the profiling script reports row counts and data-quality findings correctly on a small example database. |
| `test_guard.py` | That the SQL guard accepts a plain `SELECT` or `WITH` query and rejects multiple statements, `DROP` and other writes, unknown tables, and qualified table names, and that it adds or lowers the `LIMIT`. |
| `test_llm.py` | That the Ollama client is configured as expected. |
| `test_graph_smoke.py` | The whole flow with a fake model that returns canned JSON. It covers the normal answer path (one model call, last query saved), optional narration, refusing a missing metric, asking a clarifying question, a model that returns invalid JSON, a query that never validates (it is retried, fails cleanly, leaves the data untouched, and doesn't pollute the saved query), and a four-turn conversation, with and without the separate rewrite step. |
| `test_summarize.py` | That the default summary is built without calling the model, that unsupported numbers in an optional narration are removed, and that the assumptions listed (freight excluded, status filter, distinct counts) match the SQL. |

## Running

```powershell
pip install -e .
pytest -q
```
