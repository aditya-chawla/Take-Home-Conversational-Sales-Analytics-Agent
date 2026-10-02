# Conversational Sales Analytics Agent

A local terminal agent for analytics on the Olist Brazilian E-Commerce dataset. It uses Ollama (`qwen3:8b`), SQLite, LangGraph, and `sqlglot`; no hosted LLM API is used at runtime. The database is created locally from CSV files and is opened read-only for questions.

## Prerequisites

- Python 3.11 or newer
- [Ollama](https://ollama.com/) installed and running
- Kaggle CLI configured with access to `olistbr/brazilian-ecommerce`

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull qwen3:8b
```

Download the source files from the project root:

```powershell
kaggle datasets download -d olistbr/brazilian-ecommerce -p data --unzip
```

Alternatively, run `scripts/download_data.sh` in a shell with the Kaggle CLI installed. The downloaded data and generated database are intentionally excluded from version control.

Build the database and inspect the data profile:

```powershell
$env:PYTHONPATH = "src"
python -m olist_agent.build_db
python -m olist_agent.profile_data
```

The builder loads every recognized Olist CSV except geolocation into `data/olist.db`, converting timestamps to ISO strings and creating common join/date indexes. Re-running it replaces the database. Review `docs/data_profile.md` and `assumptions.md` before relying on results from a new dataset variant.

## Run

From the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m olist_agent.cli
```

Optional settings are in `src/olist_agent/config.py`. The interactive commands are `/sql`, `/reset`, `/trace`, and `/quit`. Each answer includes the executed SQL, returned row count, and applicable metric assumptions. Query access is read-only and capped at 200 rows.

## Tests and evaluation

```powershell
$env:PYTHONPATH = "src"
pytest
python -m olist_agent.evals.run_eval
```

The evaluation requires the built database and a running Ollama service/model; it writes JSON and Markdown reports under `evals/results/`. Use `--model` to select a locally installed model and `--tag` to label results.

## Troubleshooting

- **No CSV files found:** unzip the Kaggle archive into `data/` or specify `OLIST_DATA_DIR`.
- **Ollama connection/model error:** start Ollama and verify `ollama list` contains `qwen3:8b`.
- **Missing database:** run `python -m olist_agent.build_db`.
- **No answer / refusal:** the agent does not infer unavailable fields (for example profit or customer names); check the schema profile and stated assumptions.
- **Expected runtime:** local 8B inference can take tens of seconds to minutes on CPU; actual latency depends on hardware and query complexity and is recorded per turn/evaluation.
- **Slow responses:** reduce question complexity and close other memory-heavy applications; inference remains local.

See [DESIGN.md](DESIGN.md) for architecture and limitations.
