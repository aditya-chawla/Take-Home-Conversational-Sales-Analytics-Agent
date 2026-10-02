from __future__ import annotations

import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from ..db import readonly_uri

PROMPT_DIR = Path(__file__).parent
DESCRIPTION_PATH = Path(__file__).parent.parent / "schema" / "column_descriptions.yaml"

EXCLUDE_TABLES = {"geolocation", "olist_geolocation_dataset"}
EXCLUDE_COLUMNS = {
    "review_comment_title", "review_comment_message", "review_creation_date",
    "review_answer_timestamp", "product_name_lenght", "product_description_lenght",
    "product_photos_qty", "product_length_cm", "product_height_cm", "product_width_cm",
    "customer_zip_code_prefix", "seller_zip_code_prefix",
}


def _template(name: str) -> str:
    return (PROMPT_DIR / f"{name}.txt").read_text(encoding="utf-8")


def make_prompt(name: str, **values: Any) -> str:
    template = _template(name)
    return re.sub(
        r"\{(\w+)\}",
        lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0),
        template,
    )


def sql_examples() -> str:
    return (PROMPT_DIR / "sql_examples.txt").read_text(encoding="utf-8")


def schema_context(db_path: Path | str) -> str:
    return _schema_context(Path(db_path))


@lru_cache(maxsize=4)
def _schema_context(db_path: Path) -> str:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}. Build it with python -m olist_agent.build_db.")
    descriptions = yaml.safe_load(DESCRIPTION_PATH.read_text(encoding="utf-8"))
    with sqlite3.connect(readonly_uri(db_path), uri=True) as conn:
        tables = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        tables = [t for t in tables if t not in EXCLUDE_TABLES]
        schema_parts: list[str] = []
        for table in tables:
            escaped = table.replace('"', '""')
            fields = conn.execute(f'PRAGMA table_info("{escaped}")').fetchall()
            described = descriptions.get("tables", {}).get(table, {})
            schema_parts.append(
                f"TABLE {table} - {described.get('description', 'No description available.')}\n"
                + "\n".join(
                    f"  {name} {kind or 'TEXT'}: {described.get('columns', {}).get(name, 'No description available.')}"
                    for _, name, kind, *_ in fields
                    if name not in EXCLUDE_COLUMNS
                )
            )
        hints: list[str] = []
        if "orders" in tables:
            cols = {r[1] for r in conn.execute('PRAGMA table_info("orders")')}
            if "order_status" in cols:
                statuses = [r[0] for r in conn.execute(
                    "SELECT DISTINCT order_status FROM orders WHERE order_status IS NOT NULL ORDER BY 1"
                )]
                hints.append("Actual order_status values: " + ", ".join(statuses))
            date_col = "order_purchase_timestamp"
            if date_col in cols:
                start, end = conn.execute(
                    f'SELECT MIN("{date_col}"), MAX("{date_col}") FROM orders'
                ).fetchone()
                hints.append(f"Actual purchase date range: {start} through {end}")
        for table, column in (("customers", "customer_state"), ("sellers", "seller_state")):
            if table in tables:
                cols = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
                if column in cols:
                    values = [r[0] for r in conn.execute(
                        f'SELECT DISTINCT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL ORDER BY 1'
                    )]
                    hints.append(f"Actual {column} values: " + ", ".join(values))
        if "products" in tables:
            product_columns = {r[1] for r in conn.execute('PRAGMA table_info("products")')}
            if "product_category_name" in product_columns:
                translated_columns: set[str] = set()
                if "product_category_name_translation" in tables:
                    translated_columns = {
                        r[1] for r in conn.execute('PRAGMA table_info("product_category_name_translation")')
                    }
                if "product_category_name_english" in translated_columns:
                    category_sql = (
                        "SELECT DISTINCT COALESCE(t.product_category_name_english, p.product_category_name) "
                        "FROM products p LEFT JOIN product_category_name_translation t "
                        "ON t.product_category_name=p.product_category_name "
                        "WHERE p.product_category_name IS NOT NULL ORDER BY 1"
                    )
                else:
                    category_sql = (
                        "SELECT DISTINCT product_category_name FROM products "
                        "WHERE product_category_name IS NOT NULL ORDER BY 1"
                    )
                categories = [r[0] for r in conn.execute(category_sql)]
                hints.append("Actual product category values: " + ", ".join(categories))
    glossary = (
        "Metric glossary: revenue=SUM(order_items.price), freight excluded; orders=COUNT(DISTINCT order_id); "
        "customers=COUNT(DISTINCT customer_unique_id). No status filter by default. "
        "For latest/recent periods anchor to MAX(order_purchase_timestamp) shown below; mention partial periods."
    )
    relationships = descriptions.get("global", {}).get("relationships", [])
    return "\n\n".join([
        descriptions.get("global", {}).get("units", ""),
        glossary,
        "SQLite schema:\n" + "\n\n".join(schema_parts),
        "Runtime values:\n" + ("\n".join(hints) if hints else "No dynamic hints available."),
        "Relationships:\n" + "\n".join(relationships),
        "SQLite rules: use SQLite date functions and strftime; timestamps are ISO text. Do not use vendor-specific SQL.",
    ])