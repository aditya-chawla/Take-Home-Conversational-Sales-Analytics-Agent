# Agent development notes

- Keep model inference local through Ollama; never add hosted inference dependencies.
- Keep graph behavior explicit and bounded; do not introduce a prebuilt SQL agent/toolkit.
- Never commit `data/`, SQLite databases, traces, or generated evaluation output.
- Derive schema, states, categories, and date bounds from the current database.
- Run `PYTHONPATH=src pytest` after changes and report data-dependent checks honestly.
