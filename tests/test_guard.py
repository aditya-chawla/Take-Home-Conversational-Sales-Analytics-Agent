import sqlite3

import pytest

from olist_agent.guard import SQLValidationError, validate_sql


ALLOWED = {"orders", "order_items"}


def test_injects_row_limit():
    result = validate_sql("SELECT order_id FROM orders", ALLOWED, max_rows=50)
    assert "LIMIT 50" in result.sql.upper()
    assert result.limit_injected


def test_caps_requested_limit():
    result = validate_sql("SELECT order_id FROM orders LIMIT 900", ALLOWED, max_rows=200)
    assert "LIMIT 200" in result.sql.upper()


@pytest.mark.parametrize("query", [
    "DELETE FROM orders",
    "PRAGMA table_info(orders)",
    "ATTACH DATABASE 'x' AS x",
    "SELECT 1; SELECT 2",
    "SELECT * FROM secret_table",
])
def test_rejects_non_readonly_or_unapproved_sql(query):
    with pytest.raises(SQLValidationError):
        validate_sql(query, ALLOWED)


def test_allows_cte_with_allowlisted_table():
    result = validate_sql(
        "WITH totals AS (SELECT order_id FROM order_items) SELECT order_id FROM totals",
        ALLOWED,
    )
    assert result.tables == {"order_items"}


def test_database_is_read_only(tmp_path):
    path = tmp_path / "sample.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE orders (order_id TEXT)")
        connection.execute("INSERT INTO orders VALUES ('1')")
    from olist_agent.db import execute_query

    result = execute_query(path, "SELECT order_id FROM orders")
    assert result["rows"] == [["1"]]
    with pytest.raises(Exception):
        execute_query(path, "DELETE FROM orders")
