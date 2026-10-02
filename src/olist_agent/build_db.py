from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd

from . import config

SKIP_STEMS = {"olist_geolocation_dataset", "geolocation"}
REVIEW_TEXT_COLUMNS = {"review_comment_title", "review_comment_message"}
INDEXES = {
    "orders": [
        ("idx_orders_customer_id", "customer_id"),
        ("idx_orders_status", "order_status"),
        ("idx_orders_purchase_ts", "order_purchase_timestamp"),
    ],
    "order_items": [
        ("idx_items_order_id", "order_id"),
        ("idx_items_product_id", "product_id"),
        ("idx_items_seller_id", "seller_id"),
    ],
    "order_payments": [("idx_payments_order_id", "order_id")],
    "order_reviews": [("idx_reviews_order_id", "order_id")],
    "customers": [("idx_customers_customer_id", "customer_id")],
    "products": [("idx_products_category", "product_category_name")],
}


def _table_name(path: Path) -> str:
    stem = path.stem.lower()
    stem = stem.removesuffix("_dataset")
    return stem.removeprefix("olist_")


def build_database(data_dir: Path, db_path: Path) -> list[str]:
    csv_files = sorted(
        p for p in data_dir.glob("*.csv")
        if p.stem.lower() not in SKIP_STEMS
    )
    if not csv_files:
        raise FileNotFoundError(
            f"No Olist CSV files found in {data_dir}. Download and unzip the Kaggle dataset first."
        )
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    loaded: list[str] = []
    with sqlite3.connect(db_path) as connection:
        for csv_path in csv_files:
            frame = pd.read_csv(csv_path, low_memory=False)
            table = _table_name(csv_path)
            if table == "order_reviews":
                frame = frame.drop(columns=[c for c in REVIEW_TEXT_COLUMNS if c in frame.columns])
            for column in frame.columns:
                lowered = column.lower()
                if "timestamp" in lowered or lowered.endswith("_date"):
                    parsed = pd.to_datetime(frame[column], errors="coerce")
                    frame[column] = parsed.map(
                        lambda value: value.isoformat(sep=" ") if pd.notna(value) else None
                    )
            frame.to_sql(table, connection, if_exists="replace", index=False)
            loaded.append(table)
        for table, indexes in INDEXES.items():
            if table not in loaded:
                continue
            columns = {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}
            for index_name, column in indexes:
                if column in columns:
                    connection.execute(
                        f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table}"("{column}")'
                    )
        connection.commit()
    return loaded


def main() -> None:
    data_dir = Path(os.environ.get("OLIST_DATA_DIR", config.DATA_DIR))
    db_path = Path(os.environ.get("OLIST_DB_PATH", config.DB_PATH))
    tables = build_database(data_dir, db_path)
    print(f"Built {db_path} with {len(tables)} tables: {', '.join(tables)}")


if __name__ == "__main__":
    main()
