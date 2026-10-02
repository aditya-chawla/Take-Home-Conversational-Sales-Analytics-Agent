from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
MODEL_NAME = "qwen3:8b"
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "olist.db"
TRACE_PATH = ROOT_DIR / "traces" / "session.jsonl"
MAX_ROWS = 200
MAX_RETRIES = 2
QUERY_TIMEOUT_SECONDS = 10
NUM_CTX = 8192
TEMPERATURE = 0
NARRATE = False
USE_REWRITE = False