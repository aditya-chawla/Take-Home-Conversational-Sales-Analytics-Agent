from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from . import config
from .graph import build_graph, new_thread_id
from .llm import create_llm


def _show_result(console: Console, result: dict) -> None:
    columns = result.get("columns", [])
    if not columns:
        return
    table = Table(*columns, title="Query result")
    for row in result.get("rows", []):
        table.add_row(*(str(value) if value is not None else "NULL" for value in row))
    console.print(table)


def _append_trace(path: Path, trace: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(trace, ensure_ascii=False, default=str) + "\n")


def run_cli(model: str = config.MODEL_NAME, db_path: Path = config.DB_PATH, trace_path: Path = config.TRACE_PATH) -> None:
    console = Console()
    graph = build_graph(llm=create_llm(model), db_path=db_path, checkpointer=MemorySaver())
    thread_id = new_thread_id()
    console.print("[bold]Olist Sales Analytics[/bold] — ask a question, or use /sql, /reset, /trace, /quit.")
    while True:
        try:
            question = console.input("[bold cyan]you> [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break
        if not question:
            continue
        command = question.lower()
        if command in {"/quit", "/exit"}:
            break
        if command == "/reset":
            thread_id = new_thread_id()
            console.print("Started a fresh conversation.")
            continue
        if command == "/sql":
            try:
                state = graph.get_state({"configurable": {"thread_id": thread_id}}).values
                sql = state.get("sql") or state.get("last_query", {}).get("sql")
                console.print(f"```sql\n{sql}\n```" if sql else "No SQL has been run in this conversation.")
            except Exception as exc:
                console.print(f"[yellow]No saved query: {exc}[/yellow]")
            continue
        if command == "/trace":
            if trace_path.exists():
                console.print(trace_path.read_text(encoding="utf-8")[-5000:])
            else:
                console.print("No trace entries yet.")
            continue
        started = time.monotonic()
        try:
            state = graph.invoke(
                {"question": question},
                {"configurable": {"thread_id": thread_id}},
            )
        except Exception as exc:
            console.print(f"[red]Agent failed visibly: {exc}[/red]")
            continue
        console.print(Markdown(state.get("answer", "The agent returned no answer.")))
        _show_result(console, state.get("result", {}))
        trace = dict(state.get("trace", {}))
        trace.setdefault("latency_seconds", round(time.monotonic() - started, 3))
        _append_trace(trace_path, trace)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Olist conversational analytics agent")
    parser.add_argument("--model", default=config.MODEL_NAME)
    parser.add_argument("--db", type=Path, default=config.DB_PATH)
    args = parser.parse_args()
    run_cli(args.model, args.db)


if __name__ == "__main__":
    main()
