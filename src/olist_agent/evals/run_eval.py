from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any

import yaml

from .. import config
from ..db import execute_query
from ..graph import build_graph, new_thread_id
from ..llm import create_llm

EVALS_PATH = Path(__file__).with_name("questions.yaml")
RESULTS_DIR = Path(__file__).with_name("results")


def _key(value: Any) -> tuple:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return (0, round(float(value), 2), "")
    return (1, 0.0, str(value))


def _same_rows(actual: list[list[Any]], expected: list[list[Any]]) -> bool:
    if len(actual) != len(expected):
        return False
    if not expected:
        return True
    actual_cols = [sorted(map(_key, col)) for col in zip(*actual)]
    return all(sorted(map(_key, col)) in actual_cols for col in zip(*expected))


def _run_case(graph, case: dict, db_path: Path) -> dict[str, Any]:
    thread_id = new_thread_id()
    state: dict[str, Any] = {}
    error = ""
    started = time.monotonic()
    try:
        for turn in case["turns"]:
            state = graph.invoke({"question": turn}, {"configurable": {"thread_id": thread_id}})
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    expected_action = case["expected_action"]
    actual_action = state.get("action")
    generated = state.get("result", {})
    passed = not error and actual_action == expected_action
    gold_rows = None

    if passed and expected_action == "answer":
        sql_lower = state.get("sql", "").lower()
        missing = [t for t in case.get("must_contain", []) if t.lower() not in sql_lower]
        if missing:
            passed, error = False, f"Generated SQL is missing expected terms: {missing}"
        elif case.get("gold_sql"):
            try:
                gold_rows = execute_query(db_path, case["gold_sql"], timeout_seconds=30)["rows"]
                if len(gold_rows) > config.MAX_ROWS:
                    passed, error = False, "Gold result exceeds MAX_ROWS; adjust the question."
                else:
                    passed = _same_rows(generated.get("rows", []), gold_rows)
            except Exception as exc:
                passed, error = False, f"Gold query failed: {exc}"
        elif not generated.get("rows"):
            passed, error = False, "No rows returned."

    trace = state.get("trace", {})
    calls = trace.get("llm_calls", [])
    return {
        "id": case["id"],
        "category": case["category"],
        "heldout": bool(case.get("heldout", False)),
        "expected_action": expected_action,
        "actual_action": actual_action,
        "passed": passed,
        "error": error or ("" if passed else state.get("error", "Action or result mismatch")),
        "sql": state.get("sql", ""),
        "rows": generated.get("rows", [])[:50],
        "gold_rows": gold_rows[:50] if gold_rows else gold_rows,
        "latency_seconds": round(time.monotonic() - started, 3),
        "retries": state.get("retries", 0),
        "llm_calls": calls,
        "prefill_seconds": round(sum(c.get("prefill_s", 0) for c in calls), 1),
    }


def _write_outputs(results: list[dict], model: str, tag: str, started: float) -> tuple[Path, Path]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    n = len(results)
    passed = sum(r["passed"] for r in results)
    summary = {
        "tag": tag,
        "model": model,
        "count": n,
        "passed": passed,
        "accuracy": passed / n if n else 0,
        "heldout_count": sum(r["heldout"] for r in results),
        "heldout_passed": sum(r["heldout"] and r["passed"] for r in results),
        "mean_latency_seconds": statistics.mean(r["latency_seconds"] for r in results) if n else 0,
        "total_elapsed_seconds": round(time.monotonic() - started, 3),
        "mean_retries": statistics.mean(r["retries"] for r in results) if n else 0,
        "results": results,
    }
    json_path = RESULTS_DIR / f"{tag}.json"
    md_path = RESULTS_DIR / f"{tag}.md"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    lines = [
        f"# Evaluation: {tag}", "",
        f"- Model: `{model}`",
        f"- Overall: {passed}/{n} ({summary['accuracy']:.1%})",
        f"- Held out: {summary['heldout_passed']}/{summary['heldout_count']}",
        f"- Mean latency: {summary['mean_latency_seconds']:.1f}s",
        f"- Total elapsed: {summary['total_elapsed_seconds']:.1f}s",
        f"- Mean retries: {summary['mean_retries']:.2f}", "",
        "| Category | Passed | Total | Accuracy |", "|---|---:|---:|---:|",
    ]
    for category in sorted({r["category"] for r in results}):
        chosen = [r for r in results if r["category"] == category]
        ok = sum(r["passed"] for r in chosen)
        lines.append(f"| {category} | {ok} | {len(chosen)} | {ok / len(chosen):.1%} |")
    lines.extend(["", "## Failures", ""])
    failures = [r for r in results if not r["passed"]]
    if failures:
        for r in failures:
            lines.extend([
                f"### {r['id']}",
                f"- Expected/actual action: {r['expected_action']} / {r['actual_action']}",
                f"- Error: {r['error']}",
                f"- Generated SQL: `{r['sql']}`", "",
            ])
    else:
        lines.append("No failures.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def run_evaluation(model: str, tag: str, db_path: Path, only: set[str] | None = None) -> tuple[Path, Path]:
    cases = yaml.safe_load(EVALS_PATH.read_text(encoding="utf-8"))
    if only:
        cases = [c for c in cases if c["id"] in only]
    graph = build_graph(llm=create_llm(model), db_path=db_path)
    results: list[dict[str, Any]] = []
    started = time.monotonic()
    paths = (RESULTS_DIR / f"{tag}.json", RESULTS_DIR / f"{tag}.md")
    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] START {case['id']} ({case['category']})", flush=True)
        result = _run_case(graph, case, db_path)
        results.append(result)
        paths = _write_outputs(results, model, tag, started)
        print(
            f"[{index}/{len(cases)}] {'PASS' if result['passed'] else 'FAIL'} {case['id']} | "
            f"{result['latency_seconds']:.1f}s | prefill={result['prefill_seconds']}s | "
            f"retries={result['retries']} | suite_elapsed={time.monotonic() - started:.1f}s",
            flush=True,
        )
        if not result["passed"]:
            print(f"    error: {result['error']}\n    sql: {result['sql']}", flush=True)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the local Olist analytics graph")
    parser.add_argument("--model", default=config.MODEL_NAME)
    parser.add_argument("--tag", default="baseline_raw_tables")
    parser.add_argument("--db", type=Path, default=config.DB_PATH)
    parser.add_argument("--only", default="", help="Comma-separated case ids")
    args = parser.parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()} or None
    json_path, md_path = run_evaluation(args.model, args.tag, args.db, only)
    print(f"Saved evaluation outputs: {json_path} and {md_path}", flush=True)


if __name__ == "__main__":
    main()