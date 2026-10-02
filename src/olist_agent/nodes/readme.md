# nodes

Each file here is one step of the flow. A step receives the current state, does one job, and returns the pieces of state it changed. `graph.py` decides which step runs next.

## The steps

| File | Job | Next step |
|---|---|---|
| `plan.py` | The main model call. Sends the schema, examples, recent conversation, and the question, and gets JSON back: an action (`answer`, `clarify`, `refuse`), the SQL if answering, and the assumptions it made. Rejects a reply with an invalid action or an empty query. | `validate`, `clarify`, `refuse`, or `failure` |
| `rewrite.py` | Optional. Turns a follow-up like "Break that down by state" into a standalone question. Off by default (`USE_REWRITE` in `config.py`), because it adds a model call. If it errors, the original question is used. | `plan` |
| `clarify.py` | Turns the model's reason and options into one short question for the user. No SQL runs. | end of turn |
| `refuse.py` | Explains what the data can't provide (a missing metric, a period outside the data, or input that isn't a question). No SQL runs. | end of turn |
| `validate.py` | Runs the SQL through the guard in `guard.py`. Stores the cleaned SQL, or an error message. | `execute`, or `repair` on error |
| `execute.py` | Runs the SQL read-only. A SQLite error or a result with zero rows counts as a problem to repair. On success, saves this query as the "last query" that follow-ups build on. | `summarize`, or `repair` |
| `repair.py` | Sends the same prompt as `plan`, with the failed SQL and the problem appended at the end. Keeping the start identical lets Ollama reuse its cache, so a retry is cheap. Counts the attempt. | `validate`, or `failure` |
| `summarize.py` | Builds the final answer: a short line, the assumptions that applied (revenue excludes freight, no status filter, which date was used), the SQL, and the row count. If `NARRATE` is on, the model also writes a sentence, and any number in it that isn't in the result rows is removed. | end of turn |
| `failure.py` | After two failed repairs, or an unusable model reply, says plainly that it couldn't answer, gives the error, and shows the last SQL it tried. | end of turn |
