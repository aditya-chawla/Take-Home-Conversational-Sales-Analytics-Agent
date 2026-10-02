# Olist data profile

Database: `data\olist.db`

## Tables

### customers (99,441 rows)

| Column | Type | Nulls | Null rate |
|---|---|---:|---:|
| `customer_id` | TEXT | 0 | 0.0% |
| `customer_unique_id` | TEXT | 0 | 0.0% |
| `customer_zip_code_prefix` | INTEGER | 0 | 0.0% |
| `customer_city` | TEXT | 0 | 0.0% |
| `customer_state` | TEXT | 0 | 0.0% |

### order_items (112,650 rows)

| Column | Type | Nulls | Null rate |
|---|---|---:|---:|
| `order_id` | TEXT | 0 | 0.0% |
| `order_item_id` | INTEGER | 0 | 0.0% |
| `product_id` | TEXT | 0 | 0.0% |
| `seller_id` | TEXT | 0 | 0.0% |
| `shipping_limit_date` | TEXT | 0 | 0.0% |
| `price` | REAL | 0 | 0.0% |
| `freight_value` | REAL | 0 | 0.0% |

### order_payments (103,886 rows)

| Column | Type | Nulls | Null rate |
|---|---|---:|---:|
| `order_id` | TEXT | 0 | 0.0% |
| `payment_sequential` | INTEGER | 0 | 0.0% |
| `payment_type` | TEXT | 0 | 0.0% |
| `payment_installments` | INTEGER | 0 | 0.0% |
| `payment_value` | REAL | 0 | 0.0% |

### order_reviews (99,224 rows)

| Column | Type | Nulls | Null rate |
|---|---|---:|---:|
| `review_id` | TEXT | 0 | 0.0% |
| `order_id` | TEXT | 0 | 0.0% |
| `review_score` | INTEGER | 0 | 0.0% |
| `review_creation_date` | TEXT | 0 | 0.0% |
| `review_answer_timestamp` | TEXT | 0 | 0.0% |

### orders (99,441 rows)

| Column | Type | Nulls | Null rate |
|---|---|---:|---:|
| `order_id` | TEXT | 0 | 0.0% |
| `customer_id` | TEXT | 0 | 0.0% |
| `order_status` | TEXT | 0 | 0.0% |
| `order_purchase_timestamp` | TEXT | 0 | 0.0% |
| `order_approved_at` | TEXT | 160 | 0.2% |
| `order_delivered_carrier_date` | TEXT | 1,783 | 1.8% |
| `order_delivered_customer_date` | TEXT | 2,965 | 3.0% |
| `order_estimated_delivery_date` | TEXT | 0 | 0.0% |

### product_category_name_translation (71 rows)

| Column | Type | Nulls | Null rate |
|---|---|---:|---:|
| `product_category_name` | TEXT | 0 | 0.0% |
| `product_category_name_english` | TEXT | 0 | 0.0% |

### products (32,951 rows)

| Column | Type | Nulls | Null rate |
|---|---|---:|---:|
| `product_id` | TEXT | 0 | 0.0% |
| `product_category_name` | TEXT | 610 | 1.9% |
| `product_name_lenght` | REAL | 610 | 1.9% |
| `product_description_lenght` | REAL | 610 | 1.9% |
| `product_photos_qty` | REAL | 610 | 1.9% |
| `product_weight_g` | REAL | 2 | 0.0% |
| `product_length_cm` | REAL | 2 | 0.0% |
| `product_height_cm` | REAL | 2 | 0.0% |
| `product_width_cm` | REAL | 2 | 0.0% |

### sellers (3,095 rows)

| Column | Type | Nulls | Null rate |
|---|---|---:|---:|
| `seller_id` | TEXT | 0 | 0.0% |
| `seller_zip_code_prefix` | INTEGER | 0 | 0.0% |
| `seller_city` | TEXT | 0 | 0.0% |
| `seller_state` | TEXT | 0 | 0.0% |

## Keys, joins, and data checks

- **orders primary key (order_id):** 0 duplicate key groups; 0 rows with a null key component
- **customers primary key (customer_id):** 0 duplicate key groups; 0 rows with a null key component
- **products primary key (product_id):** 0 duplicate key groups; 0 rows with a null key component
- **sellers primary key (seller_id):** 0 duplicate key groups; 0 rows with a null key component
- **order_reviews primary key (review_id):** 789 duplicate key groups; 0 rows with a null key component
- **order_items primary key (order_id, order_item_id):** 0 duplicate key groups; 0 rows with a null key component
- **order_payments primary key (order_id, payment_sequential):** 0 duplicate key groups; 0 rows with a null key component
- **product_category_name_translation primary key (product_category_name):** 0 duplicate key groups; 0 rows with a null key component
- **Orphan orders.customer_id references to customers.customer_id:** 0
- **Orphan order_items.order_id references to orders.order_id:** 0
- **Orphan order_items.product_id references to products.product_id:** 0
- **Orphan order_items.seller_id references to sellers.seller_id:** 0
- **Orphan order_payments.order_id references to orders.order_id:** 0
- **Orphan order_reviews.order_id references to orders.order_id:** 0
- **Orders without items:** 775
- **Items total (price):** 13,591,643.7
- **Payments total:** 16,008,872.12
- **Missing category translations:** 13
- **Unique customer IDs:** 99,441
- **Unique customer identities:** 96,096
- **orders-items:** 99,441 parent rows, 112,650 child rows, 112,650 matched join rows
- **orders-payments:** 99,441 parent rows, 103,886 child rows, 103,886 matched join rows
- **orders-reviews:** 99,441 parent rows, 99,224 child rows, 99,224 matched join rows
- **Items-vs-payments total mismatch:** price=13,591,643.70, payments=16,008,872.12, difference=2,417,228.42

## Order status distribution

- `delivered`: 96,478
- `shipped`: 1,107
- `canceled`: 625
- `unavailable`: 609
- `invoiced`: 314
- `processing`: 301
- `created`: 5
- `approved`: 2

## Purchase date coverage

- 2016-09: 4 orders
- 2016-10: 324 orders
- 2016-12: 1 orders
- 2017-01: 800 orders
- 2017-02: 1,780 orders
- 2017-03: 2,682 orders
- 2017-04: 2,404 orders
- 2017-05: 3,700 orders
- 2017-06: 3,245 orders
- 2017-07: 4,026 orders
- 2017-08: 4,331 orders
- 2017-09: 4,285 orders
- 2017-10: 4,631 orders
- 2017-11: 7,544 orders
- 2017-12: 5,673 orders
- 2018-01: 7,269 orders
- 2018-02: 6,728 orders
- 2018-03: 7,211 orders
- 2018-04: 6,939 orders
- 2018-05: 6,873 orders
- 2018-06: 6,167 orders
- 2018-07: 6,292 orders
- 2018-08: 6,512 orders
- 2018-09: 16 orders
- 2018-10: 4 orders
- **Date range:** 2016-09-04 21:15:19 through 2018-10-17 17:30:18

## Category translation coverage

- Missing translations: 13
