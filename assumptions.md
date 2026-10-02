# Dataset assumptions

Dataset profile generated from the downloaded Olist archive; see `docs/data_profile.md` for full counts and checks.

- Revenue is the sum of item `price`; freight is excluded.
- Order counts use distinct `order_id`; customer counts use distinct `customer_unique_id`.
- Status is not filtered unless requested; delivered means `order_status = 'delivered'`.
- Dates are purchase timestamps unless the question names a different event timestamp.
- The loaded data spans 2016-09-04 through 2018-10-17. 2016 is sparse and September/October 2018 are partial.
- Item and payment totals are not directly additive across a multi-table join: both are one-to-many from orders and can fan out.
- Geolocation CSV and Portuguese review comment text are excluded from analytics prompts.
- This archive contains 99,441 orders; 775 have no item rows. Avoid silently assuming every order has item revenue.
- There are 96,096 distinct `customer_unique_id` values across 99,441 customer rows; count people with the unique ID, not `customer_id`.
- The `order_reviews.review_id` column has duplicate values in this archive; do not treat it as a unique row key without deduplicating or validating the intended review grain.
- Thirteen product category values do not have an English translation; retain the original category as a fallback.
- Item price total (BRL 13,591,643.70) differs from payment total (BRL 16,008,872.12). These are distinct measures and should not be treated as equal or joined at raw child-row grain.
