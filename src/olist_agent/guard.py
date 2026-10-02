from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from .db import readonly_uri


@dataclass
class ValidationResult:
    sql: str
    tables: set[str]
    limit_injected: bool


class SQLValidationError(ValueError):
    pass


def get_tables(db_path: str | Path) -> set[str]:
    with sqlite3.connect(readonly_uri(Path(db_path)), uri=True) as connection:
        return {
            row[0].lower()
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }


def validate_sql(sql: str, allowed_tables: set[str], max_rows: int = 200) -> ValidationResult:
    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except ParseError as exc:
        raise SQLValidationError(f"SQL could not be parsed: {exc}") from exc
    if len(statements) != 1 or statements[0] is None:
        raise SQLValidationError("Exactly one SQL statement is allowed.")
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.With)):
        raise SQLValidationError("Only SELECT or WITH ... SELECT queries are allowed.")
    if not tree.find(exp.Select):
        raise SQLValidationError("WITH queries must end in a SELECT.")

    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    tables: set[str] = set()
    for table in tree.find_all(exp.Table):
        if table.this is None or not isinstance(table.this, exp.Identifier):
            raise SQLValidationError("Table-valued functions are not allowed.")
        name = table.name.lower()
        if name in cte_names:
            continue
        if table.db or table.catalog:
            raise SQLValidationError("Qualified or attached-database table names are not allowed.")
        if name not in {t.lower() for t in allowed_tables}:
            raise SQLValidationError(f"Table '{table.name}' is not in the query allowlist.")
        tables.add(name)
    if not tables:
        raise SQLValidationError("Query must read at least one allowlisted table.")

    injected = False
    limit = tree.args.get("limit")
    if limit is None:
        tree = tree.limit(max_rows)
        injected = True
    else:
        try:
            requested = int(limit.expression.this)
        except (AttributeError, TypeError, ValueError):
            raise SQLValidationError("LIMIT must be a non-negative integer literal.")
        if requested < 0:
            raise SQLValidationError("LIMIT must be non-negative.")
        if requested > max_rows:
            tree.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
    return ValidationResult(tree.sql(dialect="sqlite"), tables, injected)
