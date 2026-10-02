# Decision log

## Project initialization

- Use the explicit LangGraph state machine instead of a ReAct SQL agent/toolkit: the local 8B model has bounded responsibilities and every query passes through validation and execution nodes.
- Use SQLite populated with pandas from local Kaggle CSVs; open it read-only at query time and skip geolocation.
- Keep model inference on-device through Ollama `qwen3:8b`, with thinking disabled and deterministic temperature.
- Keep evaluation claims data-backed: this workspace currently has no Kaggle CSVs or database, so the raw-table baseline and data-derived profile are pending; no benchmark scores are fabricated.
- SQL validation and result rendering are deterministic code paths; model-generated narrative is checked for unsupported numeric values.

## Follow-up evidence

Update this log after running `evals/run_eval.py` on the downloaded dataset. Record each reproducible baseline failure, its general-layer fix, and the before/after result. Do not tune against held-out cases.
