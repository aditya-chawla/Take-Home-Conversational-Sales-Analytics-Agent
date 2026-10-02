import sqlite3

from olist_agent.profile_data import profile_database


def test_profile_reports_keys_orphans_and_sales_checks(tmp_path):
    db_path = tmp_path / "sample.db"
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
            CREATE TABLE orders (
                order_id TEXT, customer_id TEXT, order_status TEXT,
                order_purchase_timestamp TEXT
            );
            CREATE TABLE customers (customer_id TEXT, customer_unique_id TEXT);
            CREATE TABLE order_items (order_id TEXT, price REAL);
            CREATE TABLE order_payments (order_id TEXT, payment_value REAL);
            INSERT INTO orders VALUES ('o1', 'c1', 'delivered', '2017-01-01 00:00:00');
            INSERT INTO orders VALUES ('o2', 'missing', 'canceled', '2018-01-01 00:00:00');
            INSERT INTO customers VALUES ('c1', 'u1');
            INSERT INTO order_items VALUES ('o1', 10.0);
            INSERT INTO order_payments VALUES ('o1', 11.0);
        """)
    report = profile_database(db_path)
    assert "orders primary key (order_id)" in report
    assert "Orphan orders.customer_id references to customers.customer_id:** 1" in report
    assert "Orders without items:** 1" in report
    assert "Items-vs-payments total mismatch" in report
    assert "2017-01" in report and "2018-01" in report
