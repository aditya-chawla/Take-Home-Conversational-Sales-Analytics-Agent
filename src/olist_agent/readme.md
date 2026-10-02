# olist_agent

## How a question flows through the code

1. `cli.py` reads what you typed and hands it to the graph.
2. `graph.py` runs the steps in order. It decides which step comes next, retries on errors, and keeps each conversation's state.
3. The steps live in `nodes/`. They call the model through `llm.py`, check SQL with `guard.py`, and run it with `db.py`.
4. The answer comes back to `cli.py`, which prints the text and the result table, and appends a line to the session log.

## Files

| File | What it does |
|---|---|
| `config.py` | Settings in one place: model name (`qwen3:8b`), database and log paths, number of repair tries, query timeout and context size. |
| `build_db.py` | Reads the Olist CSVs from `data/` and writes `data/olist.db`. Converts timestamps to ISO text so SQLite's date functions work, and adds indexes for the common joins. It skips the geolocation file. |
| `profile_data.py` | Inspects the database and writes the data profile: row counts, key uniqueness, nulls, orphaned keys, join sizes, and mismatches between item and payment totals. Its output is `docs/data_profile.md`. |
| `db.py` | Opens the database read-only and runs a query with a time limit. Returns the column names, rows, and row count. Raises a clear error if the query fails or times out. |
| `guard.py` | Checks generated SQL before it runs, using `sqlglot`: exactly one statement, only `SELECT` or `WITH ... SELECT`, only tables that exist in the database, no attached or qualified names. Adds `LIMIT 200` if there's none |
| `llm.py` | Creates the Ollama client and wraps calls to it. Turns off thinking for models, asks for JSON output, strips any leftover reasoning text, retries once on invalid JSON, and records the token counts and timing of each call. |
| `state.py` | Defines what the graph remembers during a turn and across turns: the question, the SQL, the result, the last successful query, the last three exchanges, and the error. |
| `graph.py` | Builds the LangGraph flow. Wires the steps together, caps the repair loop, catches errors from the model so a bad reply leads to a clear failure message instead of a crash, and assembles the trace for each turn. |
| `cli.py` | The terminal chat. Handles `/sql`, `/trace`, `/reset`, and `/quit`, prints answers with `rich`, and appends each turn to `traces/session.jsonl`. |

## Subfolders

- [`nodes/`](nodes/readme.md): the individual steps of the flow.
- [`prompts/`](prompts/readme.md): the text sent to the model and the code that builds the schema section.
- [`schema/`](schema/readme.md): the hand-written description of every table and column.
- [`evals/`](evals/readme.md): the evaluation questions, the runner, and saved results.