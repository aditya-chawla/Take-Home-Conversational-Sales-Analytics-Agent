# Evaluation: baseline_raw_tables

- Model: `qwen3:8b`
- Overall: 17/22 (77.3%)
- Held out: 4/5
- Mean latency: 56.9s
- Total elapsed: 1250.9s
- Mean retries: 0.00

| Category | Passed | Total | Accuracy |
|---|---:|---:|---:|
| aggregation | 6 | 8 | 75.0% |
| ambiguity | 4 | 4 | 100.0% |
| data_trap | 2 | 2 | 100.0% |
| multi_turn | 1 | 4 | 25.0% |
| refusal | 4 | 4 | 100.0% |

## Failures

### revenue_category
- Expected/actual action: answer / answer
- Error: 
- Generated SQL: `SELECT pc.product_category_name_english, SUM(i.price) AS revenue FROM order_items AS i JOIN products AS p ON i.product_id = p.product_id JOIN product_category_name_translation AS pc ON p.product_category_name = pc.product_category_name GROUP BY pc.product_category_name_english LIMIT 200`

### category_review_scores
- Expected/actual action: answer / answer
- Error: 
- Generated SQL: `SELECT pc.product_category_name_english AS category, AVG(r.review_score) AS average_score FROM order_reviews AS r JOIN orders AS o USING (order_id) JOIN order_items AS i USING (order_id) JOIN products AS p USING (product_id) JOIN product_category_name_translation AS pc USING (product_category_name) GROUP BY pc.product_category_name_english LIMIT 200`

### categories_then_state
- Expected/actual action: answer / answer
- Error: 
- Generated SQL: `SELECT c.customer_state AS state, pc.product_category_name_english AS category, SUM(i.price) AS revenue FROM order_items AS i JOIN products AS p ON i.product_id = p.product_id JOIN product_category_name_translation AS pc ON p.product_category_name = pc.product_category_name JOIN orders ON i.order_id = orders.order_id JOIN customers AS c ON orders.customer_id = c.customer_id WHERE STRFTIME('%Y', orders.order_purchase_timestamp) = '2017' GROUP BY state, category ORDER BY revenue DESC LIMIT 5`

### compare_with_2018
- Expected/actual action: answer / answer
- Error: Generated SQL is missing expected terms: ['2017']
- Generated SQL: `SELECT pc.product_category_name_english AS category, SUM(i.price) AS revenue FROM order_items AS i JOIN products AS p ON i.product_id = p.product_id JOIN product_category_name_translation AS pc ON p.product_category_name = pc.product_category_name JOIN orders AS o ON i.order_id = o.order_id WHERE STRFTIME('%Y', o.order_purchase_timestamp) = '2018' GROUP BY pc.product_category_name_english LIMIT 200`

### full_followup_chain
- Expected/actual action: answer / answer
- Error: Generated SQL is missing expected terms: ['customer_state']
- Generated SQL: `SELECT pc.product_category_name_english AS category, SUM(i.price) AS revenue FROM order_items AS i JOIN products AS p ON i.product_id = p.product_id JOIN product_category_name_translation AS pc ON p.product_category_name = pc.product_category_name JOIN orders ON i.order_id = orders.order_id JOIN customers AS c ON orders.customer_id = c.customer_id WHERE STRFTIME('%Y', orders.order_purchase_timestamp) = '2018' AND orders.order_status = 'delivered' GROUP BY category ORDER BY revenue DESC LIMIT 5`

