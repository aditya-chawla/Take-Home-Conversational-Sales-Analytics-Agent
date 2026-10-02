# prompts

The text the model sees, plus the code that fills it in.

## Files

| File | What it is |
|---|---|
| `plan.txt` | The main prompt. It tells the model to return one JSON object, defines when to answer, clarify, or refuse, and lists the SQL rules (SQLite dialect, only requested filters, `LEFT JOIN` for lookup tables, top-N then breakdown, compare periods side by side, avoid join fan-out). It then includes the schema and examples, and finally the conversation and question for this turn. The repair step reuses this file and fills a `{repair_block}` placeholder at the end. |
| `sql_examples.txt` | Nine generic SQL patterns (revenue by year, orders by status, translated labels, top-N then breakdown, comparing two periods, and so on). They show patterns, not answers to evaluation questions, and none should be copied from the evaluation set. |
| `rewrite.txt` | Instructions for the optional rewrite step. |
| `summarize.txt` | Instructions for the optional narration, used only when `NARRATE` is on. |
| `__init__.py` | Code that loads and fills the templates. See below. |

## What `__init__.py` does

- `make_prompt(name, **values)` loads `<name>.txt` and replaces `{placeholders}` in a single pass. Placeholders the caller doesn't provide are left alone, and the JSON braces in the templates are not touched.
- `schema_context(db_path)` builds the schema section from the live database: each table's columns with the descriptions from `schema/column_descriptions.yaml`, the metric glossary, and values read from the data (order statuses, the date range, state codes, product categories). The result is cached, so it's identical on every call, which is what lets Ollama reuse its cache.
- `EXCLUDE_TABLES` and `EXCLUDE_COLUMNS` hide things the questions never need: geolocation, review comment text, product dimensions, zip prefixes.