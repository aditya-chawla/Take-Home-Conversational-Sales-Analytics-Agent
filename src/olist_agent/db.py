from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any


class QueryExecutionError(RuntimeError):
    pass


def readonly_uri(db_path: Path) -> str:
    return f"{db_path.resolve().as_uri()}?mode=ro"


def open_readonly(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}. Run python -m olist_agent.build_db first.")
    connection = sqlite3.connect(readonly_uri(db_path), uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def execute_query(
    db_path: Path, sql: str, timeout_seconds: int = 10
) -> dict[str, Any]:
    connection = open_readonly(db_path)
    deadline = time.monotonic() + timeout_seconds
    connection.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
    try:
        cursor = connection.execute(sql)
        rows = cursor.fetchall()
        return {
            "columns": [description[0] for description in cursor.description or []],
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
        }
    except sqlite3.Error as exc:
        if "interrupted" in str(exc).lower():
            raise QueryExecutionError(f"Query exceeded the {timeout_seconds}-second time limit.") from exc
        raise QueryExecutionError(f"SQLite query failed: {exc}") from exc
    finally:
        connection.close()
