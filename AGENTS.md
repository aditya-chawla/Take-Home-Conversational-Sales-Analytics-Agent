# Notes for anyone changing this code

This file is for contributors and for AI coding assistants. It records the rules the project depends on and the mistakes already made.

## Rules

- Inference stays local. Do not add hosted-model dependencies.
- Keep the flow as explicit named steps with bounded loops. Do not replace it with a prebuilt SQL agent or toolkit; the 8B model chooses tools unreliably.
- Never commit `data/`, `*.db`, `traces/`, or scratch evaluation output.
- Derive the schema, state codes, categories, and date range from the live database. Don't hardcode values from this dataset into prompts or code.
- Fix failures with general rules (prompt, guard, or a view). Never add a question from the evaluation set to the prompt examples.

## Commands

```powershell
pip install -e .                 # once, from the repo root, venv active
pytest -q                        # a few seconds, no Ollama needed
python -m olist_agent.cli        # chat
python -m olist_agent.evals.run_eval --tag <name>
```

## Things that bit us

- **Prompt order matters for speed.** In `prompts/plan.txt`, everything that doesn't change between questions (rules, schema, examples) comes first, and everything that changes (history, question, repair block) comes last. Ollama reuses its cache only for an identical prefix. Reordering that file or adding per-question text near the top makes every question slower.
- **Always pass `--tag` to the eval.** An untagged run used to overwrite the baseline results. The default tag is now a timestamp, but keep the habit.
- **Thinking mode must stay off for Qwen3.** `llm.py` handles it. If you switch models, check that `reasoning` is only set for models that support it.
- **Last query is saved only after success.** `last_query` is updated in the execute step. Writing it earlier lets a failed query corrupt the next follow-up.
- **After any prompt change, expect one slow call** while the cache rebuilds. That's not a regression.

## Before you commit

1. `pytest -q` passes.
2. `git ls-files` shows no data files or databases.