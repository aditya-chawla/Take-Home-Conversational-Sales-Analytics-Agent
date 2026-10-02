# Conversational Sales Analytics Agent

Ask questions about Olist's sales data in plain English and get answers computed from the data. Everything runs on your machine: a local Qwen3 8B model served by Ollama writes SQL, and a SQLite database built from the Kaggle CSVs runs it. Each answer shows the SQL that produced it, so every number can be checked.


It keeps context across turns ("Break that down by customer state", then "Only delivered orders"), asks one question back when a request is genuinely ambiguous ("Who are our best sellers?"), and says so when the data can't answer something (profit, customer names, years outside 2016-2018).

## What you need

- Python 3.11 or newer
- [Ollama](https://ollama.com/), installed and running
- About 8 GB of free RAM for the model (it was developed on a 16 GB laptop, CPU only)
- A free Kaggle account, to download the dataset

## Setup

These commands are for Windows PowerShell, which is where I developed and tested. On macOS or Linux, the only changes are the virtualenv activation (`source .venv/bin/activate`) and the paths; I haven't run it there.

```powershell
git clone https://github.com/aditya-chawla/Take-Home-Conversational-Sales-Analytics-Agent
cd <repo-folder>

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

ollama pull qwen3:8b
```

Download the data. The CSVs are not in the repository. With the Kaggle CLI configured:

```powershell
kaggle datasets download -d olistbr/brazilian-ecommerce -p data --unzip
```

You can also download the archive from the [dataset page](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and unzip it into a `data/` folder in the repo root. Then build the database:

```powershell
python -m olist_agent.build_db
```

This takes under a minute. It creates `data/olist.db`, and you can rerun it at any time to rebuild from scratch.

## Run it

```powershell
python -m olist_agent.cli
```

Inside the chat:

| Command | What it does |
|---|---|
| `/sql` | Shows the SQL from the last answer |
| `/trace` | Shows the most recent entries of the session log |
| `/reset` | Starts a fresh conversation (forgets earlier turns) |
| `/quit` | Exits |

Set `OLIST_DEBUG=1` before starting to print the token counts and timing of every model call.

### What to expect on speed

On a CPU-only laptop, the first question after the model loads takes one to two minutes, because the model has to read the whole schema once. After that, the schema is cached and a typical question takes 10 to 20 seconds. A follow-up turn takes longer, since the conversation context grows with each turn. A GPU makes all of this much faster.

## Tests and evaluation

```powershell
pytest -q
python -m olist_agent.evals.run_eval --tag my_run
```

`pytest` takes a few seconds and doesn't need Ollama or the dataset. The evaluation runs 23 questions through the real agent and model, and takes roughly 10 to 15 minutes on CPU. Always pass `--tag`, because results are saved under that name in `src/olist_agent/evals/results/`. Use `--only id1,id2` to run specific cases and `--model` to try another Ollama model. See [the eval README](src/olist_agent/evals/readme.md) for how scoring works.

## Where things are

| Path | What's in it |
|---|---|
| `src/olist_agent/` | The agent itself |
| `src/olist_agent/nodes/` | The steps of the LangGraph flow |
| `src/olist_agent/prompts/` | Prompt templates and the schema builder |
| `src/olist_agent/evals/` | Question set, runner and saved results |
| `tests/` | Unit and smoke tests |
| `docs/` | Architecture diagram, data profile, decision log |
| `DESIGN.md` | Architecture, decisions, results and limits |
| `assumptions.md` | How I treated the quirks in the data |

## Troubleshooting

- **`ModuleNotFoundError: olist_agent`:** run `pip install -e .` from the repo root with the virtualenv active.
- **Database not found:** run `python -m olist_agent.build_db`. It needs the CSVs in `data/`.
- **Connection or model error:** make sure Ollama is running and `ollama list` shows `qwen3:8b`.
- **Very slow first answer:** this is the one-time schema read described above. If every question is slow, check `ollama ps`: the model should stay loaded, and `OLIST_DEBUG=1` shows where the time goes.
- **The agent refused or asked a question:** that's by design when the data can't support the request or the request is ambiguous. See "Limitations" in [DESIGN.md](DESIGN.md).