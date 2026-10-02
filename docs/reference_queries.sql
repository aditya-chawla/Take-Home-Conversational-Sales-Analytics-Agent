-- Reference 1: item revenue by purchase year (freight excluded)
SELECT substr(o.order_purchase_timestamp, 1, 4) AS purchase_year,
       ROUND(SUM(i.price), 2) AS revenue_brl
FROM orders o
JOIN order_items i ON i.order_id = o.order_id
GROUP BY purchase_year
ORDER BY purchase_year;

-- Reference 2: orders by current status
SELECT order_status, COUNT(DISTINCT order_id) AS orders
FROM orders
GROUP BY order_status
ORDER BY orders DESC;

-- Reference 3: average order item value (deduplicated at order level)
WITH order_totals AS (
  SELECT order_id, SUM(price) AS item_value
  FROM order_items
  GROUP BY order_id
)
SELECT ROUND(AVG(item_value), 2) AS average_item_value_brl
FROM order_totals;

-- Reference 4: delivered order count by customer state
SELECT c.customer_state, COUNT(DISTINCT o.order_id) AS delivered_orders
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY delivered_orders DESC;

-- Reference 5: average review score by translated product category
WITH review_category AS (
  SELECT r.order_id,
         COALESCE(t.product_category_name_english, p.product_category_name) AS category,
         AVG(r.review_score) AS order_category_score
  FROM order_reviews r
  JOIN order_items i ON i.order_id = r.order_id
  JOIN products p ON p.product_id = i.product_id
  LEFT JOIN product_category_name_translation t
    ON t.product_category_name = p.product_category_name
  GROUP BY r.order_id, category
)
SELECT category, ROUND(AVG(order_category_score), 2) AS average_review_score
FROM review_category
GROUP BY category
ORDER BY average_review_score DESC;

-- Reference 6: payment mix without multiplying payments by order items
SELECT payment_type, ROUND(SUM(payment_value), 2) AS payment_value_brl
FROM order_payments
GROUP BY payment_type
ORDER BY payment_value_brl DESC;
