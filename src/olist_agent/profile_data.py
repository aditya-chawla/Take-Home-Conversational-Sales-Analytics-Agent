from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from . import config
from .db import readonly_uri


def profile_database(db_path: Path) -> str:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}. Run python -m olist_agent.build_db first.")
    with sqlite3.connect(readonly_uri(db_path), uri=True) as conn:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        lines = ["# Olist data profile", "", f"Database: `{db_path}`", "", "## Tables", ""]
        counts: dict[str, int] = {}
        for table in tables:
            qtable = '"' + table.replace('"', '""') + '"'
            rows = conn.execute(f"SELECT COUNT(*) FROM {qtable}").fetchone()[0]
            counts[table] = rows
            info = conn.execute(f"PRAGMA table_info({qtable})").fetchall()
            lines.extend([f"### {table} ({rows:,} rows)", "", "| Column | Type | Nulls | Null rate |",
                          "|---|---|---:|---:|"])
            for _, name, dtype, notnull, default, pk in info:
                nulls = conn.execute(
                    f"SELECT COUNT(*) FROM {qtable} WHERE \"{name.replace(chr(34), chr(34)*2)}\" IS NULL"
                ).fetchone()[0]
                rate = nulls / rows if rows else 0
                lines.append(f"| `{name}` | {dtype or 'inferred'} | {nulls:,} | {rate:.1%} |")
            lines.append("")

        lines.extend(["## Keys, joins, and data checks", ""])
        primary_keys = {
            "orders": ["order_id"],
            "customers": ["customer_id"],
            "products": ["product_id"],
            "sellers": ["seller_id"],
            "order_reviews": ["review_id"],
            "order_items": ["order_id", "order_item_id"],
            "order_payments": ["order_id", "payment_sequential"],
            "product_category_name_translation": ["product_category_name"],
        }
        for table, columns in primary_keys.items():
            if table not in tables:
                continue
            available = {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}
            if not set(columns).issubset(available):
                continue
            group = ", ".join(f'"{column}"' for column in columns)
            duplicate_groups = conn.execute(
                f'SELECT COUNT(*) FROM (SELECT {group} FROM "{table}" GROUP BY {group} HAVING COUNT(*) > 1)'
            ).fetchone()[0]
            null_key_rows = conn.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE ' + " OR ".join(f'"{c}" IS NULL' for c in columns)
            ).fetchone()[0]
            lines.append(
                f"- **{table} primary key ({', '.join(columns)}):** "
                f"{duplicate_groups:,} duplicate key groups; {null_key_rows:,} rows with a null key component"
            )

        foreign_keys = [
            ("orders", "customer_id", "customers", "customer_id"),
            ("order_items", "order_id", "orders", "order_id"),
            ("order_items", "product_id", "products", "product_id"),
            ("order_items", "seller_id", "sellers", "seller_id"),
            ("order_payments", "order_id", "orders", "order_id"),
            ("order_reviews", "order_id", "orders", "order_id"),
        ]
        for child, child_col, parent, parent_col in foreign_keys:
            if child not in tables or parent not in tables:
                continue
            child_columns = {r[1] for r in conn.execute(f'PRAGMA table_info("{child}")')}
            parent_columns = {r[1] for r in conn.execute(f'PRAGMA table_info("{parent}")')}
            if child_col not in child_columns or parent_col not in parent_columns:
                continue
            orphan_count = conn.execute(
                f'SELECT COUNT(*) FROM "{child}" c LEFT JOIN "{parent}" p '
                f'ON c."{child_col}" = p."{parent_col}" '
                f'WHERE c."{child_col}" IS NOT NULL AND p."{parent_col}" IS NULL'
            ).fetchone()[0]
            lines.append(f"- **Orphan {child}.{child_col} references to {parent}.{parent_col}:** {orphan_count:,}")

        checks = [
            ("Orders without items", "SELECT COUNT(*) FROM orders o LEFT JOIN order_items i USING(order_id) WHERE i.order_id IS NULL",
             {"orders", "order_items"}),
            ("Items total (price)", "SELECT COALESCE(SUM(price),0) FROM order_items", {"order_items"}),
            ("Payments total", "SELECT COALESCE(SUM(payment_value),0) FROM order_payments", {"order_payments"}),
            ("Missing category translations", "SELECT COUNT(*) FROM products p LEFT JOIN product_category_name_translation t USING(product_category_name) WHERE p.product_category_name IS NOT NULL AND t.product_category_name IS NULL",
             {"products", "product_category_name_translation"}),
            ("Unique customer IDs", "SELECT COUNT(DISTINCT customer_id) FROM customers", {"customers"}),
            ("Unique customer identities", "SELECT COUNT(DISTINCT customer_unique_id) FROM customers", {"customers"}),
        ]
        for label, sql, needed in checks:
            if needed.issubset(tables):
                value = conn.execute(sql).fetchone()[0]
                lines.append(f"- **{label}:** {value:,}")
        cardinalities = [
            ("orders-items", "orders", "order_items"),
            ("orders-payments", "orders", "order_payments"),
            ("orders-reviews", "orders", "order_reviews"),
        ]
        for label, parent, child in cardinalities:
            if parent in tables and child in tables:
                joined = conn.execute(
                    f'SELECT COUNT(*) FROM "{parent}" p JOIN "{child}" c USING(order_id)'
                ).fetchone()[0]
                lines.append(f"- **{label}:** {counts[parent]:,} parent rows, {counts[child]:,} child rows, {joined:,} matched join rows")
        if {"orders", "order_items"}.issubset(tables) and {"order_payments"}.issubset(tables):
            price, payment = conn.execute(
                "SELECT (SELECT SUM(price) FROM order_items), (SELECT SUM(payment_value) FROM order_payments)"
            ).fetchone()
            lines.append(f"- **Items-vs-payments total mismatch:** price={price:,.2f}, payments={payment:,.2f}, difference={payment-price:,.2f}")

        for table, column in (("orders", "order_status"), ("orders", "order_purchase_timestamp")):
            if table not in tables:
                continue
            cols = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
            if column not in cols:
                continue
            if column == "order_status":
                lines.extend(["", "## Order status distribution", ""])
                lines.extend(f"- `{status}`: {n:,}" for status, n in conn.execute(
                    f'SELECT "{column}", COUNT(*) FROM "{table}" GROUP BY 1 ORDER BY 2 DESC'
                ))
            else:
                lines.extend(["", "## Purchase date coverage", ""])
                lines.extend(f"- {year}-{month}: {n:,} orders" for year, month, n in conn.execute(
                    f'SELECT substr("{column}",1,4), substr("{column}",6,2), COUNT(*) FROM "{table}" WHERE "{column}" IS NOT NULL GROUP BY 1,2 ORDER BY 1,2'
                ))
                bounds = conn.execute(f'SELECT MIN("{column}"), MAX("{column}") FROM "{table}"').fetchone()
                lines.append(f"- **Date range:** {bounds[0]} through {bounds[1]}")
        if "products" in tables and "product_category_name_translation" in tables:
            lines.extend(["", "## Category translation coverage", ""])
            lines.append(f"- Missing translations: {conn.execute('SELECT COUNT(*) FROM products p LEFT JOIN product_category_name_translation t USING(product_category_name) WHERE p.product_category_name IS NOT NULL AND t.product_category_name IS NULL').fetchone()[0]:,}")
    return "\n".join(lines) + "\n"


def main() -> None:
    db_path = Path(os.environ.get("OLIST_DB_PATH", config.DB_PATH))
    report = profile_database(db_path)
    output = Path("docs/data_profile.md")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report)
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
