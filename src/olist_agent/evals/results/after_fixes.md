# Evaluation: after_fixes

- Model: `qwen3:8b`
- Overall: 19/23 (82.6%)
- Held out: 5/5
- Mean latency: 33.0s
- Total elapsed: 759.4s
- Mean retries: 0.00

| Category | Passed | Total | Accuracy |
|---|---:|---:|---:|
| aggregation | 7 | 8 | 87.5% |
| ambiguity | 4 | 4 | 100.0% |
| data_trap | 2 | 2 | 100.0% |
| multi_turn | 2 | 4 | 50.0% |
| refusal | 4 | 5 | 80.0% |

## Failures

### category_review_scores
- Expected/actual action: answer / answer
- Generated SQL: `SELECT COALESCE(pc.product_category_name_english, pc.product_category_name) AS product_category, AVG(r.review_score) AS average_score FROM order_reviews AS r JOIN orders AS o USING (order_id) JOIN order_items AS i USING (order_id) JOIN products AS p USING (product_id) JOIN product_category_name_translation AS pc USING (product_category_name) GROUP BY product_category LIMIT 200`

### categories_then_state
- Expected/actual action: answer / answer
- Generated SQL: `SELECT COALESCE(pct.product_category_name_english, pc.product_category_name) AS category, c.customer_state, SUM(oi.price) AS revenue FROM order_items AS oi JOIN orders AS o ON oi.order_id = o.order_id JOIN products AS pc ON oi.product_id = pc.product_id LEFT JOIN product_category_name_translation AS pct ON pc.product_category_name = pct.product_category_name JOIN customers AS c ON o.customer_id = c.customer_id WHERE STRFTIME('%Y', o.order_purchase_timestamp) = '2017' GROUP BY category, c.customer_state ORDER BY revenue DESC LIMIT 5`

### add_delivered_filter
- Expected/actual action: answer / clarify
- Generated SQL: ``

### refuse_profit
- Expected/actual action: refuse / clarify
- Generated SQL: ``
