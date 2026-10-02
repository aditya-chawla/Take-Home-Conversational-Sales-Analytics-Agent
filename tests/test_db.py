import sqlite3

import pandas as pd

from olist_agent.build_db import build_database
from olist_agent.db import execute_query


def test_builder_skips_geolocation_and_formats_timestamps(tmp_path):
    data = tmp_path / "csv"
    data.mkdir()
    pd.DataFrame({
        "order_id": ["a"],
        "order_purchase_timestamp": ["2017-01-02 03:04:05"],
    }).to_csv(data / "olist_orders_dataset.csv", index=False)
    pd.DataFrame({"zip": [1]}).to_csv(data / "olist_geolocation_dataset.csv", index=False)
    target = tmp_path / "db" / "test.db"
    tables = build_database(data, target)
    assert tables == ["orders"]
    assert execute_query(target, "SELECT * FROM orders")["rows"][0][1] == "2017-01-02 03:04:05"


def test_builder_uses_standard_table_name_for_standard_csv(tmp_path):
    data = tmp_path / "csv"
    data.mkdir()
    pd.DataFrame({"order_id": ["a"]}).to_csv(data / "orders.csv", index=False)
    target = tmp_path / "olist.db"
    build_database(data, target)
    with sqlite3.connect(target) as connection:
        assert connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 1


def test_builder_discards_review_comment_text(tmp_path):
    data = tmp_path / "csv"
    data.mkdir()
    pd.DataFrame({
        "review_id": ["r1"],
        "review_score": [5],
        "review_comment_message": ["texto em português"],
        "review_comment_title": ["ótimo"],
    }).to_csv(data / "olist_order_reviews_dataset.csv", index=False)
    target = tmp_path / "olist.db"
    build_database(data, target)
    with sqlite3.connect(target) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(order_reviews)")}
    assert "review_score" in columns
    assert "review_comment_message" not in columns
    assert "review_comment_title" not in columns


def test_readonly_uri_handles_spaces_in_database_path(tmp_path):
    path = tmp_path / "db with spaces.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE orders (order_id TEXT)")
        connection.execute("INSERT INTO orders VALUES ('x')")
    assert execute_query(path, "SELECT order_id FROM orders")["rows"] == [["x"]]
