# evals

A 23-question test set, a runner that sends each question through the real agent, and the saved results.

## Files

| File | What it is |
|---|---|
| `questions.yaml` | The test cases. |
| `run_eval.py` | The runner. |
| `results/` | One `.json` and one `.md` per run, named by the `--tag` you gave. |

## Test case format

```yaml
- id: yearly_revenue
  category: aggregation          # aggregation, multi_turn, ambiguity, refusal, data_trap
  turns: ["What was item revenue by purchase year?"]   # several entries = a conversation
  expected_action: answer        # answer, clarify, or refuse
  gold_sql: >-                   # reference query for answerable questions
    SELECT ...
  must_contain: ["2018"]         # optional: terms the generated SQL must include
  heldout: true                  # optional: not to be tuned on
  notes: why this case exists
```

## How a case is scored

- **Clarify and refuse cases** pass if the agent's action matches. No SQL is checked.
- **Answer cases with `gold_sql`** run the reference query and compare it with the agent's result. The comparison is column-wise, so aliases and extra columns don't matter, and numbers are rounded to two decimals. A gold result larger than the 200-row cap is reported as a problem with the case, not the agent.
- **Answer cases with only `must_contain`** (open-ended multi-turn questions) pass if the agent returned rows and its SQL contains every listed term.
- A case that returns no rows fails with the agent's error, if there was one.

## Running

```powershell
python -m olist_agent.evals.run_eval --tag my_run                  # all cases
python -m olist_agent.evals.run_eval --only yearly_revenue --tag t # selected cases
```

Results are saved after every case, so an interrupted run keeps what it finished. Each result records the generated SQL, the rows, the number of repairs across all turns, the latency, and the time spent reading prompts. A full run takes roughly 10 to 15 minutes on a CPU-only laptop.

## Reading a result

`results/<tag>.md` has the overall score, the score per category, and a list of failures with the generated SQL. `<tag>.json` has everything, including per-call token counts. Compare two runs by looking at the same case IDs in both files.
